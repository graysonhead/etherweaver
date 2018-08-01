from etherweaver.core_classes.utils import extrapolate_dict, extrapolate_list
config = {'role': 'spine1', 'vlans': {'1-5': None}, 'plugin_package': 'cumulus',
		'connections': {'ssh': {'hostname': '10.5.5.33', 'username': 'cumulus', 'password': 'CumulusLinux!'}},
		'interfaces': {'1G': {'2-5': {'untagged_vlan': 1}}}}


class WeaverConfig(object):

	def __init__(self, config_dict):
		self.config = config_dict
		if 'vlans' in self.config:
			self.config['vlans'] = extrapolate_dict(self.config['vlans'])
		if 'interfaces' in self.config:
			new_int = {}
			for kspd, vspd in self.config['interfaces'].items():
				new_int.update({kspd: extrapolate_dict(vspd)})
			self.config['interfaces'] = new_int


