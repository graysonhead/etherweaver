from netweaver.plugins.plugin_class import NetWeaverPlugin, NWConnType


class CumulusSwitch(NetWeaverPlugin):

	def __init__(self, conn_type=None, hostname=None, username=None, password=None, port=22, config_file=None):
		if conn_type == NWConnType.SSH:
			self.ssh = self._build_ssh_client(hostname=hostname, username=username, password=password, port=port)

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

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.ssh:
			self.ssh.close()
