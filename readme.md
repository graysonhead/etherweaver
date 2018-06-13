# NetWeaver

Netweaver is an agentless configuration management system.

Similar to Ansible and Salt, the goal of NetWeaver is to abstract the task of managing large switch fabrics.

### Core Design Concepts

* ##### Vendor Agnostic

   Network engineers shouldn't have to consider the ease of configuring the equipment they are buying. The only factors they should consider are price and supported featureset. With proper config management tools, the process of configuring individual units of network equipment should be abstracted.
   
   To this end, NetWeaver supports a plugin structure to allow the open source community to collaboratively create plugins.

* #### Idempotent and Self-recovering

  To reduce the chance of NetWeaver causing momentary outages, it should always compare the current state with the desired state, and avoid making changes if they are equivelant.
  
  When possible, netweaver should use clever config file management and rollback functionality on network appliances to reduce the risk of a bad statement causing a permanent management disconnection.
  
* #### Agentless

  Closed source switching and routing platforms shouldn't be excluded from config management. Thus, NetWeaver is agentless by default. Each plugin will support a number of methods (ssh, telnet, RS232, etc.) to ensure that all networks can be maintained in an automated fashion.
  
  

## Config Structure

###Top Level objects
```yaml
roles: # A list of all roles
profiles: # A list of all profiles
hardware: # A list of all hardware
```

NetWeaver supports includes (not a standard feature of yaml.)

The the top level yaml generally looks like this.

```yaml
roles: !include roles.yml
profiles: !include profiles.yml
hardware: !include hardware.yml

```

###Roles

The base unit of NetWeaver's configuration is a Role. A Role describes the state and attributes that can describe a specific appliance, or group of appliances.

Roles can be defined on a per device status (for example, you may have role objects for individual switches, or you may have a single template that describes the configuration of hundreds of switches.)

Here is an example of a Role Object as defined in YAML:
```yaml
spine1: # The name of the object
  management: 
    hostname: spine1.net.testco.org
    ip_address: 10.11.12.2/24
    interface: vlan2
  protocols: # Contains sub-objects that configure Network Protocols
    ipv4: 
      routing:
        default_gateway: 10.11.12.1
    lldp: # LLDP is a protocol withing the protocols list
      tlv-med:
        - management-address
        - port-description
        - port-vlan
        - system-capabilities
        - system-description
        - system-name
  interfaces: # Interfaces defines the physical and logical topology of a network object with switching capability
    10G/1-40:
      profile: trunk # Profiles reference meta-network objects to reduce repeated statements
    peerlink.4094:
      ip: 169.254.1.1/30
      clag: # Clustering ling aggregation that references another Network Object to reduce configuration length
        peer_with: spine2
        clag-peer-ip: 169.254.1.2
        clag-backup-ip: 192.0.2.50
        clag-sys-mac: '44:38:39:FF:40:94'
    10G/41:
      slave-of: peerlink.4094 
      connected-to: spine2.41 # "connected-to" statements can provide for physical interconnect drift management 
    10G/42:
      slave-of: peerlink.4094
      connected-to: spine2.42

```
  