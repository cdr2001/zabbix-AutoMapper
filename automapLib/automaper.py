from automapLib.config_loader import ConfigLoader
from automapLib.zabbix_client import ZabbixClient
from automapLib.graph_builder import GraphBuilder
from automapLib.map_builder import MapBuilder

class Automaper:
    def __init__(self, url, token, map_name, group_name, layout, config_path):
        self.config = ConfigLoader(config_path)
        self.z = ZabbixClient(url, token)
        self.map_name = map_name
        self.group_name = group_name
        self.layout = layout

    def run(self):
        hosts = self.z.hosts(self.group_name)
        graph = GraphBuilder(self.config)
        graph.add_hosts(hosts)
        graph.build_edges()
        nodes = graph.get_nodes()
        edges = graph.get_edges()
        current_map = self.z.map(self.map_name)
        builder = MapBuilder(int(current_map["width"]), int(current_map["height"]), self.config, self.layout)

        existing = self.z.parse_existing(current_map)
        selements = builder.build_selements(nodes, edges, existing)
        shapes = builder.build_shapes(nodes, edges)
        self.z.update(current_map["sysmapid"], selements, [], shapes)

        refreshed_map = self.z.map(self.map_name)
        refreshed_existing = self.z.parse_existing(refreshed_map)
        selements = builder.build_selements(nodes, edges, refreshed_existing)
        links = builder.build_links(edges, refreshed_existing)
        shapes = builder.build_shapes(nodes, edges)
        self.z.update(refreshed_map["sysmapid"], selements, links, shapes)
