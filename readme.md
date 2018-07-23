# Etherweaver

[![Build Status](https://travis-ci.com/graysonhead/etherweaver.svg?branch=master)](https://travis-ci.com/graysonhead/etherweaver)
[![Docs Status](https://readthedocs.org/projects/netweaver/badge/?version=latest)](https://netweaver.readthedocs.io/en/latest/#)

Etherweaver is an agentless configuration management system.

Similar to Ansible and Salt, the goal of Etherweaver is to abstract the task of managing large switch fabrics.


### Core Design Concepts

* ##### Universal States for Different Platforms

   A switch switches packets, and a router routes them. If they follow standards, they will perform this job identically. While the featureset may be disimilar between two platforms from different vendors, the way they implement protocols are similar, as is the end result. 

   The goal of Etherweaver is to allow the user to create a "universal" definition of their desired state (configuration), and disconnect the format of this configuration from the vendor-specific OS it is being applied to.

* #### Idempotent and Self-recovering

  To reduce the chance of Etherweaver causing momentary outages, it should always compare the current state with the desired state, and avoid making changes if they are equivelant.
  
  When possible, Etherweaver should use clever config file management and rollback functionality on network appliances to reduce the risk of a bad statement causing a permanent management disconnection.
  
* #### Agentless

  Closed source switching and routing platforms shouldn't be excluded from config management. Thus, Etherweaver is agentless by default. Each plugin will support a number of methods (ssh, telnet, RS232, etc.) to ensure that all networks can be maintained in an automated fashion.
  
  

## Config Structure

### Top Level objects
```yaml
roles: # A list of all roles
fabrics: # A list of all fabrics
appliances: # A list of all hardware
```

### Roles

A Role describes the state and attributes that can describe a specific appliance, or group of appliances.

Roles can be defined on a per device status (for example, you may have role objects for individual switches, or you may have a single template that describes the configuration of hundreds of switches.)

Here is an example of a Role Object as defined in YAML:
```yaml
roles:
  spine1:
    fabric: network1
    hostname: spine1.net.testco.org
    protocols:
      dns:
        nameservers:
            - 10.5.5.115
      ntp:
        client:
          timezone: America/Chicago
          servers:
              - pool.ntp.org
              - 0.cumulusnetworks.pool.ntp.org
              - 1.cumulusnetworks.pool.ntp.org
              - 2.cumulusnetworks.pool.ntp.org
    interfaces:
      1G:
        1-5:
          tagged_vlans: [2-4]
          untagged_vlan: 7
        6:
          untagged_vlan: 5
```

### Fabrics

A fabric is a collection of common configuration items, usually representing a switch fabric in a single location. However, it can represent whatever you want. Its simply a logical construct.

Here is an example of a fabric object:

```yaml
fabrics:
  network1:
    credentials:
      username: cumulus
      password: CumulusLinux!
    vlans:
      1-5:
      6:
        description: Data
      30:
        description: Public
      11-29:
```
## Appliances

Here is an example Appliance object. 

Appliances are defined by a hyphen separated MAC address. On switches with multiple MAC addresses, the MAC of the out of band management port should be used. Or, if no management port exists, the lowest number switch port.

This file contains all hardware specific information.

```yaml
appliances:
  sw1:
    hostname: 10.5.5.33
    role: spine1
    plugin_package: cumulus
  sw2:
    hostname: 10.5.5.34
    role: spine2
    plugin_package: cumulus
```

## Usage

Etherweaver uses a salt-like syntax:

```
Etherweaver.py 'sw1' role.apply --yaml=exampleconf.yaml
```

This command will apply the role spine1 to any assigned hardware appliances.

