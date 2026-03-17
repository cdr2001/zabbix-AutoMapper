# automap-stable-v19

Neu in v19:
- Endgeräte-Layouts pro Switch-Cluster:
  - `grid`
  - `circle`
  - `half_circle`
- Standard über `endpoint_layout` in `config.json`
- Optional pro Switch oder Host über Tag überschreibbar:
  - `am.layout.endpoints=grid|circle|half_circle`
- Link-Abstand anpassbar:
  - Standard über `default_link_distance`
  - Optional per Tag `am.link.distance`
- Router bleibt im Zentrum des Snowflake-Layouts
- Switches liegen im Ring um den Router
- Endgeräte werden pro Switch-Cluster angeordnet
