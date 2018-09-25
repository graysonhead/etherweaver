from etherweaver.core_classes.utils import extrapolate_dict, extrapolate_list, smart_dict_merge
from etherweaver.core_classes.errors import ConfigKeyError, ReferenceNotFound


class WeaverConfig(object):

	def __init__(self, config_dict, name=None, validate=False):
		self.name = name
		self.type = None
		self.type_specific_keys = {}
		self.config = config_dict
		# Extrapolate abbreviated information within port_profiles (vlans, etc)
		if 'port_profiles' in self.config:
			for kp, vp in self.config['port_profiles'].items():
				vp = self._interface_extrapolate(vp)
		# Extrapolate any abbreviated vlans
		if 'vlans' in self.config:
			self.config['vlans'] = extrapolate_dict(self.config['vlans'], int_key=True)
		# Expand any interfaces present
		if 'interfaces' in self.config:
			new_int = {}
			for kspd, vspd in self.config['interfaces'].items():
					for kint, vint in self.config['interfaces'][kspd].items():
						# We can't extrapolate bonds as they are all strings
						kspd_ints = {}
						if kspd:
							kspd_ints.update(self._interface_extrapolate(vint))
					if kspd != 'bond':
						new_int.update({kspd: extrapolate_dict(vspd, int_key=True)})
					elif kspd == 'bond':
						new_int.update({kspd: vspd})
			self.config['interfaces'] = new_int
		if validate:
			self.validate()
		#self._clean_config()

	def _interface_extrapolate(self, inter):
		if 'tagged_vlans' in inter:
			inter['tagged_vlans'] = extrapolate_list(inter['tagged_vlans'], int_out=True)
		if 'untagged_vlan' in inter:
			if inter['untagged_vlan']:
				inter['untagged_vlan'] = int(inter['untagged_vlan'])
		return inter

	def _clean_config(self):
		pass

	def merge_configs(self, config_obj, validate=True, in_place=False):
		return WeaverConfig(smart_dict_merge(self.config, config_obj.config, in_place=in_place), validate=False)

	@staticmethod
	def gen_config_skel():
		return {
			'fabric': None,
			'role': None,
			'hostname': None,
			'vlans': {},
			'clag': {
				'shared_mac': None,
				'priority': None,
				'backup_ip': None,
				'peer_ip': None,
				'clag_cidr': None

			},
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
				'mgmt': {},
				'bond': {}
			}
		}

	@staticmethod
	def gen_portskel():
		return {
			'bond_slave': None,
			'tagged_vlans': [],
			'untagged_vlan': None,
			'ip': {
				'address': []
			},
			'stp': {
				'port_fast': False
			},

		}

	@staticmethod
	def gen_bondskel():
		return {
			'clag_id': None,
			'tagged_vlans': [],
			'untagged_vlan': None,
			'ip': {
				'address': []
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
			skip_set = [
				'vlans',
				'interfaces',
				'port_profiles'
			]
			invalid_keys = {}
			if k in skip_set:
				pass
			elif k in skel_dict:
				if type(v) is dict:
					self._validate_dict(config_dict[k], skel_dict[k])
			else:
				raise ConfigKeyError(k, value=v)

	def get_full_config(self):
		# Apply skeleton to the base config
		config = smart_dict_merge(self.gen_config_skel(), self.config)
		# Walk through interfaces section and apply interface skeletons
		if 'interfaces' in config:
			for ktyp, vtyp in config['interfaces'].items():
				# Regular interfaces get port skel
				if ktyp in ['1G', '10G', '40G', '100G']:
					for kint, vint in config['interfaces'][ktyp].items():
						# Apply portskel to each interface
						config['interfaces'][ktyp][kint] = smart_dict_merge(self.gen_portskel(), vint)
				elif ktyp in ['bond']:
					for kint, vint in config['interfaces'][ktyp].items():
						# Apply bondskel to each bond
						config['interfaces'][ktyp][kint] = smart_dict_merge(self.gen_bondskel(), vint)
		return config

	def apply_profiles(self):
		if 'interfaces' in self.config:
			for kspd, vspd in self.config['interfaces'].items():
				for kint, vint in self.config['interfaces'][kspd].items():
					if 'profile' in vint:
						try:
							self.config['interfaces'][kspd][kint] = self.config['port_profiles'][vint['profile']]
						except KeyError:
							raise ReferenceNotFound(vint['profile'])


class ApplianceConfig(WeaverConfig):

	def _type_specific_keys(self):
		self.type = 'Appliance'
		return {
		'role': str,
		'plugin_package': str,
		'connections': {
			'ssh': {
				'hostname': str,
				'username': str,
				'password': str,
				'port': int
			}
		}
	}

	def _clean_config(self):
		if 'role' in self.config:
			del(self.config['role'])


class FabricConfig(WeaverConfig):

	def _type_specific_keys(self):
		self.type = 'Fabric'
		return {
			'fabric': str
		}

	def _clean_config(self):
		if 'fabric' in self.config:
			del(self.config['fabric'])


# class RoleConfig(WeaverConfig):
#
# 	def _type_specific_keys(self):
# 		self.type = 'Role'
# 		return {
# 			'fabric': str
# 		}
#
# 	def _clean_config(self):
# 		if 'fabric' in self.config:
# 			del(self.config['fabric'])
