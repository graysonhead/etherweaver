class SSHCommandError(Exception):
	"""
	SSH Command exits on error code
	"""
	def __init__(self, msg):
		super().__init__('SSH Command exited on error:' + str(msg))