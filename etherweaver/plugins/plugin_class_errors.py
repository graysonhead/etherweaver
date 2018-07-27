class SSHCommandError(Exception):
	"""
	SSH Command exits on error code
	"""
	def __init__(self, msg):
		super().__init__('SSH Command exited on error:' + str(msg))

class FeatureNotSupported(Exception):
	"""
	The selected plugin doesn't support the feature
	"""
	def __init__(self, plugin, msg):
		super().__init__('The plugin {} does not support the {} command'.format(plugin, msg))


class FeatureNotImplemented(Exception):
	"""
	Pre or post function not needed, so not implemented
	"""
	def __init__(self):
		super().__init__("Not implemented")