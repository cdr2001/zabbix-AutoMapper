import logging
import re

logger = logging.getLogger("GraphBuilder")

class GraphBuilder:
    VALID_DRAWTYPES = {0, 2, 3, 4}

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
            if isinstance(i, dict):
                ip = str(i.get("ip", "")).strip()
                if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", ip):
                    return ip
        return ""

    @staticmethod
    def _subnet24(ip):
        parts = ip.split(".")
        return ".".join(parts[:3]) if len(parts) == 4 else ""

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
        mapping = {"line": 0, "solid": 0, "dotted": 2, "dot": 2, "dashed": 3, "dash": 3, "bold": 4, "thick": 4}
        if s.isdigit():
            v = int(s)
            return v if v in cls.VALID_DRAWTYPES else None
        return mapping.get(s)

    def add_hosts(self, hosts):
        self.nodes = {}
        for h in hosts:
            tags = h.get("tags", []) or []
            host_type = self.config_loader.resolve_host_type(self._tag(tags, "am.host.type"))
            color = self._normalize_color(self._tag(tags, "am.link.color")) or self._normalize_color(self.config_loader.get_default_link_colour()) or "00FF00"
            draw_type = self._normalize_draw_type(self._tag(tags, "am.link.draw_type"))
            if draw_type is None:
                draw_type = self._normalize_draw_type(self.config_loader.get_default_draw_type())
            if draw_type is None:
                draw_type = 0
            ip = self._extract_ipv4(h)
            node = {
                "id": str(h.get("hostid")),
                "name": str(h.get("name") or h.get("host") or h.get("hostid")).strip(),
                "technical_name": str(h.get("host") or h.get("name") or h.get("hostid")).strip(),
                "host_type": host_type,
                "is_cloud": host_type == "cloud",
                "is_router": host_type == "router",
                "is_switch": host_type == "switch",
                "connect_to": self._tag(tags, "am.link.connect_to"),
                "link_label": self._tag(tags, "am.link.label"),
                "link_color": color,
                "link_draw_type": draw_type,
                "url": self._tag(tags, "am.host.url"),
                "ip": ip,
                "subnet24": self._subnet24(ip),
                "host": h,
            }
            self.nodes[node["id"]] = node
            logger.debug("Host geladen: id=%s name=%s host=%s ip=%s type=%s connect_to=%s", node["id"], node["name"], node["technical_name"], node["ip"], node["host_type"], node["connect_to"])

    def _resolve_target(self, raw_target):
        target = str(raw_target or "").strip()
        if not target:
            return None, None
        checks = [
            ("name_exact", lambda n: target == n["name"]),
            ("host_exact", lambda n: target == n["technical_name"]),
            ("ip_exact", lambda n: target == n["ip"]),
            ("name_ci", lambda n: target.lower() == n["name"].lower()),
            ("host_ci", lambda n: target.lower() == n["technical_name"].lower()),
            ("ip_ci", lambda n: target.lower() == n["ip"].lower()),
            ("name_contains", lambda n: target.lower() in n["name"].lower()),
            ("host_contains", lambda n: target.lower() in n["technical_name"].lower()),
            ("ip_contains", lambda n: target.lower() in n["ip"].lower()),
        ]
        for label, fn in checks:
            for nid, node in self.nodes.items():
                try:
                    if fn(node):
                        return nid, label
                except Exception:
                    pass
        return None, None

    def build_edges(self):
        self.edges = []
        subnet_routers = {}
        for nid, n in self.nodes.items():
            if n["is_router"] and n["subnet24"]:
                subnet_routers.setdefault(n["subnet24"], []).append(nid)

        seen = set()

        for nid, n in self.nodes.items():
            target_id = None
            if n.get("connect_to"):
                logger.debug("connect_to gefunden: source=%s target_raw=%s", n["name"], n["connect_to"])
                target_id, resolved_by = self._resolve_target(n["connect_to"])
                if target_id:
                    logger.info("CONNECT_TO OK: %s -> %s (%s)", n["name"], self.nodes[target_id]["name"], resolved_by)
                else:
                    logger.warning("CONNECT_TO NOT FOUND: source=%s target_raw=%s", n["name"], n["connect_to"])
            else:
                resolved_by = None

            if not target_id or target_id == nid:
                continue
            key = (nid, target_id)
            if key in seen:
                continue
            seen.add(key)
            self.edges.append({"src": nid, "dst": target_id, "color": n["link_color"], "drawtype": int(n["link_draw_type"]), "label": n.get("link_label"), "resolved_by": resolved_by})
            logger.info("EDGE OK: %s -> %s", n["name"], self.nodes[target_id]["name"])

        for nid, n in self.nodes.items():
            if n.get("connect_to") or n["is_cloud"]:
                continue
            target_id = None
            if n["subnet24"]:
                candidates = subnet_routers.get(n["subnet24"], [])
                if candidates:
                    target_id = candidates[0]
            if not target_id or target_id == nid:
                continue
            key = (nid, target_id)
            if key in seen:
                continue
            seen.add(key)
            self.edges.append({"src": nid, "dst": target_id, "color": n["link_color"], "drawtype": int(n["link_draw_type"]), "label": n.get("link_label"), "resolved_by": "subnet24"})
            logger.info("EDGE OK: %s -> %s (subnet24)", n["name"], self.nodes[target_id]["name"])

    def get_nodes(self):
        return list(self.nodes.values())

    def get_edges(self):
        return list(self.edges)
