from etherweaver.plugins.cumulus.cumulus_switch import CumulusSwitch
from etherweaver.core_classes.appliance import Appliance
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

		self.plugin = CumulusSwitch(appconfig)
		self.plugin.appliance = Appliance('testappliance', appconfig)
		# This makes me feel dirty
		self.plugin.appliance.plugin = self.plugin

	def test_plugin_load(self):
		self.assertEqual(self.plugin.is_plugin, True)

	def test_hostname_case3(self):
		dstate = {'hostname': 'test'}
		cstate = {'hostname': None}
		self.assertEqual(self.plugin.appliance._hostname_push(dstate, cstate), 'net add hostname test')

	def test_hostname_case2(self):
		dstate = {'hostname': 'newtest'}
		cstate = {'hostname': 'test'}
		self.assertEqual(self.plugin.appliance._hostname_push(dstate, cstate), 'net add hostname newtest')

	def test_hostname_case1(self):
		dstate = {'hostname': 'test'}
		cstate = {'hostname': 'test'}
		self.assertEqual(self.plugin.appliance._hostname_push(dstate, cstate), None)

	def test_dns_nameservers_case1(self):
		dstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		cstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		self.assertEqual(self.plugin.appliance._protocol_dns_nameservers_push(dstate, cstate), None)

	def test_dns_nameservers_case2(self):
		dstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		cstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8']}}}
		self.plugin.appliance.cstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8']}}}
		self.assertEqual(self.plugin.appliance._protocol_dns_nameservers_push(dstate, cstate), ['net add dns nameserver ipv4 4.4.4.4'])

	def test_dns_nameservers_case3(self):
		dstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		cstate = {'protocols': {'dns': {'nameservers': []}}}
		self.plugin.appliance.cstate = {'protocols': {'dns': {'nameservers': []}}}
		self.assertEqual(set(self.plugin.appliance._protocol_dns_nameservers_push(dstate, cstate)),
		                 set(['net add dns nameserver ipv4 4.4.4.4', 'net add dns nameserver ipv4 8.8.8.8']))

	def test_ntpclient_tz_push_case1(self):
		dstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago'}}}}
		cstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago'}}}}
		self.assertEqual(self.plugin.appliance._protocol_ntpclient_timezone_push(dstate, cstate), None)

	def test_ntpclient_tz_push_case2(self):
		dstate = {'protocols': {'ntp': {'client': {'timezone': 'Etc/UTC'}}}}
		cstate = {'protocols': {'ntp': {'client': {'timezone': None}}}}
		self.assertEqual(self.plugin.appliance._protocol_ntpclient_timezone_push(dstate, cstate), 'net add time zone Etc/UTC')

	def test_ntpclient_server_push_case1(self):
		dstate = {'protocols': {'ntp': {'client': {'servers': ['server1.server.com']}}}}
		cstate = {'protocols': {'ntp': {'client': {'servers': []}}}}
		self.plugin.appliance.cstate = cstate
		self.assertEqual(self.plugin.appliance._protocol_ntpclient_servers(dstate, cstate), ['net add time ntp server server1.server.com iburst'])

	def test_vlan_push_case1(self):
		dstate = {'vlans': {1: None, 2: None}}
		cstate = {'vlans': {1: None, 2: None}}
		self.plugin.appliance.cstate = cstate
		self.assertEqual(self.plugin.appliance._vlans_push(dstate, cstate), None)

	def test_vlan_push_case2(self):
		dstate = {'vlans': {1: None, 2: None}}
		cstate = {'vlans': {}}
		self.plugin.appliance.cstate = cstate
		self.assertEqual(self.plugin.appliance._vlans_push(dstate, cstate), ['net add bridge bridge vids 1-2'])
if __name__ == '__main__':
	unittest.main()