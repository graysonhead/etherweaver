from netweaver.plugins.plugin_class import NetWeaverPlugin, NWConnType
from functools import wraps

class CumulusSwitch(NetWeaverPlugin):

	def __init__(self, config, fabricconfig):
		self.is_plugin = True
		self.fabricconfig = fabricconfig
		self.hostname = config['hostname']
		self.username = fabricconfig['credentials']['username']
		self.password = fabricconfig['credentials']['password']
		self.port = 22

	def build_ssh_session(self):
		self.conn_type = NWConnType  #TODO, make this dynamically selected based on something
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

	def get_hostname(self):
		return self.command('hostname').strip('\n')

	def set_hostname(self, hostname):
		if self.ssh:
			out = self.command('net add hostname {}'.format(hostname))
			self._net_commit()
			return out

	def _net_commit(self):
		if self.ssh:
			return self.command('net commit')

	def _ifparser(text):
		# Will parse lines with these keys as interfaces
		iface_keys = ("interface", "iface")
		# Will parse lines starting with these keys as options
		iface_opts = ("address")
		# This variable will be used to remember what interface we are on, in order to place options in the right
		# dict
		ifaces = {}
		current_interface = None
		for line in text.split('\n'):

			# If the line is an interface stanza, this should catch it
			if line.startswith(iface_keys):
				# Split the interface declaration
				line_items = line.split(' ')
				ifname = line_items[1]  # Interface name should be the second item
				ifaces.update({ifname: {}})
				# If there are more than two items on this line, the rest are options
				if len(line_items) > 2:
					opts = line_items[2:len(line_items)]
					ifaces[ifname].update({'options': opts})
				# Any lines starting with an option name from this point on belong to the previously identified interface
				current_interface = ifname
			elif line.strip().startswith(iface_opts):  # Strip whitespace, as the option lines are indented
				opt = line.strip().split(" ")
				# Most options have one value
				if len(opt) == 2:
					ifaces[current_interface].update({opt[0]: opt[1]})
				# But some have more
				if len(opt) > 2:
					ifaces[current_interface].update({opt[0]: []})
					for value in opt[1:len(opt)]:
						ifaces[current_interface][opt[0]].append(value)
		return ifaces

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.ssh:
			self.ssh.close()
