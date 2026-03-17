import argparse
import logging
from automapLib.automaper import Automaper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")

def main():
    parser = argparse.ArgumentParser(description="Zabbix AutoMapper v19")
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--map", required=True)
    parser.add_argument("--group", required=True)
    parser.add_argument("--map_layout", default="snowflake",
        choices=["tree", "circle", "circular", "random", "star", "horizontal", "vertical", "radial", "snowflake"])
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()

    Automaper(
        url=args.url,
        token=args.token,
        map_name=args.map,
        group_name=args.group,
        layout=args.map_layout,
        config_path=args.config,
    ).run()

if __name__ == "__main__":
    main()
