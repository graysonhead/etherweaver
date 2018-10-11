Configuration Elements
======================

Nodes
-----

.. note:: This is a stand-in for some custom auto-documentation I haven't dealt with yet.
            If you are interested in tackling this, take a look at this Issue_.

.. _Issue: https://github.com/graysonhead/etherweaver/issues/61

Main Nodes
^^^^^^^^^^
.. code-block:: text


    {
			'dstate': {
				'apply': self.push_state,
				'get': self.dstate,
				'allowed_functions': ['get', 'apply'],
				'description': "Interact with the desired state of the appliance, either viewing the desired state"
				" or applying it non-interactively."
			},
			'cstate': {
				'get': self.cstate,
				'allowed_functions': ['get']
			},
			'hostname': {
				'set': self.plugin.set_hostname,
				'get': self.plugin.cstate['hostname'],
				'data_type': str,
				'allowed_functions': ['get', 'set', 'del']
			},
			'vlans': {
				'get': self.plugin.cstate['vlans'],
				'set': self.plugin.set_vlans,
				'allowed_functions': ['get', 'set', 'add', 'del']
			},
			'clag': {
				'get': self.cstate['clag'],
				'allowed_functions': ['get'],
				'shared_mac': {
					'get': self.cstate['clag']['shared_mac'],
					'set': self.plugin.set_clag_shared_mac,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				},
				'priority': {
					'get': self.cstate['clag']['priority'],
					'set': self.plugin.set_clag_priority,
					'data_type': int,
					'allowed_functions': ['get', 'set', 'del']
				},
				'backup_ip': {
					'get': self.cstate['clag']['backup_ip'],
					'set': self.plugin.set_clag_backup_ip,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				},
				'clag_cidr': {
					'get': self.cstate['clag']['clag_cidr'],
					'set': self.plugin.set_clag_cidr,
					'data_type': list,
					'list_subtype': str,
					'allowed_functions': ['get', 'set', 'del', 'add']
				},
				'peer_ip': {
					'get': self.cstate['clag']['peer_ip'],
					'set': self.plugin.set_clag_peer_ip,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				}
			},
			'interfaces': {
				'get': self.cstate['interfaces'],
				'allowed_functions': ['get'],
				'1G': {
					'get': self.cstate['interfaces']['1G'],
					'allowed_functions': ['get']
				},
				'10G': {
					'get': self.cstate['interfaces']['10G'],
					'allowed_functions': ['get']
				},
				'40G': {
					'get': self.cstate['interfaces']['40G'],
					'allowed_functions': ['get']
				},
				'100G': {
					'get': self.cstate['interfaces']['100G'],
					'allowed_functions': ['get']
				},
				'bond': {
					'get': self.cstate['interfaces']['bond'],
					'allowed_functions': ['get']
				}
			},
			'protocols': {
				'ntp': {
					'get': self.cstate['protocols']['ntp'],
					'allowed_functions': ['get'],
					'client':
						{
							'timezone': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['timezone'],
								'set': self.plugin.set_ntp_client_timezone,
								'data_type': str,
								'allowed_functions': ['get', 'set']
							},
							'servers': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['servers'],
								'set': self.plugin.set_ntp_client_servers,
								'data_type': list,
								'list_subtype': str,
								'allowed_functions': ['get', 'set', 'del', 'add']
							},
							'get': self.plugin.cstate['protocols']['ntp']['client'],
							'allowed_functions': ['get']
						}
				},
				'dns': {
					'get': self.plugin.cstate['protocols']['dns'],
					'allowed_functions': ['get'],
					'nameservers': {
						'get': self.plugin.cstate['protocols']['dns']['nameservers'],
						'set': self.plugin.set_dns_nameservers,
						'data_type': list,
						'data_subtype': str,
						'allowed_functions': ['get', 'set', 'del', 'add']
					}
				}
			}
		}

Interface Nodes
^^^^^^^^^^^^^^^

.. code-block:: text

        {
				'get': int_cstate,
				'set': self.plugin.set_interface,
				'allowed_functions': ['set', 'get'],
				'ip': {
					'get': int_cstate['ip'],
					'allowed_functions': ['get'],
					'addresses': {
						'get': int_cstate['ip']['addresses'],
						'set': self.plugin.set_interface_ip_addresses,
						'data_type': list,
						'list_subtype': str,
						'allowed_functions': ['get', 'add', 'set', 'del']
					}
				},
				'untagged_vlan': {
					'get': int_cstate['untagged_vlan'],
					'set': self.plugin.set_interface_untagged_vlan,
					'data_type': int,
					'allowed_functions': ['get', 'set', 'del']
				},
				'tagged_vlans': {
					'get': int_cstate['tagged_vlans'],
					'set': self.plugin.set_interface_tagged_vlans,
					'data_type': list,
					'list_subtype': int,
					'allowed_functions': ['get', 'set', 'add', 'del']
				}
			}

Interface Specific Nodes
........................

.. code-block:: text

    {
				'stp': {
					'get': int_cstate['stp'],
					'allowed_functions': ['get'],
					'port_fast': {
						'get': int_cstate['stp']['port_fast'],
						'set': self.plugin.set_portfast,
						'allowed_functions': ['get', 'set']
					}
				},
				'bond_slave': {
					'get': int_cstate['bond_slave'],
					'set': self.plugin.set_bond_slaves,
					'data_type': str,
					'allowed_functions': ['get', 'delete', 'set']
				},
				'mtu': {
					'get': int_cstate['mtu'],
					'set': self.plugin.set_interface_mtu,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				}
			}

Bond Specific Nodes
...................

.. code-block:: text

    {
				'clag_id': {
					'get': int_cstate['clag_id'],
					'set': self.plugin.set_bond_clag_id,
					'data_type': int,
					'allowed_functions': ['get', 'set', 'del']
				},
				'mtu': {
					'get': int_cstate['mtu'],
					'set': self.plugin.set_bond_mtu,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				}
			}

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
