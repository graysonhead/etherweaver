from netweaver.plugins.plugin_class import NetWeaverPlugin, NWConnType
from functools import wraps
import logging
from ipaddress import ip_address, IPv4Address, IPv6Address
import pytz
import json
from netweaver.core_classes.utils import extrapolate_list, extrapolate_dict, compare_dict_keys


class CumulusSwitch(NetWeaverPlugin):

	def __init__(self, appconfig, fabricconfig):
		self.is_plugin = True
		self.fabricconfig = fabricconfig
		self.hostname = appconfig['hostname']
		self.username = fabricconfig['credentials']['username']
		self.password = fabricconfig['credentials']['password']
		self.port = 22

		self.portmap = None
		self.cstate = None

		self.commands = []

		"""
		State cases referenced in below modules:
		cstate = Current State (stored in plugin)
		dstate = Desired state (stored in appliance)
		
		Case0: exists in cstate but not dstate (ignore)
		Case1: exists in dstate but not cstate (create dstate)
		Case2: exists in both, but values do not match (apply dstate)
		Case3 exists in both, and both match (do nothing)
		"""
	def connect(self):
		self.build_ssh_session()
		self.portmap = self.pull_port_state()
		self.cstate = self.pull_state()

	def build_ssh_session(self):
		self.conn_type = NWConnType
		self.ssh = self._build_ssh_client(
			hostname=self.hostname,
			username=self.username,
			password=self.password,
			port=self.port
		)

	def get_current_config(self):
		"""
		Get_current_config should return a Dict containing the current state of an object.
		This structure should match the structure of a standard 'role' object.
		"""
		config = {}
		config.update({'hostname': self.get_hostname()})
		return config

	def command(self, command):
		"""
		This just wraps _ssh_command right now, eventually it will allow for other comm types
		:param command:
		:return:
		"""
		if self.ssh:
			return self._ssh_command(command)

	def _net_commit(self):
		ret = self.command('net commit')
		self.cstate = self.pull_state()
		return ret

	def net_config_parser(self):
		pass

	def get_dns_nameservers(self):
		return self.cstate['protocols']['dns']['nameservers']

	def pull_state(self):
		pre_parse_commands = self.command('net show configuration commands').split('\n')
		# This dict is constructed following the yaml structure for a role starting at the hostname level
		# Watch the pluralization in here, a lot of the things are unplural in cumulus that are plural in weaver
		conf = {
			'hostname': None,
			'vlans': {},
			'protocols': {
				'dns': {
					'nameservers': []
				},
				'ntp': {
					'client': {
						'servers': []
					}
				}
			},
			'interfaces': {
				'1G': {},
				'10G': {},
				'40G': {},
				'100G': {},
				'mgmt': {}
			}
		}
		# We have to do some pre-parsing here to expand interface ranges and such
		commands = []
		for line in pre_parse_commands:
			# This handles lines like: net add interface swp3,5 bridge vids 2-5
			if line.startswith('net add interface') and ',' in line.split(' ')[3]\
					or line.startswith('net add interface') and '-' in line.split(' ')[3]:
				components = line.split(' ')
				int_iter = line.split(' ')[3].strip('swp').split(',')
				int_iter = extrapolate_list(int_iter, int_out=False)
				for interface in int_iter:
					newline = []
					for comp in components[0:3]:
						newline.append(comp)
					newline.append('swp' + interface)
					for comp in components[4:]:
						newline.append(comp)
					commands.append(' '.join(newline))
			else:
				commands.append(line)


		for line in commands:
			# Nameservers
			if line.startswith('net add dns nameserver'):
				ln = line.split(' ')
				conf['protocols']['dns']['nameservers'].append(ln[5])
			# Hostname
			elif line.startswith('net add hostname'):
				ln = line.split(' ')
				conf.update({'hostname': ln[3]})
			# NTP - client
			elif line.startswith('net add time'):
				# TZ
				if line.startswith('net add time zone'):
					conf['protocols']['ntp']['client'].update({'timezone': line.split(' ')[4]})
				# Timeservers
				elif line.startswith('net add time ntp server'):
					if 'servers' not in conf['protocols']['ntp']['client']:
						conf['protocols']['ntp']['client'].update({'servers': []})
					conf['protocols']['ntp']['client']['servers'].append(line.split(' ')[5])
			#VLANs
			elif line.startswith('net add bridge bridge vids'):
				vidstring = line.split(' ')[5]
				vids = extrapolate_list(vidstring.split(','))
				for vid in vids:
					conf['vlans'].update({vid: None})
			# Interfaces
			elif line.startswith('net add interface'):
				portid = line.split(' ')[3]
				# lookup port
				portnum = self.portmap['by_name'][portid]['portid']
				if self.portmap['by_name'][portid]['mode'] == 'Mgmt':
					speed = 'mgmt'
				else:
					speed = self.portmap['by_name'][portid]['speed']
					# Bootstrap the interface if it doesn't exist
				if portnum not in conf['interfaces'][speed]:
					conf['interfaces'][speed].update({portnum: self._gen_portskel()})
				# Parse bridge options
				if line.startswith('net add interface {} bridge vids'.format(portid)):
					vids = line.split(' ')[6].split(',')
					conf['interfaces'][speed][portnum]['tagged_vlans'] = extrapolate_list(vids, int_out=True)
				if line.startswith('net add interface {} bridge pvid'.format(portid)):
					conf['interfaces'][speed][portnum]['untagged_vlan'] = line.split(' ')[6]
		return conf

	def _check_atrib(self, atrib):
		try:
			atrib
		except KeyError:
			return False
			pass
		else:
			if atrib:
				return True

	def reload_state(self):
		self.cstate = self.pull_state()
		self.portmap = self.pull_port_state()

	def push_state(self, execute=True):
			queue = []
			dstate = self.appliance.dstate
			cstate = self.cstate
			self._add_command(self._hostname_push(dstate, cstate))
			self._add_command(self._protocol_dns_nameservers_push(dstate, cstate))
			self._add_command(self._protocol_ntpclient_timezone_push(dstate, cstate))
			self._add_command(self._protocol_ntpclient_servers(dstate, cstate))
			self._add_command(self._vlans_push(dstate, cstate))
			self._add_command(self._interfaces_push(dstate, cstate))

			# 	# Interfaces
			# 	# Iterate through dstate interface types
			# 	for typekey, typeval in dstate['interfaces'].items():
			# 		# Iterate through interfaces in each type
			# 		for portnum, portconf in typeval.items():
			# 			# If the portnumber exists in cstate:
			# 			if portnum in self.cstate['interfaces'][typekey]:
			# 				#Compare the desired state to the current state of any defined interfaces
			# 				current_portstate = self.cstate['interfaces'][typekey][portnum]
			#
			# 				if extrapolate_list(portconf['tagged_vlans'], int_out=True) != extrapolate_list(current_portstate['tagged_vlans'], int_out=True):
			# 						queue = queue + self\
			# 							.set_interface_tagged_vlans(self._number_port_mapper(portnum), extrapolate_list(portconf['tagged_vlans'], int_out=False), execute=False)
			# 				if portnum not in self.cstate['interfaces'][typekey]:
			# 					if portconf['tagged_vlans']:
			# 						self.set_interface_tagged_vlans(self._number_port_mapper(portnum), extrapolate_list(portconf['tagged_vlans']), int_out=False, execute=False)
			# 				if 'untagged_vlan' in portconf:
			# 					if str(portconf['untagged_vlan']) != str(current_portstate['untagged_vlan']):
			# 						queue.append(self.set_interface_untagged_vlan(self._number_port_mapper(portnum), portconf['untagged_vlan'], execute=False))
			#
			# 			# If the port doesn't exist in cstate
			# 			else:
			# 				if portconf['tagged_vlans']:
			# 					queue = queue + self.set_interface_tagged_vlans(self._number_port_mapper(portnum), extrapolate_list(portconf['tagged_vlans'], int_out=False), execute=False)
			# 						#TODO: Fix portmap to contain all interfaces (even downed ones). Finish interface creation logic
			for com in self.commands:
				self.command(com)
			self._net_commit()
			self.reload_state()
			return self.commands

	def add_dns_nameserver(self, ip, commit=True, execute=True):
		ip = ip_address(ip)
		if ip._version == 4:
			version = 'ipv4'
		elif ip._version == 6:
			version = 'ipv6'
		command = 'net add dns nameserver {} {}'.format(version, ip)
		if execute:
			self.command(command)
			if commit:
				self._net_commit()
		return command

	def get_dns(self):
		return self.cstate['protocols']['dns']

	def set_dns_nameservers(self, nameserverlist, execute=True, commit=True):
		commandqueue = []
		try:
			nslist = self.cstate['protocols']['dns']['nameservers']
		except KeyError:
			pass
		else:
			for ns in nslist:
				if ns not in nameserverlist:
					commandqueue.append(self.rm_dns_nameserver(ns, execute=False))
		for ns in nameserverlist:
				if ns not in self.cstate['protocols']['dns']['nameservers']:
					commandqueue.append(self.add_dns_nameserver(ns, commit=False, execute=False))
		if execute:
			for com in commandqueue:
				self.command(com)
			if commit:
				self._net_commit()
		return commandqueue

	def rm_dns_nameserver(self, ip, commit=True, execute=True):
		ip = ip_address(ip)
		if ip._version == 4:
			version = 'ipv4'
		elif ip._version == 6:
			version = 'ipv6'
		command = 'net del dns nameserver {} {}'.format(version, ip)
		if execute:
			self.command(command)
			if commit:
				self._net_commit()
		return command

	def get_hostname(self):
		return self.command('hostname').strip('\n')

	def set_hostname(self, hostname, execute=True, commit=True):
		command = 'net add hostname {}'.format(hostname)
		if execute:
			self.command(command)
			if commit:
				self._net_commit()
		return command

	def set_ntp_client_timezone(self, timezone, execute=True):
		if timezone in pytz.all_timezones:
			command = 'net add time zone {}'.format(timezone)
		else:
			raise ValueError("Invalid timezone string")
		if execute:
			self.command(command)
			self._net_commit()
		return command

	def add_ntp_client_server(self, ntpserver, execute=True):
		command = 'net add time ntp server {} iburst'.format(ntpserver)
		if execute:
			self.command(command)
			self._net_commit()
		return command

	def rm_ntp_client_server(self, ntpserver, execute=True):
		command = 'net del time ntp server {}'.format(ntpserver)
		if execute:
			self.command(command)
			self._net_commit()
		return command

	def set_ntp_client_servers(self, ntpserverlist, execute=True, commit=True):
		commandqueue = []
		try:
			slist = self.cstate['protocols']['ntp']['client']['servers']
		except KeyError:
			pass
		else:
			for serv in slist:
				if serv not in ntpserverlist:
					commandqueue.append(self.rm_ntp_client_server(serv, execute=False))
		for serv in ntpserverlist:
			if serv not in self.cstate['protocols']['ntp']['client']['servers']:
				commandqueue.append(self.add_ntp_client_server(serv, execute=False))
		if execute:
			for com in commandqueue:
				self.command(com)
			if commit:
				self._net_commit()
		return commandqueue

	def _get_interface_json(self):
		return json.loads(self.command('net show interface all json'))

	def pull_port_state(self):
		ports_by_name = {}
		ports_by_number = {}
		"""
		Ports will look like:
		{ swp1: { speed: 1G, mode: Mgmt}
		"""
		prtjson = self._get_interface_json()
		for k, v in prtjson.items():
			if v['mode'] == 'Mgmt':
				portname = k
				portnum = k.strip('eth')
			else:
				portname = k
				portnum = k.strip('swp')
			ports_by_name.update({portname: {'portid': portnum, 'speed': v['speed'], 'mode': v['mode']}})
			ports_by_number.update({portnum: {'portname': portname, 'speed': v['speed'], 'mode': v['mode']}})
		return {'by_name': ports_by_name, 'by_number': ports_by_number}



	def set_interface_config(self, interfaces, profile=None, execute=True):
		pass

	def add_vlan(self, vlan, execute=True, commit=True):
		"""
		Config objects like {1: {'description': 'Data'}}
		:param vlans:
		:param execute:
		:return:
		"""
		command = 'net add bridge bridge vids {}'.format(vlan)
		if execute:
			self.command(command)
			if commit:
				self._net_commit()
		return command

	def rm_vlan(self, vid, execute=True, commit=True):
		command = 'net del bridge bridge vids {}'.format(vid)
		if execute:
			self.command(command)
			if commit:
				self._net_commit()
		return command

	def set_vlans(self, vlandictlist, execute=True, commit=True):
		cvl = self.cstate['vlans']
		commandqueue = []
		for k, v in vlandictlist.items():
			if k not in cvl:
				commandqueue.append(self.add_vlan(k, execute=False))
		for k, v in cvl.items():
			if k not in vlandictlist:
				commandqueue.append(self.rm_vlan(k, execute=False))
		return commandqueue


	def _dict_input_handler(self, stringordict):
		if type(stringordict) is str:
			dic = json.loads(stringordict)
		elif type(stringordict) is dict:
			dic = stringordict
		return dic

	def _gen_portskel(self):
		return {
			'tagged_vlans': [],
			'untagged_vlan': None,
			'ip': {
				'address': []
			}

		}

	def set_interface_tagged_vlans(self, interface, vlans, execute=True, commit=True):
		commands = []
		vids_to_add = ','.join(vlans)
		commands.append('net del interface {} bridge vids'.format(interface))
		commands.append('net add interface {} bridge vids {}'.format(interface, vids_to_add))
		if execute:
			for com in commands:
				self.command(com)
			if commit:
				self._net_commit()
		return commands

	def _name_port_mapper(self, port):
		return self.portmap['by_name'][str(port)]['portid']

	def _number_port_mapper(self, port):
		return self.portmap['by_number'][str(port)]['portname']

	def set_interface_untagged_vlan(self, interface, vlan, execute=True):
		command = 'net add interface {} bridge pvid {}'.format(interface, vlan)
		if execute:
			self.command(command)
		return command

	def rm_interface_untagged_vlan(self, interface, execute=True):
		command = 'net del interface {} bridge pvid'.format(interface)
		if execute:
			self.command(command)
		return command

	def _protocol_ntpclient_timezone_push(self, dstate, cstate):
		dstate = dstate['protocols']['ntp']['client']['timezone']
		cstate = cstate['protocols']['ntp']['client']['timezone']
		# Case0
		try:
			dstate
		except KeyError:
			return
		# Case1
		if dstate == cstate:
			return
		# Case 2 and 3
		if dstate != cstate:
			return self.set_ntp_client_timezone(dstate, execute=False)

	def _protocol_dns_nameservers_push(self, dstate, cstate):
		dstate = dstate['protocols']['dns']['nameservers']
		cstate = cstate['protocols']['dns']['nameservers']
		return self._compare_state(dstate, cstate, self.set_dns_nameservers)

	def _compare_state(self, dstate, cstate, func):
		# Case0
		try:
			dstate
		except KeyError:
			return
		# Case1
		if dstate == cstate:
			return
		# Case2 and 3 create
		elif dstate != cstate:
			return func(dstate, execute=False)

	def _protocol_ntpclient_servers(self, dstate, cstate):
		dstate = dstate['protocols']['ntp']['client']['servers']
		cstate = cstate['protocols']['ntp']['client']['servers']
		return self._compare_state(dstate, cstate, self.set_ntp_client_servers)

	def _hostname_push(self, dstate, cstate):
		dstate = dstate['hostname']
		cstate = cstate['hostname']
		return self._compare_state(dstate, cstate, self.set_hostname)

	def _vlans_push(self, dstate, cstate):
		dstate = dstate['vlans']
		cstate = cstate['vlans']
		return self._compare_state(dstate, cstate, self.set_vlans)

	def _interfaces_push(self, dstate, cstate):
		i_dstate = dstate['interfaces']
		i_cstate = cstate['interfaces']
		blankstate = self._gen_portskel()
		for kspd, vspd in i_dstate.items():
			for kint, vint in vspd.items():
				if 'tagged_vlan' in vint:
					self._interface_tagged_vlans_push(cstate, dstate, kspd, kint)
				if 'untagged_vlan' in vint:
					self._interface_untagged_vlan_push(cstate, dstate, kspd, kint)

	def _interface_untagged_vlan_push(self, cstate, dstate, speed, interface):
		dstate = str(dstate['interfaces'][speed][interface]['untagged_vlan'])
		# Case 3
		try:
			cstate = str(cstate['interfaces'][speed][str(interface)]['untagged_vlan'])
		except KeyError:
			self._add_command(self.set_interface_untagged_vlan(self._number_port_mapper(interface), dstate, execute=False))
		# Case0
		try:
			dstate
		except KeyError:
			return
		# Case1
		if dstate == cstate:
			return
		# Case 2
		elif dstate != cstate:
			self._add_command(
				self.set_interface_untagged_vlan(self._number_port_mapper(interface), dstate, execute=False))


	def _interface_tagged_vlans_push(self, cstate, dstate, speed, interface):
		# Case 3
		dstate = extrapolate_list(dstate['interfaces'][speed][interface]['tagged_vlans'], int_out=False)
		try:
			cstate = extrapolate_list(cstate['interfaces'][speed][str(interface)]['tagged_vlans'], int_out=False)
		except KeyError:
			self._add_command(self.set_interface_tagged_vlans(self._number_port_mapper(interface), dstate, execute=False))
		# Case0
		try:
			dstate
		except KeyError:
			return
		# Case1
		if dstate == cstate:
			return
		# Case 2
		elif dstate != cstate:
			self._add_command(self.set_interface_tagged_vlans(self._number_port_mapper(interface), dstate, execute=False))




	def _add_command(self, commands):
		if type(commands) == list:
			for com in commands:
				self.commands.append(com)
		elif commands is None:
			return
		else:
			self.commands.append(commands)

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.ssh:
			self.ssh.close()
