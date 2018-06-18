from netweaver.core_classes.config_object import ConfigObject


class Fabric(ConfigObject):

	def __init__(self, name, config):
		self.name = name
		self.config = config
		self.appliances = []
		self.is_fabric = True

	def __repr__(self):
		return '<Fabric: {}>'.format(self.name)
