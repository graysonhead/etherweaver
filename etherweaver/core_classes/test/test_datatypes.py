import unittest
from etherweaver.core_classes.datatypes import WeaverConfig


class TestDataTypeMerge(unittest.TestCase):
	def test_dataclass_merge(self):
		config = {'role': 'spine1', 'vlans': {'1-5': None}, 'plugin_package': 'cumulus',
				'connections': {'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}},
				'interfaces': {'1G': {'2-5': {'untagged_vlan': 1, 'tagged_vlans': ['2-5', 7]}}}}

		config1 = {'role': 'spine1', 'vlans': {'1-5': None}, 'plugin_package': 'cumulus',
				'connections': {
				'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}},
				'interfaces': {'1G': {'2-3': {'untagged_vlan': 5, 'tagged_vlans': ['1-5', '9-20']}}}}

		endconf = {'role': 'spine1', 'vlans': {1: None, 2: None, 3: None, 4: None, 5: None},
				'plugin_package': 'cumulus',
				'connections': {
				'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}},
				'interfaces': {
					'1G': {2: {'untagged_vlan': 5,
								'tagged_vlans': [1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]},
							3: {'untagged_vlan': 5,
								'tagged_vlans': [1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]},
							4: {'untagged_vlan': 5,
								'tagged_vlans': [1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]},
							5: {'untagged_vlan': 5,
								'tagged_vlans': [1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}}}}
		wc1 = WeaverConfig(config)
		wc2 = WeaverConfig(config1)
		mc = wc1.merge_configs(wc2)
		self.assertEqual(endconf, mc.config)