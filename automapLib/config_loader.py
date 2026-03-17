import json

class ConfigLoader:
    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def get_default_host_type(self):
        return str(self.data.get("default_host_type", "server")).strip().lower()

    def get_default_link_colour(self):
        return str(self.data.get("default_link_colour", "00FF00")).strip()

    def get_default_draw_type(self):
        try:
            return int(self.data.get("default_draw_type", 0))
        except Exception:
            return 0

    def get_endpoint_layout(self):
        return str(self.data.get("endpoint_layout", "grid")).strip().lower()

    def get_default_link_distance(self):
        try:
            return int(self.data.get("default_link_distance", 160))
        except Exception:
            return 160

    def get_host_type_config(self, host_type):
        return self.data.get("host_type", {}).get(str(host_type).strip().lower(), {})

    def resolve_host_type(self, host_type):
        host_type = str(host_type or "").strip().lower()
        if host_type and host_type in self.data.get("host_type", {}):
            return host_type
        return self.get_default_host_type()
