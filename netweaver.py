import argparse
import yaml
from netweaver.core_classes.infrastructure import Infrastructure

class CLIApp:

	def __init__(self, tgt, func, yaml=None):
		self.tgt = tgt
		self.func = func
		self.config = None  # This is defined by the parsers below
		if yaml:
			self.config = self._parse_yaml_file(yaml)

		self._build_infrastructure_object()


	def _parse_yaml_file(self, yamlfile):
		"""Read Yaml from file and send to parse_yaml_string"""
		with open(yamlfile, 'r') as stream:
			try:
				return yaml.safe_load(stream)
			except yaml.YAMLError:
				raise

	def _build_infrastructure_object(self):
		"""
		This builds instances of the appliance class.
		"""
		self.inf = Infrastructure(self.config)

	def run(self):
		return self._parse_target(self.tgt).plugin.command(self.func)

	def _parse_target(self, target):
		for a in self.inf.appliances:
			if a.name == target:
				return a




if __name__ == '__main__':
	pass
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
	# target = '0c-b3-6d-f1-11-00'
	# func = 'get.hostname'
	# cli = CLIApp(target, func, yaml='exampleconfig.yaml')
	print(cli.run())
