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

    def get_show_description(self):
        return bool(self.data.get("show_description", True))

    def get_description_max_lines(self):
        try:
            return max(1, int(self.data.get("description_max_lines", 2)))
        except Exception:
            return 2

    def get_description_max_line_length(self):
        try:
            return max(10, int(self.data.get("description_max_line_length", 40)))
        except Exception:
            return 40

    def get_host_type_config(self, host_type):
        return self.data.get("host_type", {}).get(str(host_type).strip().lower(), {})

    def resolve_host_type(self, host_type):
        host_type = str(host_type or "").strip().lower()
        aliases = {"telefon": "phone"}
        host_type = aliases.get(host_type, host_type)
        return host_type if host_type in self.data.get("host_type", {}) else self.get_default_host_type()
