Current State
-------------

The current state of Etherweaver is pre-alpha. Featureset, syntax, and yaml
structure are all subject to change.

Currently, the only working plugin is for Cumulus Linux. I plan on acquiring some second hand
gear for some of the more popular vendors to write plugins for those as well.

Currently, our goal is to establish a minimum viable product capable of configuring:

- Hostname
- Dns resolver configuration
- NTP client configuration
- Switchport/Interface control
    - tagged vlans
    - untagged vlans (pvid)
    - CLAG/MLAG
- VLAN configuration
- LLDP configuration


Currently, the following features have been implemented in the Cumulus Switch plugin:

- Hostname
- DNS resolver configuration
- NTP client configuration
- Switchport/Interface control *
    - tagged vlans
    - untagged vlans (pvid)
- VLAN configuration *


\* partially implemented




