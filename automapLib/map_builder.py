import textwrap
from collections import defaultdict

TYPE_ORDER = {
    "server": 1,
    "pc": 2,
    "notebook": 3,
    "phone": 4,
    "printer": 5,
    "iot": 6,
    "camera": 7,
    "ups": 8,
    "satellit": 9,
    "switch": 10,
    "router": 11,
    "cloud": 12,
}

class MapBuilder:
    VALID_DRAWTYPES = {0, 2, 3, 4}

    def __init__(self, width, height, config_loader, layout="hierarchical", margin=80):
        self.w = int(width)
        self.h = int(height)
        self.config = config_loader
        self.layout = str(layout).strip().lower()
        self.margin = int(margin)

    def _format_description(self, description):
        description = str(description or "").strip()
        if not description or not self.config.get_show_description():
            return ""
        description = " ".join(description.split())
        wrapped = textwrap.wrap(description, width=self.config.get_description_max_line_length())
        wrapped = wrapped[:self.config.get_description_max_lines()]
        if wrapped and len(" ".join(wrapped)) < len(description):
            wrapped[-1] = wrapped[-1].rstrip(" .") + "..."
        return "\n".join(wrapped)

    def _build_label(self, node):
        cfg = self.config.get_host_type_config(node["host_type"]) or self.config.get_host_type_config(self.config.get_default_host_type())
        label = str(cfg.get("label") or "{HOSTNAME}")
        label = label.replace("{HOSTNAME}", str(node["host"].get("name") or node["host"].get("host") or node["name"]))
        label = label.replace("{HOST.IP}", str(node.get("ip") or ""))
        description = self._format_description(node["host"].get("description"))
        return f"{label}\n{description}" if description else label

    def _sort_nodes(self, nodes):
        return sorted(nodes, key=lambda n: (TYPE_ORDER.get(n["host_type"], 99), n["name"].lower()))

    def _build_tree(self, nodes, edges):
        node_map = {n["id"]: n for n in nodes}
        parent_of = {}
        children_of = defaultdict(list)
        for e in edges:
            parent_of[e["src"]] = e["dst"]
            children_of[e["dst"]].append(e["src"])
        return node_map, parent_of, children_of

    def _cluster_width(self, switch_count, device_count):
        sw_w = max(220, switch_count * 220)
        dev_cols = min(4, max(1, device_count))
        dev_w = max(220, dev_cols * 180)
        return max(sw_w, dev_w) + 120

    def _make_shape(self, x, y, width, height, text):
        return {
            "type": 0,
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
            "border_type": 0,
            "border_width": 1,
            "border_color": "C8C8C8",
            "background_color": "F8F8F8",
            "font": 9,
            "font_size": 11,
            "font_color": "444444",
            "text_halign": 0,
            "text_valign": 0,
            "text": str(text),
            "zindex": -10,
        }

    def _hierarchical_positions_and_shapes(self, nodes, edges):
        positions = {}
        shapes = []
        node_map, parent_of, children_of = self._build_tree(nodes, edges)

        clouds = self._sort_nodes([n for n in nodes if n["is_cloud"]])
        routers = self._sort_nodes([n for n in nodes if n["is_router"]])

        cloud_y = self.margin + 40
        router_y = cloud_y + 180
        switch_y = router_y + 230
        device_y = switch_y + 220

        if len(clouds) == 1:
            positions[clouds[0]["id"]] = {"x": self.w // 2, "y": cloud_y}
        elif clouds:
            total = min(800, int(self.w * 0.6))
            start = (self.w - total) // 2
            step = total / max(1, len(clouds) - 1)
            for i, node in enumerate(clouds):
                positions[node["id"]] = {"x": int(start + i * step), "y": cloud_y}

        direct_device_groups = defaultdict(list)
        switch_groups = defaultdict(list)

        for node in nodes:
            parent_id = parent_of.get(node["id"])
            if not parent_id:
                continue
            if node["is_switch"]:
                switch_groups[parent_id].append(node)
            elif not node["is_cloud"] and not node["is_router"]:
                direct_device_groups[parent_id].append(node)

        for k in list(switch_groups.keys()):
            switch_groups[k] = self._sort_nodes(switch_groups[k])
        for k in list(direct_device_groups.keys()):
            direct_device_groups[k] = self._sort_nodes(direct_device_groups[k])

        # width per router/network based on child counts
        router_blocks = []
        for r in routers:
            sw_count = len(switch_groups.get(r["id"], []))
            direct_count = len(direct_device_groups.get(r["id"], []))
            switch_child_count = 0
            for sw in switch_groups.get(r["id"], []):
                switch_child_count += len([cid for cid in children_of.get(sw["id"], []) if cid in node_map and not node_map[cid]["is_switch"]])
            width = self._cluster_width(sw_count, max(direct_count, switch_child_count))
            router_blocks.append((r, width))

        total_cluster_width = sum(width for _, width in router_blocks) + max(0, (len(router_blocks) - 1) * 120)
        total_cluster_width = min(total_cluster_width, self.w - 2 * self.margin)
        start_x = max(self.margin, (self.w - total_cluster_width) // 2)

        cursor_x = start_x
        router_centers = {}
        for router, width in router_blocks:
            center_x = cursor_x + width // 2
            router_centers[router["id"]] = (cursor_x, width, center_x)
            positions[router["id"]] = {"x": int(center_x), "y": router_y}
            cursor_x += width + 120

        # cloud children connection can remain above; shapes start at router zones
        for router, width in router_blocks:
            zone_x, zone_w, center_x = router_centers[router["id"]]
            switches = switch_groups.get(router["id"], [])
            devices = direct_device_groups.get(router["id"], [])

            shapes.append(self._make_shape(zone_x, router_y - 70, zone_w, 560, router["name"]))

            if switches:
                total_sw_width = max(0, (len(switches) - 1) * 220)
                sw_start_x = center_x - total_sw_width // 2
                for i, sw in enumerate(switches):
                    positions[sw["id"]] = {"x": int(sw_start_x + i * 220), "y": switch_y}

            if devices:
                cols = max(1, min(4, len(devices)))
                rows = (len(devices) + cols - 1) // cols
                total_width = max(0, (cols - 1) * 180)
                total_height = max(0, (rows - 1) * 160)
                dev_start_x = center_x - total_width // 2
                dev_start_y = device_y - total_height // 2
                for idx, dev in enumerate(devices):
                    r = idx // cols
                    c = idx % cols
                    positions[dev["id"]] = {"x": int(dev_start_x + c * 180), "y": int(dev_start_y + r * 160)}

        # switch children strictly below each switch
        for sw in [n for n in nodes if n["is_switch"]]:
            children = self._sort_nodes([node_map[cid] for cid in children_of.get(sw["id"], []) if cid in node_map and not node_map[cid]["is_switch"]])
            if not children or sw["id"] not in positions:
                continue
            parent_x = positions[sw["id"]]["x"]
            cols = max(1, min(4, len(children)))
            rows = (len(children) + cols - 1) // cols
            total_width = max(0, (cols - 1) * 180)
            start_x = parent_x - total_width // 2
            start_y = device_y
            for idx, dev in enumerate(children):
                r = idx // cols
                c = idx % cols
                positions[dev["id"]] = {"x": int(start_x + c * 180), "y": int(start_y + r * 160)}

        remaining = [n for n in nodes if n["id"] not in positions]
        if remaining:
            remaining = self._sort_nodes(remaining)
            y = min(self.h - self.margin, device_y + 260)
            total = min(800, int(self.w * 0.6))
            start = (self.w - total) // 2
            if len(remaining) == 1:
                positions[remaining[0]["id"]] = {"x": self.w // 2, "y": y}
            else:
                step = total / max(1, len(remaining) - 1)
                for i, n in enumerate(remaining):
                    positions[n["id"]] = {"x": int(start + i * step), "y": y}
        return positions, shapes

    def _circle_positions(self, nodes):
        import math
        cx, cy = self.w // 2, self.h // 2
        radius = max(120, min(cx, cy) - self.margin)
        pos = {}
        items = self._sort_nodes(nodes)
        for i, node in enumerate(items):
            angle = (2 * math.pi * i) / max(1, len(items))
            pos[node["id"]] = {"x": cx + int(radius * math.cos(angle)), "y": cy + int(radius * math.sin(angle))}
        return pos, []

    def build_positions_and_shapes(self, nodes, edges):
        return self._hierarchical_positions_and_shapes(nodes, edges) if self.layout == "hierarchical" else self._circle_positions(nodes)

    def build_selements(self, nodes, edges, existing):
        positions, _ = self.build_positions_and_shapes(nodes, edges)
        by_hostid = existing.get("by_hostid", {})
        out = []
        for node in nodes:
            cfg = self.config.get_host_type_config(node["host_type"]) or self.config.get_host_type_config(self.config.get_default_host_type())
            pos = positions[node["id"]]
            s = {
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
                s["urls"] = [{"name": "Webadmin", "url": str(node["url"])}]
            existing_s = by_hostid.get(node["id"])
            if existing_s and existing_s.get("selementid") is not None:
                s["selementid"] = int(existing_s["selementid"])
            out.append(s)
        return out

    def build_shapes(self, nodes, edges):
        _, shapes = self.build_positions_and_shapes(nodes, edges)
        return shapes

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
            link = {"selementid1": int(sid1), "selementid2": int(sid2), "drawtype": drawtype, "color": str(edge.get("color", "00FF00")).strip()}
            if edge.get("label"):
                link["label"] = str(edge["label"])
            links.append(link)
        return links
