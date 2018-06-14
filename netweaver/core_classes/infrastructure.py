from netweaver.core_classes.fabric import Fabric

class ConfigObject(object):
	"""
	Some common stuff will probably wind up here in the future
	"""
	type = 'configObject'


class Infrastructure:

	def __init__(self, config_dict):
		self.appliances_conf = config_dict['appliances']
		self.roles_conf = config_dict['roles']
		self.fabrics_conf = config_dict['fabrics']
		self._build_fabric()

	def _build_fabric(self):
		self.fabrics = {}
		for f, fv in self.fabrics_conf.items():
			fabobj = Fabric(f, fv)
			self.fabrics.update({f: fabobj})



