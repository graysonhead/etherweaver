from netweaver.plugins.plugin_class import NetWeaverPlugin, NWConnType
from functools import wraps
import logging
from ipaddress import ip_address, IPv4Address, IPv6Address
import pytz
import json
from netweaver.core_classes.utils import extrapolate_list, extrapolate_dict, compare_dict_keys


class CumulusSwitch(NetWeaverPlugin):

	def __init__(self, config, fabricconfig):
		self.is_plugin = True
		self.fabricconfig = fabricconfig
		self.hostname = config['hostname']
		self.username = fabricconfig['credentials']['username']
		self.password = fabricconfig['credentials']['password']
		self.port = 22

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
		commands = self.command('net show configuration commands').split('\n')
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
				'Mgmt': {}
			}
		}

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
			#Interfaces
			elif line.startswith('net add interface'):
				portid = line.split(' ')[3]
				# Iterate through portmap
				for k, v in self.portmap.items():
					# Iterate through port group
					for kpt, vpt in v.items():
						# If we find a matching ID in the portmap, figure out if it exists in cstate interfaces
						if vpt['id'] == portid:
							# If this is the first time we are seeing this port, create a skeleton dict for it
							if kpt not in conf['interfaces'][k]:
								conf['interfaces'][k].update({kpt: self._gen_portskel()})
							# Port VLAN configuration
							if line.startswith('net add interface {} bridge'.format(portid)):
								#PVID
								if line.startswith('net add interface {} bridge pvid'.format(portid)):
									conf['interfaces'][k][kpt]['untagged_vlan'] = line.split(' ')[6]
								#Tagged vlans
								if line.startswith('net add interface {} bridge vids'.format(portid)):
									vids = line.split(' ')[6].split(',')
									conf['interfaces'][k][kpt]['tagged_vlans'] = extrapolate_list(vids, int_out=True)
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
			dstate = self.appliance.role.config
			dpstate = self.appliance.fabric.config
			if 'hostname' in dstate:
				if dstate['hostname'] != self.cstate['hostname']:
					queue.append(self.set_hostname(dstate['hostname'], execute=False))
			if 'protocols' in dstate:
				if 'dns' in dstate['protocols']:
					if 'nameservers' in dstate['protocols']['dns']:
						if dstate['protocols']['dns']['nameservers'] != self.cstate['protocols']['dns']['nameservers']:
							queue = queue + self.set_dns_nameservers(
								dstate['protocols']['dns']['nameservers'],
								execute=False)
				if 'ntp' in dstate['protocols']:
					if 'client' in dstate['protocols']['ntp']:
						if 'timezone' in dstate['protocols']['ntp']['client']:
							if dstate['protocols']['ntp']['client']['timezone'] != self.cstate['protocols']['ntp']['client']['timezone']:
								queue.append(self.set_ntp_client_timezone(dstate['protocols']['ntp']['client']['timezone'], execute=False))
						if 'servers' in dstate['protocols']['ntp']['client']:
							if dstate['protocols']['ntp']['client']['servers'] != self.cstate['protocols']['ntp']['client']['servers']:
								queue = queue + (self.set_ntp_client_servers(dstate['protocols']['ntp']['client']['servers'], execute=False))
				if 'vlans' in dpstate:
					dvl = self.appliance.fabric.config['vlans']
					cvl = self.cstate['vlans']
					if not compare_dict_keys(dvl, cvl):
						queue = queue + self.set_vlans(dvl, execute=False)
				# Interfaces
				for typekey, typeval in dstate['interfaces'].items():
					for portnum, portconf in typeval.items():
						if portnum in self.cstate['interfaces'][typekey]:
							#Compare the desired state to the current state of any defined interfaces
							current_portstate = self.cstate['interfaces'][typekey][portnum]
							if portconf != self.cstate['interfaces'][typekey][portnum]:
								if portconf['tagged_vlans'] != current_portstate['tagged_vlans']:
									queue = queue + self\
										.set_interface_tagged_vlans(self.portmap[typekey][portnum]['id'], extrapolate_list(portconf['tagged_vlans'], int_out=False))
							if portnum not in self.cstate['interfaces'][typekey]:
								if portconf['tagged_vlans']:
									self.set_interface_tagged_vlans(self.portmap[typekey][portnum]['id'])
									#TODO: Fix portmap to contain all interfaces (even downed ones). Finish interface creation logic
			for com in queue:
				self.command(com)
			self._net_commit()
			self.reload_state()
			return queue

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
		ports = {
			'1G': {},
			'10G': {},
			'40G': {},
			'100G': {},
			'Mgmt': {}
		}
		prtjson = self._get_interface_json()
		for pt, pv in ports.items():
			for k, v in prtjson.items():
				if v['mode'] == 'Trunk/L2':
					if v['speed'] == pt:
						if 'eth' in k:
							num = int(k.strip('eth'))
						elif 'swp' in k:
							num = int(k.strip('swp'))
						ports[pt].update({num: {'id': k, 'info': v}})
				if pt == 'Mgmt' and v['mode'] == 'Mgmt':
					num = int(k.strip('eth'))
					ports['Mgmt'].update({num: {'id': k, 'info': v}})

		# for k, v in prtjson.items():
		# 	if v['mode'] == 'Mgmt':
		# 		num = k.strip('eth')
		# 		id = k
		# 		body = v
		# 		ports['mgmt'].update({num: {'id': id, 'info': body}})
		#
		# 	elif v['mode'] == '1G':
		# 		num = k.strip('swp')
		# 		ports['1g'].update({num: {'id': k, 'info': v}})

		return ports

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

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.ssh:
			self.ssh.close()
