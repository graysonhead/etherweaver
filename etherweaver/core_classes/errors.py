class MissingRequiredAttribute(Exception):
	"""
	There is a required attribute missing from a dict
	"""

	def __init__(self, msg, objname):
		super().__init__('Missing Attribute on object {}: {}'.format(objname, msg))


class NonExistantPlugin(Exception):
	"""
	The plugin name is specified incorrectly, or plugin is missing
	"""

	def __init__(self, plugin):
		super()\
			.__init__('The plugin {} is either specified incorrectly, or missing from the plugin directory'.format(plugin))


class ConfigKeyError(Exception):
	"""
	Raised when an unknown or illegal key is used in a yaml file
	"""

	def __init__(self, key, value=None):
		super().__init__('Unknown key in \'{}\': \'{}\' in config'.format(key, value))