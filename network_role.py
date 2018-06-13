import yaml

class NetworkRole:

	def __init__(self, yamlfile=None):
		self.config = self._parse_yaml_file(yamlfile)

	def _parse_yaml_string(self, yaml):
		"""Parse yaml input to build structured Network Role Dict"""

	def _parse_yaml_file(self, yamlfile):
		"""Read Yaml from file and send to parse_yaml_string"""
		with open(yamlfile, 'r') as stream:
			try:
				return yaml.safe_load(stream)
			except yaml.YAMLError:
				raise


if __name__ == '__main__':
	nr = NetworkRole(yamlfile='../exampleconfig.yaml')
	print(nr.config)