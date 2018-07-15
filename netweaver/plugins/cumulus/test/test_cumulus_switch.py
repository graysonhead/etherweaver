from netweaver.plugins.cumulus.cumulus_switch import CumulusSwitch
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

	def test_dns_nameservers_case1(self):
		dstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		cstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		self.assertEqual(self.plugin._protocol_dns_nameservers_push(dstate, cstate), None)

	def test_dns_nameservers_case2(self):
		dstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		cstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8']}}}
		self.plugin.cstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8']}}}
		self.assertEqual(self.plugin._protocol_dns_nameservers_push(dstate, cstate), ['net add dns nameserver ipv4 4.4.4.4'])

	def test_dns_nameservers_case3(self):
		dstate = {'protocols': {'dns': {'nameservers': ['8.8.8.8', '4.4.4.4']}}}
		cstate = {'protocols': {'dns': {'nameservers': []}}}
		self.plugin.cstate = {'protocols': {'dns': {'nameservers': []}}}
		self.assertEqual(set(self.plugin._protocol_dns_nameservers_push(dstate, cstate)),
		                 set(['net add dns nameserver ipv4 4.4.4.4', 'net add dns nameserver ipv4 8.8.8.8']))

	def test_ntpclient_tz_push_case1(self):
		dstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago'}}}}
		cstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago'}}}}
		self.assertEqual(self.plugin._protocol_ntpclient_timezone_push(cstate, dstate), None)

	def test_ntpclient_tz_push_case2(self):
		dstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago'}}}}
		cstate = {'protocols': {'ntp': {'client': {'timezone': None}}}}
		self.assertEqual(self.plugin._protocol_ntpclient_timezone_push(cstate, dstate), 'net add time zone America/Chicago')

	def test_ntpclient_server_push_case1(self):
		dstate = {'protocols': {'ntp': {'client': {'servers': ['server1.server.com']}}}}
		cstate = {'protocols': {'ntp': {'client': {'servers': []}}}}
		self.plugin.cstate = cstate
		self.assertEqual(self.plugin._protocol_ntpclient_servers(dstate, cstate), ['net add time ntp server server1.server.com iburst'])

if __name__ == '__main__':
	unittest.main()