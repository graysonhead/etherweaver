Configuration Elements
======================

Nodes
-----
All elements can contain the following nodes:

.. Taken from WeaverConfig.gen_config_skel()

.. code-block:: json

    {
			'hostname': None,
			'vlans': {},
			'port_profiles': {},
			'protocols': {
				'dns': {
					'nameservers': []
				},
				'ntp': {
					'client': {
						'servers': [],
						'timezone': None
					}
				}
			},
			'interfaces': {
				'1G': {},
				'10G': {},
				'40G': {},
				'100G': {},
				'mgmt': {}
			}
		}

Each interface can contain the following nodes:

.. Taken from WeaverConfig.gen_portskel()

.. code-block:: json

    {
			'tagged_vlans': [],
			'untagged_vlan': None,
			'ip': {
				'address': []
			}

		}

Type Specific nodes:
--------------------

Appliance
^^^^^^^^^

.. code-block:: json

    {
		'role': references parent role object,
		'plugin_package': references plugin package,
		'connections': {
			'ssh': {
				'hostname': hostname of ssh connection,
				'username': username of ssh connection,
				'password': password of ssh connection,
				'port': ssh port
			}
		}
	}

Role
^^^^

.. code-block:: json

    {
			'fabric': references parent fabric object
		}

Fabric
^^^^^^

.. code-block:: json

    {
			'fabric': references parent fabric object
		}

List Expansion
==============

Wherever lists are valid values, items following the pattern '1-3' will be expanded.

For instance: [1, 3, 7-9] will be expanded to [1, 3, 7, 8, 9]


Interface Profiles
==================

If any object in the inheritance chain contains a port_profiles node, this profile can be referenced
either at the same level or in a child object. This allows you to re-use common port configurations.

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
        role: dist1
        plugin_package: cumulus
        connections:
          ssh:
            hostname: 10.5.5.33
            username: cumulus
            password: CumulusLinux!
            port: 22