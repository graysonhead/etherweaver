from netweaver.core_classes.config_object import ConfigObject


class Fabric(ConfigObject):

	def __init__(self, name, config):
		self.name = name
		self.config = config
		self.appliances = []

	def __repr__(self):
		return '<Fabric: {}>'.format(self.name)
