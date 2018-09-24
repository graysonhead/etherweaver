from paramiko import SSHClient, WarningPolicy
from enum import IntEnum
from etherweaver.plugins.plugin_class_errors import *

"""
This is the best place to start if you plan on building a plugin.

If you are making commits to this file, please be extra careful to add descriptive comments.

The NetWeaverPlugin class must be inherited by any plugin. Any class marked with "PLUGIN_OVERRIDE" 
is a skeleton method intended to be implemented by a plugin.

There are a few different archetypes of each set function:

All methods must have execute and it must default to True. IF execute is true, run and apply the command immediately
Otherwise just return the line(s) needed to run the command

Set methods that set a single string value per appliance (I.E. setting NTP timezone)

These methods must accept the following arguments:

:param timezone_value:
	The string that the timezone will be set to

:param delete:
	Removes the string if True, defaults to false

Set methods that set a single list value per appliance (I.E. setting DNS server list)

:param dns_servers_value:
	List of DNS servers to add

:param delete:
	If delete is true, and value parameter is empty, remove the whole list.
	IF delete is true, and value parameter a list or dict (depending on the datatype of the function) delete the values in it
	Even if a single value is requested to be deleted, it will be marshaled into the datatype the method usually accpets (List, Dict, etc)

Set methods that operate on interfaces have additional positional paraemeters:

:param speed: 
	The speed or type of interface (I.E. 1G, 10G, bond, etc)

:interface:
	The number of the interface in dstate (you will probably need a mapper function as part of your plugin to translate this
	to the value utilized by your appliance)
	vlans


Boolean functions

Boolean functions only have a True or False, so they inherently handle deletions on their own. Their state is either 
true or false (I.E. set_portfast) 
"""


class NWConnType(IntEnum):
	Telnet = 1
	SSH = 2
	RS232 = 3


