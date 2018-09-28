Getting Started
===============

Config Structure
----------------

Top Level objects
^^^^^^^^^^^^^^^^^

Etherweaver's can consist of two sections, of which Fabrics are optional:

.. code-block:: yaml
   :caption: config.yaml

   fabrics: # A list of all fabrics
   appliances: # A list of all hardware

Fabrics represent networks, or collections of network devices with inherited settings.

An appliance represents a network operating system to be configured, and it inherits settings (as well as defining it's own).

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
         fabric: distribution
         plugin_package: cumulus
         connections:
            ssh:
               hostname: 10.5.5.33

The inheritance structure flows in this manner:

Fabric -> Child Fabric*n -> appliances.

A node specified twice will take the value of the last object to specify it in the structure.

Nodes
-----

Nodes represent a dictionary structure that allow you to access, modify, or remove the current state
of an appliance without writing any YAML. A node is represented by it's path in the dict (which is the same as the config.yaml)

For instance, here are some valid nodes:

- protocols.dns.nameservers
- interfaces.1G.1
- hostname

Nodes have different commands depending on their type. For instance single value nodes (such as hostname) generally have
three commands:

- hostname.get
- hostname.set
- hostname.del

List nodes will often have more command types:

- protocols.ntp.client.servers.add: Adds a server or servers
- protocols.ntp.client.servers.get: Gets a list of all servers
- protocols.ntp.client.servers.set: Overwrites the server list with a new list
- protocols.ntp.client.servers.del: If a value is specified, deletes the value, otherwise deletes all values

Additionally, there are a few meta nodes such as 'state'. State is likely the one you will use the most, and it has one function:

- state.apply: Applies the current config.yaml in an interactive manner

In addition there are also two additional state nodes with the following commands:

- cstate.get: Fetch current state of the appliance
- dstate.get: Fetch desired state of the appliance (based on config.yaml)
- dstate.apply: Non-interactively apply the desired state without confirmation



Commands
--------
Commands follow a simple syntax:

netweaver 'role|*' node value --yaml=config.yaml

The YAML state can be applied to every appliance in the infrastructure file by running the following:

.. code-block:: bash

   netweaver.py '*' state.apply --yaml=config.yaml
   sw1: []
   sw2: []

The brackets will contain a list of any commands run in order to bring the switches in alignment with the current state.

You can view the current state of all appliances in the environment using the following command:

.. code-block:: bash

   netweaver.py 'sw1' cstate.get --yaml=config.yaml
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

   netweaver.py 'sw1' hostname.set 'spine2' --yaml=config.yaml
    net add hostname spine2

.. note::
    Not all appliance plugins can implement all nodes due to hardware limitations, accessing any unsupported node will
    result in a NotImplemented or NotSupported error.

Examples
--------

A Simple Example
^^^^^^^^^^^^^^^^

Lets imagine that you are tasked with deploying a switch fabric for
a small branch office, with two switches total. Based on the needs of the office,
you determine that you need two 24 port switches, which are to be configured using the following rules:

- VLANs for Employees, VOIP phones, servers, Public Wireless, and Management interfaces
- Ports 1-20 on both switches will be for employee usage, and will need the Employee VLAN untagged and the VOIP vlan tagged for phone passthrough
- Ports 20-22 on both switches are reserved for Wireless access points, and need to be untagged on the Management VLAN for AP administration, and tagged on Employee and Public
- Port 24 will be the trunk between switches

From the system you are running etherweaver from, copy your public ssh keys to the switches (For switches that cannot
do this, you can use a username and password, but you still need to accept the public ssh key of the system on your machine
to prevent man in the middle attacks.) Then you write an etherweaver state file, simple_example.yaml:

.. literalinclude:: ExampleConfigs/simple_example.yaml
   :language: yaml

Then, run:

.. literalinclude:: ExampleConfigs/serun1.txt


Now your switches are configured correctly, subsequent runs won't do anything because the curent state and desired state match.

To complicate matters, a developer now needs to have a development server at his desk. unfortunately, his port
is right in the middle of our 10-20 range, at port 11 on dist1. Not to worry though, we can place a config statement at
any lower inheritance level to override the port range.  All we need to do is add an interface definition for the port
in question, and define profile to false in order to stop inheritance. Now our state file looks like this:

.. literalinclude:: ExampleConfigs/simple_examplev2.yaml
   :language: yaml

And running the program gives us the following output:

.. literalinclude:: ExampleConfigs/serun2.txt

As you can see, etherweaver operated idempotently, only applying the changes from the desired state that
didn't match the current state. This allows you to easily manage and monitor config drift from within your environment.

CLAG
^^^^

The cumulus switches we have been using as an example also support a feature known as Clustering Link Aggregation, or CLAG.

This allows two independent switches to share link aggregation groups without a single point of failure, and without
stacking. This is an excellent use case for fabric inheritance, as there are attributes that the switches share, as well
as plenty that they don't. Here is an example CLAG configuration with etherweaver:

.. literalinclude:: ExampleConfigs/clag_example.yaml
   :language: yaml

