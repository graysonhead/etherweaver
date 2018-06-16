from netweaver.core_classes.fabric import Fabric
from netweaver.core_classes.appliance import Appliance


class Infrastructure:

	def __init__(self, config_dict):
		self.appliances_conf = config_dict['appliances']
		self.roles_conf = config_dict['roles']
		self.fabrics_conf = config_dict['fabrics']
		self.fabrics = []

		self._build_fabric()
		self._build_appliances()

	def _build_fabric(self):
		for f, fv in self.fabrics_conf.items():
			fabobj = Fabric(f, fv)
			self.fabrics.append(fabobj)

	def _build_appliances(self):
		"""
		Iterates through selected fabrics and returns objects for the appliances that belong to those fabrics.
		:return:
		"""
		for fabric_object in self.fabrics:
			for role_key, role_object in self.roles_conf.items():
				if fabric_object.name == role_object['fabric']:
					app = Appliance(role_key, role_object)
					fabric_object.appliances.append(app)


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