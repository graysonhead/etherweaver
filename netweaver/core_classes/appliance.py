from netweaver.core_classes.config_object import ConfigObject
import unittest
from netweaver.server_config_loader import get_server_config
from importlib.machinery import SourceFileLoader
from .errors import *



class Appliance(ConfigObject):

	def __init__(self, name, appliance_dict):
		self.name = name
		self.config = appliance_dict
		self.fabric = None
		self.role = None
		self.plugin = None

	def load_plugin(self):
		'''
		:return: plugin initialized with self.config, error otherwise (e.g. incompatible with config, plugin not found..).
		'''
		path = self.get_plugin_path()
		package = SourceFileLoader('package', '{}/{}'.format(path, '__init__.py')).load_module()
		module = SourceFileLoader('module', '{}/{}'.format(path, package.information['module_name'])).load_module()
		plugin = getattr(module, package.information['class_name'])
		# return plugin(self.config)
		self.plugin = plugin(self.config, self.fabric.config)

	def get_plugin_path(self):
		try:
			return '{}/{}'.format(get_server_config()['plugin_path'], self.config['plugin_package'])
		except KeyError:
			raise NonExistantPlugin()

	def __repr__(self):
		return '<Appliance: {}>'.format(self.name)


class TestPluginLoader(unittest.TestCase):
	def test_plugin_loader(self):
		mock = {
					'hostname': '10.0.0.1',
					'role': 'spine1',
					'plugin_package': 'cumulus'
				}
		appl = Appliance("00-00-00-00-00-00",  mock)
		inst = appl.load_plugin()
		self.assertEqual(inst.is_plugin(), True)


if __name__ == '__main__':
	unittest.main()