from netweaver.core_classes.fabric import Fabric
from netweaver.core_classes.appliance import Appliance
from netweaver.core_classes.role import NetworkRole
from netweaver.core_classes.errors import MissingRequiredAttribute

class Infrastructure:
	"""
	This is the constructor/dependency injector for the Appliance, Fabric, and Role classes
	"""

	def __init__(self, config_dict):
		self.appliances_conf = config_dict['appliances']
		self.roles_conf = config_dict['roles']
		self.fabrics_conf = config_dict['fabrics']
		self.appliances = []
		self.fabrics = []
		self.roles = []

		self._build_infrastructure()

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
				if app.config['role'] == role.name:
					app.role = role
					role.appliances.append(app)
			for fabric in self.fabrics:  # Attach Appliances to fabrics
				if app.role.config['fabric'] == fabric.name:
					app.fabric = fabric
					fabric.appliances.append(app)


conf = {
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
inf = Infrastructure(conf)