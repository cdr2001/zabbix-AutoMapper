from zabbix_utils import ZabbixAPI

class ZabbixClient:
    def __init__(self, url, token):
        self.api = ZabbixAPI(url=url, token=token)

    def hosts(self, group_name):
        groups = self.api.hostgroup.get(output=["groupid"], filter={"name": [group_name]})
        if not groups:
            raise RuntimeError(f"Hostgruppe nicht gefunden: {group_name}")
        gid = groups[0]["groupid"]
        return self.api.host.get(groupids=[gid], output=["hostid", "host", "name", "description"], selectTags="extend", selectInterfaces=["ip"])

    def map(self, map_name):
        maps = self.api.map.get(output="extend", selectSelements="extend", selectLinks="extend", selectShapes="extend", filter={"name": [map_name]})
        if not maps:
            raise RuntimeError(f"Map nicht gefunden: {map_name}")
        return maps[0]

    def parse_existing(self, map_obj):
        result = {"by_hostid": {}, "hostid_to_selementid": {}, "shapes": map_obj.get("shapes", []) or []}
        for s in map_obj.get("selements", []):
            sid = s.get("selementid")
            for e in s.get("elements", []) or []:
                hid = e.get("hostid")
                if hid:
                    hid = str(hid)
                    result["by_hostid"][hid] = s
                    if sid is not None:
                        result["hostid_to_selementid"][hid] = int(sid)
        return result

    def update(self, mapid, selements, links, shapes=None):
        payload = {"sysmapid": int(mapid), "selements": selements, "links": links}
        if shapes is not None:
            payload["shapes"] = shapes
        return self.api.map.update(**payload)
