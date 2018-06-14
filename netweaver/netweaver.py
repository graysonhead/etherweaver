import argparse
import yaml


class CLIApp:

	def __init__(self, tgt, func, yaml=None):
		self.tgt = tgt
		self.func = func
		self.config = None  # This is defined by the parsers below
		if yaml:
			self.config = self._parse_yaml_file(yaml)

	def _parse_yaml_file(self, yamlfile):
		"""Read Yaml from file and send to parse_yaml_string"""
		with open(yamlfile, 'r') as stream:
			try:
				return yaml.safe_load(stream)
			except yaml.YAMLError:
				raise

	def run(self):
		for name, dict in self.config['appliances'].items():
			print(name)
			print(dict['hostname'])
			self._build_infrastructure_object()

	def _build_infrastructure_object(self):
		"""
		This builds instances of the appliance class.
		"""



if __name__ == '__main__':
	#TODO move this to init for the class
	parser = argparse.ArgumentParser(
			description='Netweaver is an application to orchestrate network configurations.')
	parser.add_argument('target', type=str)
	parser.add_argument('func', type=str)
	parser.add_argument(
		'--yaml',
		type=str,
		dest='yamlfile',
		help='YAML file containing the roles, appliances, and fabric objects'
	)
	args = parser.parse_args()
	cli = CLIApp(args.target, args.func, yaml=args.yamlfile)
	cli.run()





