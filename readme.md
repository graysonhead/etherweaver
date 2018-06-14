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

### Top Level objects
```yaml
roles: # A list of all roles
fabrics: # A list of all fabrics
appliances: # A list of all hardware
```

NetWeaver supports includes.

The the top level yaml generally looks like this.

```yaml
roles: !include roles.yml
fabrics: !include fabrics.yml
appliances: !include appliances.yml

```

### Roles

A Role describes the state and attributes that can describe a specific appliance, or group of appliances.

Roles can be defined on a per device status (for example, you may have role objects for individual switches, or you may have a single template that describes the configuration of hundreds of switches.)

Here is an example of a Role Object as defined in YAML:
```yaml
spine1: # The name of the object
  fabric: network1
  hostname: spine1.net.testco.org
  protocols: # Contains sub-objects that configure Network Protocols
    ipv4: 
      routing:
        default_gateway: 10.11.12.1
  interfaces: # Interfaces defines the physical and logical topology of a network object with switching capability
    1g: # Interfaces are distinguished by speed, and automatically translated to the correct format by the vendor specific plugins
      eth0: #represents out of band management interface
        ip: 10.11.12.2/24
    10g:
      1-40:
        profile: trunk # Profiles reference meta-network objects to reduce repeated statements
      peerlink.4094:
        ip: 169.254.1.1/30
        clag: # Clustering ling aggregation that references another Network Object to reduce configuration length
          peer_with: spine2
          clag_peer_ip: 169.254.1.2
          clag_backup_ip: 192.0.2.50
          clag_sys_mac: '44:38:39:FF:40:94'
      41:
        slave_of: peerlink.4094 
        connected_to: spine2.41 # "connected-to" statements can provide for physical interconnect drift management 
      42:
        slave_of: peerlink.4094
        connected_to: spine2.42

```

### Fabrics

A fabric is a collection of common configuration items, usually representing a switch fabric in a single location. However, it can represent whatever you want. Its simply a logical construct.

Here is an example of a fabric object:

```yaml
network1:
  vlans:
    - 1
    - 2:
        description: Management
    - 20:
        description: VOIP
    - 30:
        description: Data
    - 35:
        description: Public
  interface_profiles:
    trunk:
      untagged_vlan: 1
      tagged_vlans: [2, 20, 30, 35]
      lldp:
        enable: True
    desk_access:
      untagged_vlan: 30
      tagged_vlans: 20
      stp:
        mode: access_port
      lldp:
        enable: True
        tlv:
          - system-name
          - system-description
    Wireless_Access_Point:
      untagged_vlan: 2
      tagged_vlans: [35, 30]
      lldp:
        enable: True
        tlv: all
```
## Appliances

Here is an example Appliance object. 

Appliances are defined by a hyphen separated MAC address. On switches with multiple MAC addresses, the MAC of the out of band management port should be used. Or, if no management port exists, the lowest number switch port.

This file contains all hardware specific information.

```yaml
0c-b3-6d-f1-11-00:
  hostname: 10.5.5.33
  role: spine1
```
## Dependencies

- paramiko
- scp
- PyYAML

## Usage

Netweaver uses a salt-like syntax:

```
netweaver.py 'spine1' role.apply
```

This command will apply the role spine1 to any assigned hardware appliances.