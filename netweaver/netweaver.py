from netweaver.network_role import NetworkRole
from netweaver.plugins.plugin_class_errors import *

class CliApp:

	def parse_pattern(self, pattern):
		pass

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Netweaver is an application to orchestrate network configurations.')
	parser.add_argument(type=str, name='selection-pattern', dest='selection-pattern')


