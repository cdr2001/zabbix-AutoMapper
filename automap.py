import argparse
import logging
from automapLib.automaper import Automaper

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler("automap.log", encoding="utf-8"), logging.StreamHandler()],
    )

def main():
    setup_logging()
    p = argparse.ArgumentParser(description="Zabbix AutoMapper v36")
    p.add_argument("--url", required=True)
    p.add_argument("--token", required=True)
    p.add_argument("--map", required=True)
    p.add_argument("--group", required=True)
    p.add_argument("--map_layout", default="hierarchical", choices=["hierarchical", "circle"])
    p.add_argument("--config", default="config.json")
    a = p.parse_args()
    Automaper(url=a.url, token=a.token, map_name=a.map, group_name=a.group, layout=a.map_layout, config_path=a.config).run()

if __name__ == "__main__":
    main()
