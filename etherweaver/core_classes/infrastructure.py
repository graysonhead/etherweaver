from etherweaver.core_classes.fabric import Fabric
from etherweaver.core_classes.appliance import Appliance
from etherweaver.core_classes.role import NetworkRole
from etherweaver.core_classes.errors import MissingRequiredAttribute
from etherweaver.core_classes.utils import extrapolate_list, extrapolate_dict

class Infrastructure:
	"""
	This is the constructor/dependency injector for the Appliance, Fabric, and Role classes
	"""

	def __init__(self, config_dict):
		self.appliances_conf = config_dict['appliances']
		self.roles_conf = self._extrapolate_config_dict('role', config_dict['roles'])
		self.fabrics_conf = config_dict['fabrics']
		self.appliances = []
		self.fabrics = []
		self.roles = []
		self.is_infrastructure = True

		self._build_infrastructure()

	def _extrapolate_config_dict(self, type, config):
		"""
		:param type: 'role', 'appliance', or 'dict'
		:param config:
		:return:
		"""

		if type == 'role':
			for rolek, rolev in config.items():
				if 'interfaces' in rolev:
					for spdk, spdv in rolev['interfaces'].items():
						config[rolek]['interfaces'][spdk] = extrapolate_dict(spdv)
					for spdk, spdv in rolev['interfaces'].items():
						for intk, intv in spdv.items():
							if 'tagged_vlans' in intv:
								config[rolek]['interfaces'][spdk][intk]['tagged_vlans'] = extrapolate_list(intv['tagged_vlans'])
		return config

	def _build_infrastructure(self):
		"""
		Builds the requisite classes and injects dependencies
		"""
		self._build_appliances()
		self._build_fabrics()
		self._build_roles()
		self._associate_dependencies()

	def _build_appliances(self):
		"""
		Builds appliance objects from config
		"""
		for app_key, app_dict in self.appliances_conf.items():
			self.appliances.append(Appliance(app_key, app_dict))

	def _build_fabrics(self):
		for fabric_key, fabric_dict in self.fabrics_conf.items():
			self.fabrics.append(Fabric(fabric_key, fabric_dict))

	def _build_roles(self):
		for role_key, role_dict in self.roles_conf.items():
			self.roles.append(NetworkRole(role_key, role_dict))

	def _check_attribute(self, name, dictionary, attribute):
		try:
			dictionary[attribute]
		except:
			raise MissingRequiredAttribute(attribute, name)

	def _check_required_attributes(self):
		"""Check config for missing attribute names"""
		required_app_atribs = [
			'role',
			'hostname',
			'plugin_package'
		]
		for atrib in required_app_atribs:
			for appkey, appdict in self.appliances_conf.items():
				self._check_attribute(appkey, appdict, atrib)
		required_role_atribs = [
			'fabric'
		]
		for atrib in required_role_atribs:
			for appkey, appdict in self.roles_conf.items():
				self._check_attribute(appkey, appdict, atrib)

	def _associate_dependencies(self):
		"""Attach appliances to roles"""
		for app in self.appliances:
			for role in self.roles:
				try:
					if app.config['role'] == role.name:
						app.role = role
						role.appliances.append(app)
				except KeyError:
					raise SyntaxError('Appliance {} has no associated role'.format(app.name))
			for fabric in self.fabrics:  # Attach Appliances to fabrics
				if app.role.config['fabric'] == fabric.name:
					app.fabric = fabric
					fabric.appliances.append(app)
				if 'fabric' in fabric.config:
					for pfab in self.fabrics:
						if pfab.name == fabric.config['fabric']:
							fabric.parent_fabric = pfab
							pfab.child_fabrics.append(fabric)
			app.load_plugin()
			app.build_dstate()

	def _parse_target(self, target):
		for a in self.appliances:
			if a.name == target:
				return a

	def run_command(self, target, func, value):
		if target == '*':
			retvals = {}
			for app in self.appliances:
				retvals.update({app.name: app.run_individual_command(func, value)})
			return retvals
		appliance = self._parse_target(target)
		return appliance.run_individual_command(func, value)
