from etherweaver.core_classes.config_object import ConfigObject


class NetworkRole(ConfigObject):

	def __init__(self, name, role_dict=None):
		self.name = name
		self.config = role_dict
		self.appliances = []
		self.is_role = True

	def __repr__(self):
		return '<Role: {}>'.format(self.name)
