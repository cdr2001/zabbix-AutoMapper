import re

class GraphBuilder:
    VALID_DRAWTYPES = {0, 2, 3, 4}
    ENDPOINT_TYPES = {"server", "pc", "notebook", "telefon", "satellit", "ups"}
    VALID_ENDPOINT_LAYOUTS = {"grid", "circle", "half_circle"}

    def __init__(self, config_loader):
        self.config_loader = config_loader
        self.nodes = {}
        self.edges = []

    @staticmethod
    def _tag(tags, name):
        if not isinstance(tags, list):
            return None
        for t in tags:
            if isinstance(t, dict) and str(t.get("tag", "")).strip() == name:
                return str(t.get("value", "")).strip()
        return None

    @staticmethod
    def _extract_ipv4(host):
        for i in host.get("interfaces", []) or []:
            if not isinstance(i, dict):
                continue
            ip = str(i.get("ip", "")).strip()
            if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                return ip
        return ""

    @staticmethod
    def _subnet24(ip):
        p = ip.split(".")
        return ".".join(p[:3]) if len(p) == 4 else ""

    @staticmethod
    def _normalize_color(value):
        if value is None:
            return None
        value = str(value).strip().upper().replace("#", "")
        value = re.sub(r"[^0-9A-F]", "", value)
        if len(value) == 3:
            value = "".join(ch * 2 for ch in value)
        return value if len(value) == 6 else None

    @classmethod
    def _normalize_draw_type(cls, value):
        if value is None:
            return None
        s = str(value).strip().lower()
        mapping = {
            "line": 0, "solid": 0,
            "dotted": 2, "dot": 2,
            "dashed": 3, "dash": 3,
            "bold": 4, "thick": 4,
            "bold_dotted": 4, "bold-dotted": 4, "thick_dotted": 4,
        }
        if s.isdigit():
            v = int(s)
            return v if v in cls.VALID_DRAWTYPES else None
        v = mapping.get(s)
        return v if v in cls.VALID_DRAWTYPES else None

    @classmethod
    def _normalize_endpoint_layout(cls, value):
        if value is None:
            return None
        v = str(value).strip().lower()
        return v if v in cls.VALID_ENDPOINT_LAYOUTS else None

    @staticmethod
    def _normalize_distance(value):
        if value is None:
            return None
        try:
            v = int(str(value).strip())
            return max(60, min(v, 500))
        except Exception:
            return None

    def add_hosts(self, hosts):
        self.nodes = {}
        for h in hosts:
            tags = h.get("tags", []) or []
            host_type = self.config_loader.resolve_host_type(self._tag(tags, "am.host.type"))
            color = self._normalize_color(self._tag(tags, "am.link.color"))
            if color is None:
                color = self._normalize_color(self.config_loader.get_default_link_colour()) or "00FF00"
            draw_type = self._normalize_draw_type(self._tag(tags, "am.link.draw_type"))
            if draw_type is None:
                draw_type = self._normalize_draw_type(self.config_loader.get_default_draw_type())
            if draw_type is None:
                draw_type = 0

            endpoint_layout = self._normalize_endpoint_layout(self._tag(tags, "am.layout.endpoints"))
            link_distance = self._normalize_distance(self._tag(tags, "am.link.distance"))

            ip = self._extract_ipv4(h)
            node = {
                "id": str(h.get("hostid")),
                "name": str(h.get("name") or h.get("host") or h.get("hostid")).strip(),
                "technical_name": str(h.get("host") or h.get("name") or h.get("hostid")).strip(),
                "host_type": host_type,
                "is_switch": host_type == "switch",
                "is_router": host_type == "router",
                "is_endpoint": host_type in self.ENDPOINT_TYPES,
                "connect_to": self._tag(tags, "am.link.connect_to"),
                "link_label": self._tag(tags, "am.link.label"),
                "link_color": color,
                "link_draw_type": draw_type,
                "url": self._tag(tags, "am.host.url"),
                "ip": ip,
                "subnet24": self._subnet24(ip),
                "endpoint_layout": endpoint_layout,
                "link_distance": link_distance,
                "host": h,
            }
            self.nodes[node["id"]] = node

    def build_edges(self):
        self.edges = []
        by_name = {n["name"]: nid for nid, n in self.nodes.items()}
        by_tech = {n["technical_name"]: nid for nid, n in self.nodes.items()}

        subnet_switches = {}
        for nid, node in self.nodes.items():
            if node["is_switch"] and node["subnet24"]:
                subnet_switches.setdefault(node["subnet24"], []).append(nid)

        seen = set()

        for nid, node in self.nodes.items():
            target_id = None

            if node.get("connect_to"):
                target_id = by_name.get(node["connect_to"]) or by_tech.get(node["connect_to"])
            elif node["is_endpoint"] and node["subnet24"]:
                candidates = subnet_switches.get(node["subnet24"], [])
                if candidates:
                    target_id = candidates[0]

            if not target_id or target_id == nid:
                continue

            key = tuple(sorted((nid, target_id)))
            if key in seen:
                continue
            seen.add(key)

            edge = {
                "src": nid,
                "dst": target_id,
                "color": node["link_color"],
                "drawtype": int(node["link_draw_type"]),
                "distance": node.get("link_distance"),
                "endpoint_layout": node.get("endpoint_layout"),
            }
            if node.get("link_label"):
                edge["label"] = node["link_label"]
            self.edges.append(edge)

    def get_nodes(self):
        return list(self.nodes.values())

    def get_edges(self):
        return list(self.edges)