class NetWeaverPlugin:
	# Hard coded to SSH for now
	protocol = 2
	hostname = None
	commands = []

	def add_command(self, commands):
		"""
		Adds a command to the command queue
		:param commands:
		:return:
		"""
		# This function can expect to receive a single command, a list of commands,
		# or non-commands ([], None, etc). This is done to simplify upstream functions
		# In the latter case, we don't apppend it
		if commands == [] or commands == None or commands == '':
			return
		elif type(commands):
			for com in commands:
				if com is not None:
					self.commands.append(com)
		else:
			self.commands.append(commands)

	def build_ssh_session(self):
		"""
		This builds the SSH connection
		:return:
		"""
		self.conn_type = NWConnType
		self.ssh = self._build_ssh_client(
			hostname=self.appliance.dstate['connections']['ssh']['hostname'],
			username=self.appliance.dstate['connections']['ssh']['username'],
			password=self.appliance.dstate['connections']['ssh']['password'],
			port=self.appliance.dstate['connections']['ssh']['port']
		)

	def connect(self):
		"""
		Examine protocol attribute and set up connection accordingly
		:return:
		"""
		if self.protocol == 2:
			self.build_ssh_session()
			self.after_connect()

	def after_connect(self):
		"""
		PLUGIN_OVERRIDE

		Put anything here that your plugin needs to do after a self.connect is called
		:return:
		"""
		pass

	def _build_ssh_client(self, hostname=None, accept_untrusted=False, username=None, password=None, port=22):
		"""Returns a paramiko ssh client object"""
		ssh = SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(WarningPolicy)
		ssh.connect(hostname=hostname, port=port, username=username, password=password)
		return ssh

	def _ssh_command(self, command):
		"""
		Runs a command via self.ssh object
		:param command:
		:return:
		"""
		stdin, stdout, stderr = self.ssh.exec_command(command)
		if stderr.read():
			# TODO: Put useful info in here
			raise SSHCommandError("While running command {} on appliance {}, got error {} {}".format(command, self.hostname, stderr.read(), stdout.read())) #TODO For some reason this line returns empty on error when run from a child instance
		return stdout.read().decode('utf-8')

	def pull_state(self):
		self._not_supported('pull_state')

	def push_state(self, execute=True):
		self._not_supported('push_state')

	def _generic_command(self, command):
		if self.protocol == 2:
			return self._ssh_command(command)

	def _not_supported(self, feature):
		raise FeatureNotSupported(self.__repr__(), feature)

	def _not_implemented(self):
		raise FeatureNotImplemented

	def pre_push(self):
		self._not_implemented()
	"""Override these functions to enable each feature"""

	def set_interface_tagged_vlans(self, type, interface, vlans, execute=True, commit=True, delete=False, add=False):
		"""
		This method modifies the list of allowed tagged vlans for a given interface.

		:param type:
			This is the type of the interface, for instance: 'bond', '1G', '10G'. Used to determine the group of the
			interface to be modified.

		:param interface:
			This is the number of the interface, or text ID of the bond. You will likely need to translate this.

		:param vlans:
			This parameter will always contain a list of vlans to add or remove, even if there is a single value, and may be empty.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all tagged vlans from the interface.
			If delete is true and there is one or more values, remove only the specified values.

		:param add:
			If add is true and value is set, add all the tagged vlans in the list without removing any.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True

		"""
		self._not_supported('set_interface_tagged_vlans')

	def set_hostname(self, hostname, execute=True, commit=True, delete=False):
		"""
		This method sets the system hostname of the appliance

		:param hostname:
			A string containing the hostname of the system. Either a FQDN or short name, but not both (as most
			appliances don't differentiate)

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all tagged vlans from the interface.
			If delete is true and there is one or more values, remove only the specified values.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_hostname')

	def set_dns_nameservers(self, nameserverlist, execute=True, commit=True, delete=False):
		"""
		This method sets the dns resolvers used by the appliance.

		:param nameserverlist:
			A list of DNS server IPv4 or IPv6 addresses to add to the resolver list.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all tagged vlans from the interface.
			If delete is true and there is one or more values, remove only the specified values.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_dns_nameservers')

	def set_ntp_client_timezone(self, timezone, execute=True, delete=True, commit=True):
		# TODO: make this pass a pytz object instead of a pytz string?
		"""
		Sets the timezone of the NTP client.

		:param timezone:
			Contains a string containing a valid timeozne recognized by pytz

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all tagged vlans from the interface.
			If delete is true and there is one or more values, remove only the specified values.
			If you cannot delete the timezone on your appliance (I.E., one must always be specified), call the inherited
			self._not_supported(string), with string being an informative error message.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_ntp_client_timezone')

	def set_ntp_client_servers(self, ntpserverlist, execute=True, commit=True, delete=False):
		"""

		:param ntpserverlist:
			A list of ntp servers to add (IP Addresses or DNS)

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.


		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True

		"""
		self._not_supported('set_ntp_client_servers')

	def set_vlans(self, vlandictlist, execute=True, commit=True, delete=False):
		"""
		Add a dict containing vlan interfaces

		:param vlandictlist:
		:param execute:
		:param commit:
		:param delete:
		:return:
		"""
		self._not_supported('set_vlans')

	def set_interface_untagged_vlan(self, type, interface, vlan, execute=True, delete=False):
		"""
		Sets the untagged (PVID) of an interface

		:param type:
			This is the type of the interface, for instance: 'bond', '1G', '10G'. Used to determine the group of the
			interface to be modified.

		:param interface:
			This is the number of the interface, or text ID of the bond. You will likely need to translate this.

		:param vlan:
			The ID of the vlan to add.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True

		"""
		self._not_supported('set_interface_untagged_vlan')

	""" Old standard commands below this line"""


	def set_vlans(self, vlandictlist, execute=True, commit=True, delete=False):
		self._not_supported('set_vlans')




	def set_clag_backup_ip(self, backup_ip, execute=True, delete=False, commit=True):
		"""
		Sets the backup peer IP for CLAG

		:param backup_ip:
			IPv4 or IPv6 backup address of CLAG member (call self._not_supported(string) with string as a helpful error
			message if your plugin's appliance doesn't support IPv6.

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_clag_backup_ip')

	def set_clag_cidr(self, cidr, execute=True, delete=False, commit=True):
		"""
			Set the IP address and subnet mask of the primary CLAG peer interface

		:param cidr:
			CIDR of the appliance's CLAG peering interface as a string. EX; '169.254.2.1/30'

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_clag_cidr')

	def set_clag_peer_ip(self, peer_ip, execute=True, delete=False, commit=True):
		"""
		Sets CLAG interface peer IP

		:param peer_ip:
			IP address of the peer as a string I.E. '169.254.2.1'

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_clag_peer_ip')

	def set_clag_priority(self, priority, execute=True, delete=False, commit=True):
		"""
		Sets the CLAG priority of the appliance

		:param priority:
			Non negative integer

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_clag_priority')

	def set_clag_shared_mac(self, shared_mac, execute=True, delete=False, commit=True):
		"""
		Sets the shared mac of the CLAG daemon on the appliance

		:param shared_mac:
			String containing the shared MAC address of the cluster

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_clag_shared_mac')

	def set_bond_clag_id(self, type, interface, clag_id, execute=True, commit=True):
		"""
		Sets the CLAG ID of a bond

		:param type:
			This is the type of the interface, for instance: 'bond', '1G', '10G'. Used to determine the group of the
			interface to be modified.

		:param interface:
			This is the number of the interface, or text ID of the bond. You will likely need to translate this.

		:param clag_id:
			Non negative integer

		:param commit:
			If commit is true, the appliance must load the new configuration as part of this method.

		:param delete:
			If delete is true and no value is set, remove all values.
			If delete is true and there is one or more values, remove only the specified values.

		:param execute:
			If execute is True, this method must run and apply the configuration.

		:return:
			Return the list of commands that can be run to effect the change.
			You must return the list EVEN IF execute=True
		"""
		self._not_supported('set_bond_clag_id')