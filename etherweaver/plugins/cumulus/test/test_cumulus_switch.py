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
		ports_by_name = {'bridge': {'portid': 'bridge', 'speed': '1G', 'mode': 'Bridge/L2'}, 'swp8': {'portid': 8, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp9': {'portid': 9, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp2': {'portid': 2, 'speed': '1G', 'mode': 'BondMember'}, 'swp3': {'portid': 3, 'speed': '1G', 'mode': 'BondMember'}, 'swp1': {'portid': 1, 'speed': '1G', 'mode': 'BondMember'}, 'swp6': {'portid': 6, 'speed': '1G', 'mode': 'BondMember'}, 'swp7': {'portid': 7, 'speed': '1G', 'mode': 'BondMember'}, 'swp4': {'portid': 4, 'speed': '1G', 'mode': 'BondMember'}, 'eth0': {'portid': 0, 'speed': '1G', 'mode': 'Mgmt'}, 'peerlink.4094': {'portid': 'eerlink.4094', 'speed': '2G', 'mode': 'SubInt/L3'}, 'swp19': {'portid': 19, 'speed': '1G', 'mode': 'NotConfigured'}, 'peerlink': {'portid': 'eerlink', 'speed': '2G', 'mode': 'LACP'}, 'swp10': {'portid': 10, 'speed': '1G', 'mode': 'NotConfigured'}, 'lo': {'portid': 'lo', 'speed': '1G', 'mode': 'Loopback'}, 'swp12': {'portid': 12, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp13': {'portid': 13, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp14': {'portid': 14, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp15': {'portid': 15, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp16': {'portid': 16, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp17': {'portid': 17, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp5': {'portid': 5, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp18': {'portid': 18, 'speed': '1G', 'mode': 'NotConfigured'}, 'po6': {'portid': 'o6', 'speed': '1G', 'mode': 'LACP'}, 'po7': {'portid': 'o7', 'speed': '1G', 'mode': 'LACP'}, 'po4': {'portid': 'o4', 'speed': '1G', 'mode': 'LACP'}, 'po2': {'portid': 'o2', 'speed': '1G', 'mode': 'LACP'}, 'po3': {'portid': 'o3', 'speed': '1G', 'mode': 'LACP'}, 'po1': {'portid': 'o1', 'speed': '1G', 'mode': 'LACP'}, 'swp21': {'portid': 21, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp20': {'portid': 20, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp23': {'portid': 23, 'speed': '1G', 'mode': 'BondMember'}, 'swp22': {'portid': 22, 'speed': '1G', 'mode': 'NotConfigured'}, 'swp24': {'portid': 24, 'speed': '1G', 'mode': 'BondMember'}, 'swp11': {'portid': 11, 'speed': '1G', 'mode': 'NotConfigured'}}
		ports_by_number = {'bridge': {'portname': 'bridge', 'speed': 'N/A', 'mode': 'Bridge/L2'}, 8: {'portname': 'swp8', 'speed': 'N/A', 'mode': 'NotConfigured'}, 9: {'portname': 'swp9', 'speed': 'N/A', 'mode': 'NotConfigured'}, 2: {'portname': 'swp2', 'speed': '1G', 'mode': 'BondMember'}, 3: {'portname': 'swp3', 'speed': '1G', 'mode': 'BondMember'}, 1: {'portname': 'swp1', 'speed': '1G', 'mode': 'BondMember'}, 6: {'portname': 'swp6', 'speed': '1G', 'mode': 'BondMember'}, 7: {'portname': 'swp7', 'speed': '1G', 'mode': 'BondMember'}, 4: {'portname': 'swp4', 'speed': '1G', 'mode': 'BondMember'}, 0: {'portname': 'eth0', 'speed': '1G', 'mode': 'Mgmt'}, 'eerlink.4094': {'portname': 'peerlink.4094', 'speed': '2G', 'mode': 'SubInt/L3'}, 19: {'portname': 'swp19', 'speed': 'N/A', 'mode': 'NotConfigured'}, 'eerlink': {'portname': 'peerlink', 'speed': '2G', 'mode': 'LACP'}, 10: {'portname': 'swp10', 'speed': 'N/A', 'mode': 'NotConfigured'}, 'lo': {'portname': 'lo', 'speed': 'N/A', 'mode': 'Loopback'}, 12: {'portname': 'swp12', 'speed': 'N/A', 'mode': 'NotConfigured'}, 13: {'portname': 'swp13', 'speed': 'N/A', 'mode': 'NotConfigured'}, 14: {'portname': 'swp14', 'speed': 'N/A', 'mode': 'NotConfigured'}, 15: {'portname': 'swp15', 'speed': 'N/A', 'mode': 'NotConfigured'}, 16: {'portname': 'swp16', 'speed': 'N/A', 'mode': 'NotConfigured'}, 17: {'portname': 'swp17', 'speed': 'N/A', 'mode': 'NotConfigured'}, 5: {'portname': 'swp5', 'speed': 'N/A', 'mode': 'NotConfigured'}, 18: {'portname': 'swp18', 'speed': 'N/A', 'mode': 'NotConfigured'}, 'o6': {'portname': 'po6', 'speed': 'N/A', 'mode': 'LACP'}, 'o7': {'portname': 'po7', 'speed': 'N/A', 'mode': 'LACP'}, 'o4': {'portname': 'po4', 'speed': 'N/A', 'mode': 'LACP'}, 'o2': {'portname': 'po2', 'speed': 'N/A', 'mode': 'LACP'}, 'o3': {'portname': 'po3', 'speed': 'N/A', 'mode': 'LACP'}, 'o1': {'portname': 'po1', 'speed': 'N/A', 'mode': 'LACP'}, 21: {'portname': 'swp21', 'speed': 'N/A', 'mode': 'NotConfigured'}, 20: {'portname': 'swp20', 'speed': 'N/A', 'mode': 'NotConfigured'}, 23: {'portname': 'swp23', 'speed': '1G', 'mode': 'BondMember'}, 22: {'portname': 'swp22', 'speed': 'N/A', 'mode': 'NotConfigured'}, 24: {'portname': 'swp24', 'speed': '1G', 'mode': 'BondMember'}, 11: {'portname': 'swp11', 'speed': 'N/A', 'mode': 'NotConfigured'}}
		self.plugin.portmap = {'by_name': ports_by_name, 'by_number': ports_by_number}
		self.plugin.appliance.plugin = self.plugin

	def test_plugin_load(self):
		self.assertEqual(self.plugin.is_plugin, True)

	def test_hostname_case3(self):
		dstate = {'hostname': 'test'}
		cstate = {'hostname': None}
		self.assertEqual(self.plugin.appliance._hostname_push(dstate, cstate), ['net add hostname test'])

	def test_hostname_case2(self):
		dstate = {'hostname': 'newtest'}
		cstate = {'hostname': 'test'}
		self.assertEqual(self.plugin.appliance._hostname_push(dstate, cstate), ['net add hostname newtest'])

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
		dstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago', 'servers': []}}}}
		cstate = {'protocols': {'ntp': {'client': {'timezone': 'America/Chicago', 'servers': []}}}}
		self.assertEqual(self.plugin.appliance._protocol_ntpclient_push(dstate, cstate), [])

	def test_ntpclient_tz_push_case2(self):
		dstate = {'protocols': {'ntp': {'client': {'timezone': 'Etc/UTC', 'servers': []}}}}
		cstate = {'protocols': {'ntp': {'client': {'timezone': None, 'servers': []}}}}
		self.assertEqual(self.plugin.appliance._protocol_ntpclient_push(dstate, cstate), ['net add time zone Etc/UTC'])

	def test_ntpclient_server_push_case1(self):
		dstate = {'protocols': {'ntp': {'client': {'servers': ['server1.server.com'], 'timezone': None}}}}
		cstate = {'protocols': {'ntp': {'client': {'servers': [], 'timezone': None}}}}
		self.plugin.appliance.cstate = cstate
		self.assertEqual(self.plugin.appliance._protocol_ntpclient_push(dstate, cstate), ['net add time ntp server server1.server.com iburst'])

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

	# Ad Hoc command testing
	def test_set_interface_tagged_vlans(self):
		cstate = {'interfaces': {'1G': {1: {'tagged_vlans': [1, 2]}}}}
		self.plugin.appliance.cstate = cstate
		self.assertEqual(
			self.plugin.set_interface_tagged_vlans('1G', 1, [2, 3, 4], add=True, execute=False),
			 ['net add interface swp1 bridge vids 3-4']
			 )
		self.assertEqual(
			self.plugin.set_interface_tagged_vlans('1G', 1, None, delete=True, execute=False),
			['net del interface swp1 bridge vids 1-2']
		)
		self.assertEqual(
			self.plugin.set_interface_tagged_vlans('1G', 1, [2], delete=True, execute=False),
			['net del interface swp1 bridge vids 2']
		)
	def test_set_hostname(self):
		self.assertEqual(
			self.plugin.set_hostname('testhostname', execute=False),
			['net add hostname testhostname']
		)
		self.assertEqual(
			self.plugin.set_hostname(None, delete=True, execute=False),
			['net del hostname']
		)

	def test_set_interface_untagged_vlan(self):
		self.assertEqual(
			self.plugin.set_interface_untagged_vlan('1G', 1, 10, execute=False),
			['net add interface swp1 bridge pvid 10']
		)
		self.assertEqual(
			self.plugin.set_interface_untagged_vlan('1G', 1, None, delete=True, execute=False),
			['net del interface swp1 bridge pvid']
		)

	def test_set_clag_backup_ip(self):
		self.assertEqual(
			self.plugin.set_clag_backup_ip('192.168.1.1', execute=False),
			['net add interface peerlink.4094 clag backup-ip 192.168.1.1']
		)
		self.assertEqual(
			self.plugin.set_clag_backup_ip(None, delete=True, execute=False),
			['net del interface peerlink.4094 clag backup-ip']
		)
	# Disabled pending fix of a bug
	# def test_set_clag_cidr(self):
	# 	self.assertEqual(
	# 		self.plugin.set_clag_cidr('192.168.1.1/24', execute=False),
	# 		['net add interface peerlink.4094 ip address 192.168.1.1/24']
	# 	)
	# 	self.assertEqual(
	# 		self.plugin.set_clag_cidr(None, delete=True, execute=False),
	# 		['net del interface peerlink.4094 ip address']
	# 	)
	# def test_set_clag_peer_ip(self):
	# 	self.assertEqual(
	# 		self.plugin.set_clag_peer_ip('192.168.1.1', execute=False),
	# 		['net add interface peerlink.4094 clag peer-ip 192.168.1.1']
	# 	)
	# 	self.assertEqual(
	# 		self.plugin.set_clag_peer_ip(None, delete=True, execute=False),
	# 		['net del interface peerlink.4094 clag peer-ip']
	#	)
	def test_set_clag_priority(self):
		self.assertEqual(
			self.plugin.set_clag_priority(1001, execute=False),
			['net add interface peerlink.4094 clag priority 1001']
		)
		self.assertEqual(
			self.plugin.set_clag_priority(None, delete=True, execute=False),
			['net del interface peerlink.4094 clag priority']
		)
	def test_set_clag_shared_mac(self):
		self.assertEqual(
			self.plugin.set_clag_shared_mac('ff:ff:ff:ff:ff:ff', execute=False),
			['net add interface peerlink.4094 clag sys-mac ff:ff:ff:ff:ff:ff']
		)
		self.assertEqual(
			self.plugin.set_clag_shared_mac(None, delete=True, execute=False),
			['net del interface peerlink.4094 clag sys-mac']
		)

	def test_set_bond_clag_id(self):
		self.assertEqual(
			self.plugin.set_bond_clag_id('1G', 1, 3, execute=False),
			['net add bond 1 clag id 3']
		)
		self.assertEqual(
			self.plugin.set_bond_clag_id('1G', 1, None, delete=True, execute=False),
			['net del bond 1 clag id']
		)

if __name__ == '__main__':
	unittest.main()