Configuration Elements
======================

Nodes
-----


Type Specific nodes
^^^^^^^^^^^^^^^^^^^

TBD


List Expansion
--------------

Wherever lists are valid values, items following the pattern '1-3' will be expanded.

For instance: [1, 3, 7-9] will be expanded to [1, 3, 7, 8, 9]


Interface Profiles
------------------

If any object in the inheritance chain contains a port_profiles node, this profile can be referenced
either at the same level or in a child object. This allows you to re-use common port configurations.
You can stop the application of profiles on a lower level by defining 'profile: false'.

For example:

.. code-block:: yaml

    fabrics:
      network1:
        vlans:
          4-10:
        fabric: toplevelnet
        port_profiles:
          access:
            untagged_vlan: 1
          wap_trunk:
            untagged_vlan: 2
            tagged_vlans: [4-6, 10]

    roles:
      dist1:
        fabric: network1
      interfaces:
        1G:
          4-5:
            profile: access
          1:
            profile: wap_trunk

    appliances:
      sw1:
        interfaces:
            5:
              profile: false
              untagged_vlan: 10
        role: dist1
        plugin_package: cumulus
        connections:
          ssh:
            hostname: 10.5.5.33
            username: cumulus
            password: CumulusLinux!
            port: 22

Iterator Keys
-------------

Iterator keys are used for dynamic naming of parts of a string value, or an int value.
Iterator keys lets you significantly reduce the number of lines needed to implement
certian functionality homogeneously across many switchports. Right now, the only iterator key
is '$i', and it represents either the number ID, or number component of the port or bond respectively.

For example:

.. code-block:: yaml

    interfaces:
      1G:
        1-5:
          bond_slave: po$i
      bond:
        po1-5:
          clag_id: $i

Is equivalent to:

.. code-block:: yaml

    interfaces:
      1G:
        1:
          bond_slave: po1
        2:
          bond_slave: po2
        3:
          bond_slave: po3
        4:
          bond_slave: po4
        5:
          bond_slave: po5
      bond:
        po1:
          clag_id: 1
        po2:
          clag_id: 2
        po3:
          clag_id: 3
        po4:
          clag_id: 4
        po5:
          clag_id: 5
