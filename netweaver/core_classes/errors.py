class MissingRequiredAttribute(Exception):
	"""
	There is a required attribute missing from a dict
	"""


	def __init__(self, msg, objname):
		super().__init__('Missing Attribute on object {}: {}'.format(objname, msg))