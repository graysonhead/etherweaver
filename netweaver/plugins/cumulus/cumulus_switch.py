from netweaver.plugins.plugin_class import NetWeaverPlugin, NWConnType


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

	def get_hostname(self):
		if self.ssh:
			return self._ssh_command('hostname').strip('\n')

	def set_hostname(self, hostname):
		if self.ssh:
			return self._ssh_command('net add hostname {}'.format(hostname))
			self._net_commit()

	def _net_commit(self):
		if self.ssh:
			return self._ssh_command('net commit')

	def command(self, command):
		if 'get.hostname' in command:
			return self.get_hostname()


	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.ssh:
			self.ssh.close()
