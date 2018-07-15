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

    roles:
      spine1:
        fabric: network1
        hostname: spine1.net.testco.org
        protocols:
          dns:
            nameservers:
                - 10.5.5.115
        interfaces:
          1G:
            1:
              tagged_vlans: [2, 3, 4, 5, 6]
              untagged_vlan: 7

    fabrics:
      network1:
        credentials:
          username: cumulus
          password: CumulusLinux!
        vlans:
         2-6:

    appliances:
      sw1:
        hostname: 10.5.5.33
        role: spine1
        plugin_package: cumulus

The above configuration will configure one switch to set its hostname to "spine1.net.testco.org", set its nameserver to
"10.5.5.115", and configure interface 1 with a PVID of 7, and tagged vlans 2-6.

This state can be applied by running "netweaver.py sw1 state.apply --yaml=config.yaml"