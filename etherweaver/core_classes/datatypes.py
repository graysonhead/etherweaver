from etherweaver.core_classes.utils import extrapolate_dict, extrapolate_list, smart_dict_merge
from etherweaver.core_classes.errors import ConfigKeyError


class WeaverConfig(object):

	def __init__(self, config_dict, name=None):
		self.name = name
		self.type = None
		self.type_specific_keys = {}
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
		self.validate()

	def merge_configs(self, config_obj):
		return WeaverConfig(smart_dict_merge(self.config, config_obj.config))


	def gen_config_skel(self):
		return {
			'hostname': None,
			'vlans': {},
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

	def validate(self):
		config_skel = self.gen_config_skel()
		# Config skel will be overriden by child classes to validate any class specific keys
		config_skel.update(self._type_specific_keys())
		self._validate_dict(self.config, config_skel)

	def _type_specific_keys(self):
		return {}

	def _validate_dict(self, config_dict, skel_dict):
		"""
		Currently only validates keys
		:param config_dict:
		Usually self.config.
		:param skel_dict:
		:return:
		"""
		for k, v in config_dict.items():
			# Ensure key is present in the skeleton config, otherwise it is invalid
			invalid_keys = {}
			if k in skel_dict and k is not 'interfaces':
				if type(v) is dict:
					self._validate_dict(config_dict[k], skel_dict[k])
			elif k is 'interfaces':
				pass
			else:
				raise ConfigKeyError(k, value=v)

	def get_full_config(self):
		return smart_dict_merge(self.config, self.gen_config_skel())


class ApplianceConfig(WeaverConfig):

	def _type_specific_keys(self):
		return {
		'role': str,
		'plugin_package': str,
		'connections': {
			'ssh': {
				'hostname': str,
				'username': str,
				'password': str
			}
		}
	}

class FabricConfig(WeaverConfig):

	def _type_specific_keys(self):
		return {
			'fabric': str
		}

class RoleConfig(WeaverConfig):

	def _type_specific_keys(self):
		return {
			'fabric': str
		}
