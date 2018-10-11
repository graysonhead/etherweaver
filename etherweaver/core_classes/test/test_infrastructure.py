import unittest
from etherweaver.core_classes.appliance import Appliance
from etherweaver.core_classes.infrastructure import Infrastructure
from etherweaver.__main__ import CLIApp

mock1 = {
			'roles':
				{
					'spine1': {
						'interfaces': {
							'1G': {
								1: {'untagged_vlan': 2}
							}
						},
						'fabric': 'network1'
					}
				},
			'fabrics': {
				'network1': {
					'vlans': {'4-10': None}
				}
			},
			'appliances': {
				'app1': {
					'plugin_package': 'cumulus',
					'hostname': 'host',
					'role': 'spine1',
					'connections': {
					'ssh': {
						'hostname': '10.5.5.33',
						'username': 'test',
						'password': 'test'
					}
				}
			}
		}
}

mock = {'roles': {
	'spine1': {'hostname': 'billy2', 'fabric': 'network1', 'interfaces': {'1G': {'1-6': {'untagged_vlan': 1}}}}},
        'fabrics': {'network1': {'vlans': {'4-10': None}, 'fabric': 'toplevelnet'},
                    'toplevelnet': {'vlans': {'1-10': 'None'}}}, 'appliances': {
		'sw1': {'role': 'spine1', 'plugin_package': 'cumulus',
		        'connections': {'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}},
		        'interfaces': {'1G': {'2-5': {'untagged_vlan': 1, 'tagged_vlans': [1, '2-5']}}}}}}


class TestPluginLoader(unittest.TestCase):

	def test_plugin_loader(self):
		inf1 = Infrastructure(mock1)
		self.assertEqual(inf1.appliances[0].plugin.is_plugin, True)


class TestInfrastructureClass(unittest.TestCase):
	def test_infrastructure_class(self):
		inf = Infrastructure(mock)
		self.assertEqual(inf.is_infrastructure, True)
		self.assertEqual(inf.appliances[0].is_appliance, True)
		self.assertEqual(inf.fabrics[0].is_fabric, True)
		self.assertEqual(inf.appliances[0].plugin.is_plugin, True)


class TestDstateInherit(unittest.TestCase):
	def test_basic_inheritance(self):
		correct_dstate = {'fabric': 'dist', 'role': None, 'hostname': 'dist1',
						'vlans': {1: None, 2: None, 3: None, 4: None, 5: None, 6: None},
						'clag': {'shared_mac': None, 'priority': None, 'backup_ip': None, 'peer_ip': None,
						'clag_cidr': []}, 'port_profiles': {}, 'protocols': {'dns': {'nameservers': []},
						'ntp': {
						'client': {'servers': [],
						'timezone': None}}},
						'interfaces': {'1G': {
						1: {'admin_down': False, 'delete': False, 'bond_slave': None, 'tagged_vlans': [3, 4], 'untagged_vlan': 2,
						'ip': {'addresses': []}, 'stp': {'port_fast': False}, 'mtu': None},
						2: {'admin_down': False, 'delete': False, 'bond_slave': None, 'tagged_vlans': [3, 4], 'untagged_vlan': 2,
						'ip': {'addresses': []}, 'stp': {'port_fast': False}, 'mtu': None},
						3: {'admin_down': False, 'delete': False, 'bond_slave': None, 'tagged_vlans': [3, 4], 'untagged_vlan': 2,
						'ip': {'addresses': []}, 'stp': {'port_fast': False}, 'mtu': None},
						4: {'admin_down': False, 'delete': False, 'bond_slave': None, 'tagged_vlans': [3, 4], 'untagged_vlan': 2,
						'ip': {'addresses': []}, 'stp': {'port_fast': False}, 'mtu': None},
						5: {'admin_down': False, 'delete': False, 'bond_slave': None, 'tagged_vlans': [1, 2, 3, 4, 5, 6],
						'untagged_vlan': None, 'ip': {'addresses': []}, 'stp': {'port_fast': False},
						'mtu': None},
						6: {'admin_down': False, 'delete': False, 'bond_slave': None, 'tagged_vlans': [1, 2, 3, 4, 5, 6],
						'untagged_vlan': None, 'ip': {'addresses': []}, 'stp': {'port_fast': False},
						'mtu': None}}, '10G': {}, '40G': {}, '100G': {}, 'mgmt': {}, 'bond': {}},
						'plugin_package': 'cumulus', 'plugin_options': {'port_speed': '1G'},
						'connections': {'ssh': {'hostname': '192.168.122.121', 'username': 'cumulus', 'port': 22}}}
		cli = CLIApp(yaml='./etherweaver/core_classes/test/inheritancetest.yaml')
		cli._build_infrastructure_object()
		cli.inf.appliances[0].build_dstate()
		self.assertEqual(cli.inf.appliances[0].dstate, correct_dstate)



if __name__ == '__main__':
	unittest.main()
