import unittest
from etherweaver.core_classes.appliance import Appliance
from etherweaver.core_classes.infrastructure import Infrastructure


class TestPluginLoader(unittest.TestCase):
	def test_plugin_loader(self):
		mock = {
			'roles':
				{'spine1':
					{
						'fabric': 'network1',
						'hostname': 'spine1.net.testco.org'
					}, 'spine2':
					{
						'fabric': 'network1',
						'hostname': 'spine2.net.testco.org'
					}
				},
			'fabrics': {
				'network1':
					{'credentials':
						{
							'username': 'cumulus',
							'password': 'CumulusLinux!'
						}
					}
			},
			'appliances':
				{'0c-b3-6d-f1-11-00':
					{
						'hostname': '10.5.5.33',
						'role': 'spine1',
						'plugin_package': 'cumulus'
					},
					'0c-b3-6d-9c-67-00':
						{
							'hostname': '10.5.5.34',
							'role': 'spine2',
							'plugin_package': 'cumulus'
						}
				}
		}
		inf = Infrastructure(mock)
		self.assertEqual(inf.appliances[0].plugin.is_plugin, True)


class TestInfrastructureClass(unittest.TestCase):
	def test_infrastructure_class(self):
		mock = {
				'roles':
					{'spine1':
						{
							'fabric': 'network1',
							'hostname': 'spine1.net.testco.org'
						}, 'spine2':
						{
							'fabric': 'network1',
							'hostname': 'spine2.net.testco.org'
						}
					},
				'fabrics': {
					'network1':
						{'credentials':
							{
								'username': 'cumulus',
								'password': 'CumulusLinux!'
							}
						}
					},
				'appliances':
					{'0c-b3-6d-f1-11-00':
						{
							'hostname': '10.5.5.33',
							'role': 'spine1',
							'plugin_package': 'cumulus'
						},
						'0c-b3-6d-9c-67-00':
							{
								'hostname': '10.5.5.34',
								'role': 'spine2',
								'plugin_package': 'cumulus'
							}
					}
				}
		inf = Infrastructure(mock)
		self.assertEqual(inf.is_infrastructure, True)
		self.assertEqual(inf.appliances[0].is_appliance, True)
		self.assertEqual(inf.fabrics[0].is_fabric, True)
		self.assertEqual(inf.appliances[0].role.is_role, True)
		self.assertEqual(inf.appliances[0].plugin.is_plugin, True)


if __name__ == '__main__':
	unittest.main()
