import math

class MapBuilder:
    VALID_DRAWTYPES = {0, 2, 3, 4}

    def __init__(self, width, height, config_loader, layout="snowflake", margin=80):
        self.w = int(width)
        self.h = int(height)
        self.config = config_loader
        self.layout = str(layout).strip().lower()
        self.margin = int(margin)

    def _build_label(self, node):
        cfg = self.config.get_host_type_config(node["host_type"]) or self.config.get_host_type_config(self.config.get_default_host_type())
        template = str(cfg.get("label") or "{HOSTNAME}")
        name = str(node["host"].get("name") or node["host"].get("host") or node["name"])
        ip = str(node.get("ip") or "")
        return template.replace("{HOSTNAME}", name).replace("{HOST.IP}", ip)

    def _circle_positions(self, nodes):
        cx, cy = self.w // 2, self.h // 2
        radius = max(120, min(cx, cy) - self.margin)
        positions = {}
        for i, node in enumerate(nodes):
            angle = (2 * math.pi * i) / max(1, len(nodes))
            positions[node["id"]] = {
                "x": cx + int(radius * math.cos(angle)),
                "y": cy + int(radius * math.sin(angle)),
            }
        return positions

    def _cluster_grid(self, cx, cy, members, spacing):
        positions = {}
        if not members:
            return positions
        members = sorted(members, key=lambda n: (n["host_type"], n["name"].lower()))
        cols = max(2, int(math.ceil(math.sqrt(len(members)))))
        rows = int(math.ceil(len(members) / cols))
        width = (cols - 1) * spacing
        height = (rows - 1) * spacing
        start_x = cx - width // 2
        start_y = cy - height // 2
        for idx, node in enumerate(members):
            row = idx // cols
            col = idx % cols
            positions[node["id"]] = {
                "x": start_x + col * spacing,
                "y": start_y + row * spacing,
            }
        return positions

    def _cluster_circle(self, cx, cy, members, radius):
        positions = {}
        if not members:
            return positions
        members = sorted(members, key=lambda n: (n["host_type"], n["name"].lower()))
        for i, node in enumerate(members):
            angle = (2 * math.pi * i) / max(1, len(members))
            positions[node["id"]] = {
                "x": cx + int(radius * math.cos(angle)),
                "y": cy + int(radius * math.sin(angle)),
            }
        return positions

    def _cluster_half_circle(self, switch_x, switch_y, center_x, center_y, members, radius):
        positions = {}
        if not members:
            return positions
        members = sorted(members, key=lambda n: (n["host_type"], n["name"].lower()))
        base_angle = math.atan2(switch_y - center_y, switch_x - center_x)
        start = base_angle - math.pi / 2
        end = base_angle + math.pi / 2
        if len(members) == 1:
            angles = [base_angle]
        else:
            step = (end - start) / (len(members) - 1)
            angles = [start + step * i for i in range(len(members))]
        for node, angle in zip(members, angles):
            positions[node["id"]] = {
                "x": switch_x + int(radius * math.cos(angle)),
                "y": switch_y + int(radius * math.sin(angle)),
            }
        return positions

    def _snowflake_positions(self, nodes, edges):
        positions = {}
        cx, cy = self.w // 2, self.h // 2

        routers = sorted([n for n in nodes if n["is_router"]], key=lambda n: n["name"].lower())
        switches = sorted([n for n in nodes if n["is_switch"] and not n["is_router"]], key=lambda n: n["name"].lower())
        endpoints = sorted([n for n in nodes if n["is_endpoint"]], key=lambda n: n["name"].lower())

        # Router ins Zentrum
        if routers:
            if len(routers) == 1:
                positions[routers[0]["id"]] = {"x": cx, "y": cy}
            else:
                rr = max(40, min(self.w, self.h) // 12)
                for i, r in enumerate(routers):
                    angle = (2 * math.pi * i) / len(routers)
                    positions[r["id"]] = {"x": cx + int(rr * math.cos(angle)), "y": cy + int(rr * math.sin(angle))}

        # Ziel-Switch je Endpoint aus Edges ableiten
        endpoint_target = {}
        edge_meta = {}
        for edge in edges:
            endpoint_target[edge["src"]] = edge["dst"]
            edge_meta[edge["src"]] = edge

        groups = {sw["id"]: [] for sw in switches}
        for ep in endpoints:
            target = endpoint_target.get(ep["id"])
            if target in groups:
                groups[target].append(ep)

        max_group = max([len(v) for v in groups.values()] + [0])
        switch_radius = min(
            max(220, min(self.w, self.h) // 4) + len(switches) * 24 + max_group * 14,
            max(320, min(self.w, self.h) // 2 - 180)
        )

        switch_positions = {}
        for i, sw in enumerate(switches):
            angle = (2 * math.pi * i) / max(1, len(switches))
            x = cx + int(switch_radius * math.cos(angle))
            y = cy + int(switch_radius * math.sin(angle))
            positions[sw["id"]] = {"x": x, "y": y}
            switch_positions[sw["id"]] = {"x": x, "y": y}

        # Endgeräte je Switch als grid/circle/half_circle
        for sw in switches:
            members = groups.get(sw["id"], [])
            if not members:
                continue

            meta = None
            for m in members:
                meta = edge_meta.get(m["id"])
                if meta:
                    break

            layout = None
            if meta:
                layout = meta.get("endpoint_layout")
            if not layout:
                for m in members:
                    if m.get("endpoint_layout"):
                        layout = m["endpoint_layout"]
                        break
            if not layout:
                layout = self.config.get_endpoint_layout()

            distance = None
            if meta:
                distance = meta.get("distance")
            if distance is None:
                for m in members:
                    if m.get("link_distance") is not None:
                        distance = m["link_distance"]
                        break
            if distance is None:
                distance = self.config.get_default_link_distance()

            sx = switch_positions[sw["id"]]["x"]
            sy = switch_positions[sw["id"]]["y"]

            if layout == "grid":
                spacing = max(80, min(distance, 220))
                positions.update(self._cluster_grid(sx, sy + spacing, members, spacing))
            elif layout == "half_circle":
                radius = max(80, min(distance, 260))
                positions.update(self._cluster_half_circle(sx, sy, cx, cy, members, radius))
            else:
                radius = max(80, min(distance, 260))
                positions.update(self._cluster_circle(sx, sy, members, radius))

        remaining = [n for n in nodes if n["id"] not in positions]
        if remaining:
            outer_radius = max(switch_radius + 180, min(self.w, self.h) // 2 - self.margin)
            for i, node in enumerate(remaining):
                angle = (2 * math.pi * i) / max(1, len(remaining))
                positions[node["id"]] = {
                    "x": cx + int(outer_radius * math.cos(angle)),
                    "y": cy + int(outer_radius * math.sin(angle)),
                }

        return positions

    def build_positions(self, nodes, edges):
        if self.layout == "snowflake":
            return self._snowflake_positions(nodes, edges)
        return self._circle_positions(nodes)

    def build_selements(self, nodes, edges, existing):
        positions = self.build_positions(nodes, edges)
        by_hostid = existing.get("by_hostid", {})
        out = []
        for node in nodes:
            cfg = self.config.get_host_type_config(node["host_type"]) or self.config.get_host_type_config(self.config.get_default_host_type())
            pos = positions[node["id"]]
            selement = {
                "elements": [{"hostid": node["id"]}],
                "elementtype": int(cfg.get("elementtype", 0)),
                "iconid_off": int(cfg.get("iconid_off", 0)),
                "iconid_on": int(cfg.get("iconid_on", 0)),
                "iconid_disabled": int(cfg.get("iconid_disabled", 0)),
                "iconid_maintenance": int(cfg.get("iconid_maintenance", 0)),
                "x": int(pos["x"]),
                "y": int(pos["y"]),
                "label": self._build_label(node),
            }
            if node.get("url"):
                selement["url"] = node["url"]
            existing_selement = by_hostid.get(node["id"])
            if existing_selement and existing_selement.get("selementid") is not None:
                selement["selementid"] = int(existing_selement["selementid"])
            out.append(selement)
        return out

    def build_links(self, edges, existing):
        hostid_to_selementid = existing.get("hostid_to_selementid", {})
        links = []
        for edge in edges:
            sid1 = hostid_to_selementid.get(edge["src"])
            sid2 = hostid_to_selementid.get(edge["dst"])
            if sid1 is None or sid2 is None:
                continue
            drawtype = int(edge.get("drawtype", 0))
            if drawtype not in self.VALID_DRAWTYPES:
                drawtype = 0
            link = {
                "selementid1": int(sid1),
                "selementid2": int(sid2),
                "drawtype": drawtype,
                "color": str(edge.get("color", "00FF00")).strip(),
            }
            if edge.get("label"):
                link["label"] = str(edge["label"])
            links.append(link)
        return links
