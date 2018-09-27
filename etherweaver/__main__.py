import argparse
import yaml
from etherweaver.core_classes.infrastructure import Infrastructure
import pprint

pp = pprint.PrettyPrinter(indent=4)

class CLIApp:

	def __init__(self, yaml=None):
		self.config = None  # This is defined by the parsers below
		if yaml:
			self.config = self._parse_yaml_file(yaml)
			for k, v in self.config.items():
				if k not in ['roles', 'fabrics', 'appliances']:
					raise KeyError('Key \'{}\' not allowed at top level'.format(k))
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

	def run(self, target=None, func=None, value=None, yamlout=True):
		retval = self.inf.run_command(target, func, value)
		if type(retval) == dict or list:
			if not yamlout:
				retval = (pp.pprint(retval))
			else:
				retval = yaml.dump(retval)
		return retval





def main():
	pass
	#TODO move this to init for the class
	parser = argparse.ArgumentParser(
			description='Etherweaver is an application to orchestrate network configurations.')
	parser.add_argument('target', type=str)
	parser.add_argument('func', type=str)
	parser.add_argument('value', type=str, nargs='?', default=None)
	parser.add_argument(
		'--yaml',
		type=str,
		dest='yamlfile',
		help='YAML file containing appliances and fabric objects'
	)
	args = parser.parse_args()
	cli = CLIApp(yaml=args.yamlfile)
	print(cli.run(target=args.target, func=args.func, value=args.value))


if __name__ == '__main__':
	main()