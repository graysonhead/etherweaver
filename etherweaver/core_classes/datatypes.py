from etherweaver.core_classes.utils import extrapolate_dict, extrapolate_list, smart_dict_merge


class WeaverConfig(object):

	def __init__(self, config_dict):
		self.config = config_dict
		if 'vlans' in self.config:
			self.config['vlans'] = extrapolate_dict(self.config['vlans'], int_key=True)
		if 'interfaces' in self.config:
			new_int = {}
			for kspd, vspd in self.config['interfaces'].items():
				for kint, vint in self.config['interfaces'][kspd].items():
					if 'tagged_vlans' in vint:
						vint['tagged_vlans'] = extrapolate_list(vint['tagged_vlans'], int_out=True)
				new_int.update({kspd: extrapolate_dict(vspd, int_key=True)})
			self.config['interfaces'] = new_int

	def merge_configs(self, config_obj):
		return WeaverConfig(smart_dict_merge(self.config, config_obj.config))