Getting Started
===============

Config Structure
----------------

Top Level objects
^^^^^^^^^^^^^^^^^

Etherweaver's config file (henceforth, referenced as config.yaml) must contain three sections:

.. code-block:: yaml
   :caption: config.yaml

   roles: # A list of all roles
   fabrics: # A list of all fabrics
   appliances: # A list of all hardware

Fabrics represent networks, or collections of network devices with similar settings (vlans, port profiles, etc).

Roles represent a desired configuration. They can reference certian objects from fabrics, and will usually identify
a single device or group of devices with similar configurations.

An appliance represents a network operating system to be configured, it's objects contain authentication credentials,
as well as instructions on how to contact and configure each appliance, and which plugin to use.

An Example Config
^^^^^^^^^^^^^^^^^

.. code-block:: yaml
   :caption: config.yaml

   fabrics:
      network1:
         vlans:
            4-10
      connections:
         ssh:
            username: user
            password: password!

   roles:
      distribution:
         fabric: network1
         interfaces:
            1G:
               1-22:
                  untagged_vlan: 4
                  tagged_vlans: 5-7
               23-24:
                  tagged_vlans: 4-10

   appliances:
      distsw1:
         role: distribution
         plugin_package: cumulus
         connections:
            ssh:
               hostname: 10.5.5.33

The inheritance structure flows like so:

Fabric -> Fabric*n -> roles -> appliances.

Appliances map to individual instances of hosts, but everything else is logically mapped to whatever makes sense for a given user.

Nodes
-----

Think of nodes as a meta-dictionary that allow you to access, modify, or remove the current state
of an appliance without writing any YAML. A node is respresented by it's path in the dict (which is the same as the config.yaml)

For instance, here are some valid nodes:

- protocols.dns.nameservers
- interfaces.1G.1
- hostname

Nodes have different commands depending on their type, for instance single value nodes (such as hostname) generally have
two commands:

- hostname.get
- hostname.set

List nodes will often have more command types:

- protocols.ntp.client.servers.add: Adds a single server
- protocols.ntp.client.servers.get: Gets a list of all servers
- protocols.ntp.client.servers.set: Overwrites the server list with a new list
- protocols.ntp.client.servers.del: deletes the list

Additionally, there are a few meta nodes such as 'state'. State is likely the one you will use the most, and it has two
functions:

- state.apply: Applies the current config.yaml
- state.get: Returns a yaml or json formatted dict representing the current state of the appliances specified


Commands
--------
Commands follow a simple syntax:

netweaver 'role|*' node --yaml=Yaml config file --value=Value to be written to a write node.



The YAML state can be applied to every appliance in the infrastructure file by running the following:

.. code-block:: bash

   netweaver.py '*' state.apply --yaml=config.yaml
   sw1: []
   sw2: []

The brackets will contain a list of any commands run in order to bring the switches in alignment with the current state.

You can view the current state of all appliances in the environment using the following command:

.. code-block:: bash

   netweaver.py 'sw1' state.get --yaml=config.yaml
   sw1:
      hostname: spine1.net.testco.org
      interfaces:
        100G: {}
        10G: {}
        1G:
          '1':
            ip:
              address: []
            tagged_vlans: [2, 3, 4]
            untagged_vlan: '7'
       ...


.. code-block:: bash

    etherweaver.py '*' protocols.ntp.client.servers.get --yaml=config.yaml
    sw1: [pool.ntp.org, 0.cumulusnetworks.pool.ntp.org, 1.cumulusnetworks.pool.ntp.org,
    2.cumulusnetworks.pool.ntp.org]
    sw2: [0.cumulusnetworks.pool.ntp.org, 1.cumulusnetworks.pool.ntp.org, 2.cumulusnetworks.pool.ntp.org,
    pool.ntp.org]



.. code-block:: bash

   netweaver.py 'sw1' hostname.set --value='spine2' --yaml=config.yaml
    net add hostname spine2

Note: Currently not all config nodes work. Accessing any disabled
nodes should raise a NotSupported error