from netweaver.core_classes.infrastructure import ConfigObject


class Fabric(ConfigObject):

	def __init__(self, name, config):
		self.name = name
		self.config = config
