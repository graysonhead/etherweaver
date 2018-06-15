from netweaver.core_classes.config_object import ConfigObject
from netweaver.plugins.cumulus.cumulus_switch import CumulusSwitch  #TODO Dynamic plugin loading


class Appliance(ConfigObject):

	def __init__(self, name, appliance_dict):
		self.name = name
		self.config = appliance_dict

	def __repr__(self):
		return '<Appliance: {}>'.format(self.name)
