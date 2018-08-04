import unittest
from etherweaver.core_classes.appliance import Appliance
from etherweaver.core_classes.infrastructure import Infrastructure

mock = {
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

class TestPluginLoader(unittest.TestCase):
	def test_plugin_loader(self):

		inf = Infrastructure(mock)
		self.assertEqual(inf.appliances[0].plugin.is_plugin, True)


class TestInfrastructureClass(unittest.TestCase):
	def test_infrastructure_class(self):
		inf = Infrastructure(mock)
		self.assertEqual(inf.is_infrastructure, True)
		self.assertEqual(inf.appliances[0].is_appliance, True)
		self.assertEqual(inf.fabrics[0].is_fabric, True)
		self.assertEqual(inf.appliances[0].role.is_role, True)
		self.assertEqual(inf.appliances[0].plugin.is_plugin, True)


if __name__ == '__main__':
	unittest.main()
