from .cumulus_switch import CumulusSwitch
import unittest

fabricconf = {
	'credentials': {
		'username': 'cumulus',
		'password': 'CumulusLinux!'
	}
}

appconfig = {
	'hostname': 'test'
}


class TestPlugin(unittest.TestCase):
	def setUp(self):
		self.plugin = CumulusSwitch(appconfig, fabricconf)

	def test_plugin_load(self):
		self.assertEqual(self.plugin.is_plugin, True)

	def test_hostname_case3(self):
		dstate = {'hostname': 'test'}
		cstate = {'hostname': None}
		self.assertEqual(self.plugin._hostname_push(dstate, cstate), 'net add hostname test')

	def test_hostname_case2(self):
		dstate = {'hostname': 'newtest'}
		cstate = {'hostname': 'test'}
		self.assertEqual(self.plugin._hostname_push(dstate, cstate), 'net add hostname newtest')

	def test_hostname_case1(self):
		dstate = {'hostname': 'test'}
		cstate = {'hostname': 'test'}
		self.assertEqual(self.plugin._hostname_push(dstate, cstate), None)

if __name__ == '__main__':
	unittest.main()