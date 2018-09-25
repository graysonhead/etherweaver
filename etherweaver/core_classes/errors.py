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

class ReferenceNotFound(Exception):
	"""
	Raised when a reference is not found elsewhere in the yaml
	"""

	def __init__(self, ref):
		super().__init__('Reference \'{}\' not found in config'.format(ref))

class ConfigKeyMissing(Exception):
	"""
	Raised when a required key is missing
	"""

	def __init__(self, key, section):
		super().__init__('Required key \'{}\' is missing from config section {}'.format(key, section))

class InvalidNodeFunction(Exception):
	"""
	Raised when an illegal function is attempted to be executed on a node
	"""

	def __init__(self, func, node):
		super().__init__('Function {} is not allowed on node {}'.format(func, node))