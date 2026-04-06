<h2>zabbix-AutoMapper 0.5</h2>

Generate automatic map placement for Zabbix hosts using zabbix API. (Tested with zabbix	7.4.8)<br>
<br>
<h4>a. Prerequisites </h4>
install the required python packages<br>
<br>
pip install -r requirements.txt<br>
<br>
<h4>b. How to run the script</h4>
python automap.py<br>
<br>
python automap.py --help => to get help<br>
<br>
python3 automap.py --token [zabbix token] --map [zabbix map] --group [zabbix host group] --url [zabbix url] --map_layout [hierarchical|grid|snowflake]<br>

<h4>c. hierarchy</h4>
  0. cloud<br>
  1. router<br>
  n. all other devices<br> --> all network devices in same class C network will be automatically connect to its router

                     cloud
                  /         \
          router 1           router 2
        /         \           /      \
     pc         notebook   server    nas

<h4>d. tags used by the script</h4>
- am.host.type => type of the host, should be defined in config.json<br>
- am.link.connect_to => add or overwrite the hierarchically connection to router (see c. hierarchy)<br>
- am.link.label => the label to show on the link<br>
- am.link.color => the color of the link --> standard can defined in config.json<br>
- am.link.draw_type => the type of the link (0: line, 2: bold line, 3: dotted line, 4: dashed line) --> standard defined in config.json<br>
- am.host.url => URL to device Webadmin <br>
- am.layout.endpoints = [grid|circle|half_circle] => use at router - can overwrite layout for a single network<br>

<h4>e. clients-layouts per switch-cluster:</h4>
  - grid<br>
  - circle<br>
  - half_circle<br>
  - hierarchical<br>
  - snowflake<br>
