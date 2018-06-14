from netweaver.core_classes.infrastructure import ConfigObject
from netweaver.plugins.cumulus.cumulus_switch import CumulusSwitch  #TODO Dynamic plugin loading


class Appliances(ConfigObject):

	def __init__(self, appliance_dict):
		self.app_dict = appliance_dict
