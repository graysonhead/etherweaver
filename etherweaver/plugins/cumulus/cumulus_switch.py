from etherweaver.plugins.plugin_class import NetWeaverPlugin, NWConnType
from ipaddress import ip_address, IPv4Address, IPv6Address
import pytz
import json
from etherweaver.core_classes.utils import \
	extrapolate_list, \
	compact_list, \
	multi_port_parse
from etherweaver.core_classes.datatypes import WeaverConfig
from etherweaver.core_classes.errors import ConfigKeyError

class CumulusSwitch(NetWeaverPlugin):

	def __init__(self, cstate):
		self.is_plugin = True
		self.portmap = None
		self.cstate = cstate
		self.commands = []

	def after_connect(self):
		self.portmap = self.pull_port_state()
		self.cstate = self.pull_state()

	def command(self, command):
		"""
		This just wraps _ssh_command right now, eventually it will allow for other comm types
		:param command:
		:return:
		"""
		if self.protocol == 2:
			return self._ssh_command(command)

	def commit(self):
		ret = self.command('net commit')
		self.cstate = self.pull_state()
		return ret

	def multi_port_parse(self, prt):
		# Populate this list with the complete list of interface names
		int_names = []
		# We may have an abbreviation like this 'po1-3,pol2-4'
		if ',' in prt:
			ports_list = prt.split(',')
		else:
			ports_list = [prt]
		# Split it into ['pol1-3', 'pol2-4']
		for ports in ports_list:
			prt_name = None
			# Take 'po1-3' and turn it into [ 'po1', 'po2', 'po3' ]
			prt_name = ports.strip('1234567890-')
			compact_list = ports.strip(prt_name)
			prt_list = extrapolate_list([compact_list])
			# This is for some really ugly edge-cases like 'po1-3,6,pol4' where a number can appear without an ID
			# It seems safe to assume that the last ID can be used in all cases
			for pn in prt_list:
				if prt_name is None or prt_name == '':
					if last_name is not None:
						# prt_list[prt_list.index(pn)] = last_name + pn
						int_names.append(last_name + pn)
					else:
						raise ValueError(
							"The name of the port could not be determined, this is probably due to a malformed"
							" name string")
				else:
					int_names.append(prt_name + pn)
			if bool(prt_name) is True:
				last_name = prt_name
		return int_names

	def pull_state(self):
		pre_parse_commands = self.command('net show configuration commands').split('\n')
		# This dict is constructed following the yaml structure for a role starting at the hostname level
		# Watch the pluralization in here, a lot of the things are unplural in cumulus that are plural in weaver
		conf = WeaverConfig.gen_config_skel()
		# We have to do some pre-parsing here to expand interface ranges and such
		commands = []

		def pre_parse():
			for line in pre_parse_commands:
				# This handles lines like: net add interface swp3,5 bridge vids 2-5
				if line.startswith('net add interface') and ',' in line.split(' ')[3]\
						or line.startswith('net add interface') and '-' in line.split(' ')[3]:
					components = line.split(' ')
					int_iter = self.multi_port_parse(components[3])
					# int_iter = line.split(' ')[3].strip('swp').split(',')
					# int_iter = extrapolate_list(int_iter, int_out=False)
					for interface in int_iter:
						newline = []
						for comp in components[0:3]:
							newline.append(comp)
						newline.append(interface)
						for comp in components[4:]:
							newline.append(comp)
						commands.append(' '.join(newline))
				# Same thing but for bonds
				# TODO: This and the above could probably be a function
				elif line.startswith('net add bond') and ',' in line.split(' ')[3]\
						or line.startswith('net add bond') and '-' in line.split(' ')[3]:
					components = line.split(' ')
					int_iter = self.multi_port_parse(components[3])
					for interface in int_iter:
						newline = []
						for comp in components[0:3]:
							newline.append(comp)
						newline.append(interface)
						for comp in components[4:]:
							newline.append(comp)
						commands.append(' '.join(newline))
				else:
					commands.append(line)


		def parse_interfaces(line):
			portid = line.split(' ')[3]
			# lookup port
			portnum = self.portmap['by_name'][portid]['portid']
			if self.portmap['by_name'][portid]['mode'] == 'Mgmt':
				speed = 'mgmt'
			else:
				speed = self.portmap['by_name'][portid]['speed']
			# Bootstrap the interface if it doesn't exist
			# TODO the datatypes class needs to do this
			if speed in ['1G', '10G', '100G']:
				if portnum not in conf['interfaces'][speed]:
					conf['interfaces'][speed].update({portnum: WeaverConfig.gen_portskel()})
				# Parse bridge options
				if line.startswith('net add interface {} bridge vids'.format(portid)):
					vids = line.split(' ')[6].split(',')
					conf['interfaces'][speed][portnum]['tagged_vlans'] = extrapolate_list(vids, int_out=True)
				elif line.startswith('net add interface {} bridge pvid'.format(portid)):
					conf['interfaces'][speed][portnum]['untagged_vlan'] = line.split(' ')[6]
				# Parse STP options
				elif line.startswith('net add interface {} stp portadminedge'.format(portid)):
					conf['interfaces'][speed][portnum]['stp']['port_fast'] = True

		def clag_parse(line):
			# Parses clag statements
			# parse backup-ip
			if line.startswith('net add interface peerlink.4094 clag backup-ip'):
				conf['clag']['backup_ip'] = line.split(' ')[6]
				# parse peer ip
			elif line.startswith('net add interface peerlink.4094 clag peer-ip'):
				conf['clag']['peer_ip'] = line.split(' ')[6]
			# parse priority
			elif line.startswith('net add interface peerlink.4094 clag priority'):
				conf['clag']['priority'] = int(line.split(' ')[6])
			# parse sys-mac
			elif line.startswith('net add interface peerlink.4094 clag sys-mac'):
				conf['clag']['shared_mac'] = line.split(' ')[6]
			# parse ip address
			elif line.startswith('net add interface peerlink.4094 ip address'):
				conf['clag']['clag_cidr'] = line.split(' ')[6]

		def create_bond_inter(name, slaves):
			# Create the bond node
			conf['interfaces']['bond'].update({name: {}})
			for interface in slaves:
				# Get the speed of the interface
				speed = self.portmap['by_name']['swp{}'.format(str(interface))]['speed']
				# Create or update the interface
				if interface not in conf['interfaces'][speed]:
					conf['interfaces'][speed].update({interface: WeaverConfig.gen_portskel()})
				conf['interfaces'][speed][interface].update({'bond_slave': name})

		def bond_parse(line):
			# This should be the first reference of any bond
			if 'slaves' in line:
				name = line.split(' ')[3]
				# Parse the interfaces and extrapolate them
				interfaces = extrapolate_list(line.split(' ')[6].replace("swp", '').split(','), int_out=True)
				# Create the bond and references to slave interfaces
				create_bond_inter(name, interfaces)
			if 'clag id' in line:
				# Get the name and ID of the interface
				name = line.split(' ')[3]
				clag_id = line.split(' ')[6]
				conf['interfaces']['bond'][name]['clag_id'] = int(clag_id)
			if 'bridge vids' in line:
				name = line.split(' ')[3]
				vids = line.split(' ')[6].split(',')
				conf['interfaces']['bond'][name]['tagged_vlans'] = extrapolate_list(vids, int_out=True)
			if 'bridge pvid' in line:
				name = line.split(' ')[3]
				vid = line.split(' ')[6]
				conf['interfaces']['bond'][name]['untagged_vlan'] = int(vid)



		pre_parse()
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
					conf['vlans'].update({int(vid): None})
			# Interfaces
			elif line.startswith('net add interface') and not line.startswith('net add interface peerlink.4094'):
				parse_interfaces(line)
			# CLAG
			elif line.startswith('net add interface peerlink.4094'):
				clag_parse(line)
			# bond parsing
			elif line.startswith('net add bond'):
				bond_parse(line)

		wc = WeaverConfig(conf)
		return wc.get_full_config()

	def _check_atrib(self, atrib):
		try:
			atrib
		except KeyError:
			return False
			pass
		else:
			if atrib:
				return True

	# def add_dns_nameserver(self, ip, commit=True, execute=True):
	# 	ip = ip_address(ip)
	# 	if ip._version == 4:
	# 		version = 'ipv4'
	# 	elif ip._version == 6:
	# 		version = 'ipv6'
	# 	command = 'net add dns nameserver {} {}'.format(version, ip)
	# 	if execute:
	# 		self.command(command)
	# 		if commit:
	# 			self.commit()
	# 	return command

	def set_dns_nameservers(self, nameserverlist, execute=True, commit=True, delete=False, add=False):
		commands = []
		nameservers_to_delete = []
		nameservers_to_add = []
		cstate = self.appliance.cstate['protocols']['dns']['nameservers']
		if add:
			nameservers_to_add = list(filter(lambda srv: srv not in cstate, nameserverlist))
		elif delete:
			if nameserverlist:
				nameservers_to_delete = list(filter(lambda srv: srv in cstate, nameserverlist))
			else:
				nameservers_to_delete = cstate
		else:
			nameservers_to_add = list(filter(lambda srv: srv not in cstate, nameserverlist))
			nameservers_to_delete = list(filter(lambda srv: srv not in nameserverlist, cstate))

		for server in nameservers_to_add:
			ip = ip_address(server)
			if ip._version == 4:
				version = 'ipv4'
			elif ip._version == 6:
				version = 'ipv6'
			commands.append('net add dns nameserver {} {}'.format(version, server))
		for server in nameservers_to_delete:
			ip = ip_address(server)
			if ip._version == 4:
				version = 'ipv4'
			elif ip._version == 6:
				version = 'ipv6'
			commands.append('net del dns nameserver {} {}'.format(version, server))
		if execute:
			for com in commands:
				self.command(com)
			if commit:
				self.commit()
		return commands

	# def rm_dns_nameserver(self, ip, commit=True, execute=True):
	# 	ip = ip_address(ip)
	# 	if ip._version == 4:
	# 		version = 'ipv4'
	# 	elif ip._version == 6:
	# 		version = 'ipv6'
	# 	command = 'net del dns nameserver {} {}'.format(version, ip)
	# 	if execute:
	# 		self.command(command)
	# 		if commit:
	# 			self.commit()
	# 	return command

	def set_hostname(self, hostname, execute=True, commit=True, delete=False):
		if delete:
			command = 'net del hostname'
		else:
			command = 'net add hostname {}'.format(hostname)
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return [command]

	def set_ntp_client_timezone(self, timezone, execute=True, delete=True, commit=True):
		if timezone in pytz.all_timezones:
			command = 'net add time zone {}'.format(timezone)
		else:
			raise ValueError("Invalid timezone string")
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return command

	def set_ntp_client_servers(self, ntpserverlist, execute=True, commit=True, delete=False):
		ntp_servers_to_add = []
		ntp_servers_to_delete = []
		commands = []
		cstate = self.appliance.cstate['protocols']['ntp']['client']['servers']
		if delete:
			if ntpserverlist:
				ntp_servers_to_delete = list(filter(lambda srv: srv in cstate, ntpserverlist))
			else:
				ntp_servers_to_delete = cstate
		else:
			for server in ntpserverlist:
				# Add servers that exist already
				if server not in cstate:
					ntp_servers_to_add.append(server)
			for server in cstate:
				if server not in ntpserverlist:
					ntp_servers_to_delete.append(server)
		for server in ntp_servers_to_delete:
			commands.append('net del time ntp server {}'.format(server))
		for server in ntp_servers_to_add:
			commands.append('net add time ntp server {} iburst'.format(server))
		if execute:
			for com in commands:
				self.command(com)
			if commit:
				self.commit()
		return commands

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
				try:
					portnum = int(k.strip('eth'))
				except ValueError:
					portnum = k.strip('eth')
			else:
				portname = k
				try:
					portnum = int(k.strip('swp'))
				except ValueError:
					portnum = k.strip('swp')
			if v['speed'] == 'N/A':
				ports_by_name.update({portname: {'portid': portnum, 'speed': '1G', 'mode': v['mode']}})
			else:
				ports_by_name.update({portname: {'portid': portnum, 'speed': v['speed'], 'mode': v['mode']}})
			ports_by_number.update({portnum: {'portname': portname, 'speed': v['speed'], 'mode': v['mode']}})
		return {'by_name': ports_by_name, 'by_number': ports_by_number}

	def set_vlans(self, vlandictlist, execute=True, commit=True, delete=False):
		commands = []
		vlans_to_add = []
		vlans_to_remove = []
		if delete:
			if vlandictlist:
				for k, v in vlandictlist.items():
					if k in self.appliance.cstate['vlans']:
						vlans_to_remove.append(k)
			else:
				for k, v in self.appliance.cstate['vlans'].items():
					vlans_to_remove.append(k)
		else:
			for k, v in vlandictlist.items():
				# Comparing vlan keys and values to existing ones in cstate
				if k not in self.appliance.cstate['vlans']:
					vlans_to_add.append(k)
			for k, v in self.appliance.cstate['vlans'].items():
				if k not in vlandictlist:
					vlans_to_remove.append(k)
		if vlans_to_add:
			commands.append('net add bridge bridge vids {}'.format(
				','.join(str(x) for x in compact_list(vlans_to_add))
			))
		if vlans_to_remove:
			commands.append('net del bridge bridge vids {}'.format(
				','.join(str(x) for x in compact_list(vlans_to_remove))
			))
		if execute:
			for com in commands:
				self.command(com)
			if commit:
				self.commit()
		return commands

	def _dict_input_handler(self, stringordict):
		if type(stringordict) is str:
			dic = json.loads(stringordict)
		elif type(stringordict) is dict:
			dic = stringordict
		return dic

	# def set_interface_tagged_vlans(self, interface, vlans, execute=True, commit=True):
	# 	commands = []
	# 	vids_to_add = ','.join(str(x) for x in vlans)
	# 	interface = self._number_port_mapper(interface)
	# 	commands.append('net del interface {} bridge vids'.format(interface))
	# 	commands.append('net add interface {} bridge vids {}'.format(interface, vids_to_add))
	# 	if execute:
	# 		for com in commands:
	# 			self.command(com)
	# 		if commit:
	# 			self.commit()
	# 	return commands

	def set_interface_tagged_vlans(self, speed, interface, vlans, execute=True, commit=True, delete=False, add=False):
		if speed != 'bond':
			cumulus_interface = self._number_port_mapper(interface)
		else:
			cumulus_interface = interface
		commands = []
		vlans_to_add = []
		vlans_to_remove = []
		# If the delete value is set, we are adding vlans from the 'vlans' param into the delete set instead of adding
		# If delete and the value is set, we are deleting a list of vlans
		if add and vlans:
			for v in vlans:
				if v not in self.appliance.cstate['interfaces'][speed][interface]['tagged_vlans']:
					vlans_to_add.append(v)
		elif delete and vlans:
			for v in vlans:
				# Delete the vlans in the list
				if v in self.appliance.cstate['interfaces'][speed][interface]['tagged_vlans']:
					vlans_to_remove.append(v)
		elif delete and not vlans:
			# Delete all of them
			for v in self.appliance.cstate['interfaces'][speed][interface]['tagged_vlans']:
				vlans_to_remove.append(v)
		else:
			# Add vlans not in cstate from dstate
			if interface in self.appliance.cstate['interfaces'][speed]:
				for v in vlans:
					if v not in self.appliance.cstate['interfaces'][speed][interface]['tagged_vlans']:
						vlans_to_add.append(v)
				# Remove vlans not in dstate from cstate
				for v in self.appliance.cstate['interfaces'][speed][interface]['tagged_vlans']:
					if v not in vlans:
						vlans_to_remove.append(v)
			else:
				vlans_to_add = vlans
		if speed == 'bond':
			interface_type_name = 'bond'
		else:
			interface_type_name = 'interface'
		if vlans_to_remove:
			commands.append('net del {} {} bridge vids {}'.format(
				interface_type_name,
				cumulus_interface,
				','.join(str(x) for x in compact_list(list(vlans_to_remove)))
				)
			)
		if vlans_to_add:
			commands.append('net add {} {} bridge vids {}'.format(
				interface_type_name,
				cumulus_interface,
				','.join(str(x) for x in compact_list(list(vlans_to_add)))
				)
			)
		if execute:
			for com in commands:
				self.command(com)
			if commit:
				self.commit()
		return commands


	def set_portfast(self, speed, interface, enable_bool, execute=True, commit=True):
		if enable_bool:
			command = 'net add interface {} stp portadminedge'.format(self._number_port_mapper(interface))
		else:
			command = 'net del interface {} stp portadminedge'.format(self._number_port_mapper(interface))
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return command

	def _name_port_mapper(self, port):
		return self.portmap['by_name'][str(port)]['portid']

	def _number_port_mapper(self, port):
		try:
			return self.portmap['by_number'][port]['portname']
		except KeyError:
			raise ValueError("Referenced non-existent interface {} on appliance {}".format(port, self.appliance.name))

	def set_interface_untagged_vlan(self, type, interface, vlan, execute=True, delete=False, commit=True):
		if type == 'bond':
			if delete:
				command = 'net del bond {} bridge pvid'.format(interface)
			else:
				command = 'net add bond {} bridge pvid {}'.format(interface, vlan)
		else:
			if delete:
				command = 'net del interface {} bridge pvid'.format(self._number_port_mapper(interface))
			else:
				command = 'net add interface {} bridge pvid {}'.format(self._number_port_mapper(interface), vlan)
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return [command]

	# def rm_interface_untagged_vlan(self, interface, execute=True, delete=False):
	# 	command = 'net del interface {} bridge pvid'.format(self._number_port_mapper(interface))
	# 	if execute:
	# 		self.command(command)
	# 	return command

	def set_clag_backup_ip(self, backup_ip, execute=True, delete=False, commit=True):
		if delete:
			command = 'net del interface peerlink.4094 clag backup-ip'
		else:
			command = 'net add interface peerlink.4094 clag backup-ip {}'.format(backup_ip)
		if execute:
			self.command(command)
		return [command]


	# TODO: both of the below methods need their functionality rolled up into a generic ip addr setter

	def set_clag_cidr(self, cidr, execute=True, delete=False, commit=True):
		commands = []
		if delete:
			commands.append('net del interface peerlink.4094 ip address')
		else:
			commands.append('net add interface peerlink.4094 ip address {}'.format(cidr))
		if execute:
			for com in commands:
				self.command(com)
				if commit:
					self.commit()
		return commands

	def set_clag_peer_ip(self, peer_ip, execute=True, delete=False, commit=True):
		commands = []
		if delete:
			commands.append('net del interface peerlink.4094 clag peer-ip')
		else:
			commands.append('net add interface peerlink.4094 clag peer-ip {}'.format(peer_ip))
		if execute:
			for com in commands:
				self.command(com)
				if commit:
					self.commit()
		return commands

	def set_clag_priority(self, priority, execute=True, delete=False, commit=True):
		if delete:
			command = 'net del interface peerlink.4094 clag priority'
		else:
			command = 'net add interface peerlink.4094 clag priority {}'.format(priority)
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return [command]

	def set_clag_shared_mac(self, shared_mac, execute=True, delete=False, commit=True):
		if delete is True:
			command = 'net del interface peerlink.4094 clag sys-mac'
		else:
			command = 'net add interface peerlink.4094 clag sys-mac {}'.format(shared_mac)
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return [command]

	def set_bond_slaves(self, int_type, interface, bond, execute=True, commit=True):
		# TODO: allow deletion of bonds
		# Find interfaces belonging to this bond, since cumulus defines interfces on the bond
		# bond_slaves = []
		# for ktyp, vtyp in self.appliance.cstate['interfaces'].items():
		# 	if ktyp in ['10G', '1G', '40G', '100G']:
		# 		for kint, vint in vtyp.items():
		# 			if vint['bond'] == interface:
		# 				bond_slaves.append(self._number_port_mapper(kint))
		command = 'net add bond {} bond slaves {}'.format(bond, self._number_port_mapper(interface))
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return [command]

	def set_bond_clag_id(self, int_type, interface, clag_id, execute=True, delete=False, commit=True):
		if delete:
			command = 'net del bond {} clag id'.format(interface)
		else:
			command = 'net add bond {} clag id {}'.format(interface, clag_id)
		if execute:
			self.command(command)
			if commit:
				self.commit()
		return [command]

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.ssh:
			self.ssh.close()
