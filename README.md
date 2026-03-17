zabbix-AutoMapper

Generate automatic map placement for Zabbix hosts using zabbix API. (Tested with zabbix	7.4.8)

Prerequisites
install the required python packages

pip install -r requirements.txt

How to run the script
python automap.py

python automap.py --help to get help

python3 automap.py --token [zabbix token] --map [zabbix map] --group [zabbix host group] --url [zabbix url] --map_layout [start|grid|snowflake]

tags used by the script
am.host.type => type of the host, should be defined in config.json
am.link.connect_to => the host to connect to --> standard same class C network
am.link.label => the label to show on the link
am.link.color => the color of the link --> standard 00ff00 (green) --> defined in config.json
am.link.draw_type => the type of the link (0: line, 2: bold line, 3: dotted line, 4: dashed line) --> standard 0 --> defined in config.json

- clients-layouts per switch-cluster:
  - `grid`
  - `circle`
  - `half_circle`
- can be overwritte per switch or Host via zabbix:
  - `am.layout.endpoints=grid|circle|half_circle`
