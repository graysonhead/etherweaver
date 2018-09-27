import unittest
from etherweaver.core_classes.datatypes import ApplianceConfig, FabricConfig
import yaml

role = {'fabric': 'network1', 'interfaces': {'1G': {'1-6': {'untagged_vlan': 2}}}}
fabric = {'vlans': {'1-10': None}}
app = {'hostname': 'billy2', 'role': 'spine1', 'plugin_package': 'cumulus', 'connections': {'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}}, 'interfaces': {'1G': {'2-5': {'untagged_vlan': 1, 'tagged_vlans': [1, '2-5']}}}}


class TestDataTypeMerge(unittest.TestCase):
	def test_dataclass_merge(self):
		test_dict = {
			'role': 'spine1',
			'vlans': {1: None, 2: None, 3: None, 4: None, 5: None, 6: None, 7: None, 8: None, 9: None, 10: None},
			'interfaces': {'1G': {2: {'tagged_vlans': [1, 2, 3, 4, 5], 'untagged_vlan': 1},
			                      3: {'tagged_vlans': [1, 2, 3, 4, 5], 'untagged_vlan': 1},
			                      4: {'tagged_vlans': [1, 2, 3, 4, 5], 'untagged_vlan': 1},
			                      5: {'tagged_vlans': [1, 2, 3, 4, 5],
			                          'untagged_vlan': 1}}},
			'hostname': 'billy2',
			'plugin_package': 'cumulus',
			'connections': {'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}}}
		self.fabric = FabricConfig(fabric)
		self.app = ApplianceConfig(app)
		end = self.fabric.merge_configs(self.app, validate=False)
		self.assertEqual(end.config, test_dict)

class TestInterfaceProfile(unittest.TestCase):
	def test_interface_profile(self):
		appliance = {'port_profiles': {'toplel': {'untagged_vlan': 1}},
						'interfaces': {'1G': {1: {'profile': 'toplel'}}}}
		end = {'port_profiles': {'toplel': {'untagged_vlan': 1}}, 'interfaces': {'1G': {1: {'untagged_vlan': 1}}}}
		self.app = ApplianceConfig(appliance)
		self.app.apply_profiles()
		self.assertEqual(self.app.config, end)