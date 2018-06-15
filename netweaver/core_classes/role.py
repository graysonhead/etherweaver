from netweaver.core_classes.config_object import ConfigObject


class NetworkRole(ConfigObject):

	def __init__(self, name, role_dict=None):
		self.name = name
		self.conf = role_dict

	def __repr__(self):
		return '<Role: {}>'.format(self.name)
