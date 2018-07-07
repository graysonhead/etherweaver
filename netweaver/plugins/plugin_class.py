from paramiko import SSHClient, WarningPolicy
from enum import IntEnum
from netweaver.plugins.plugin_class_errors import *

class NWConnType(IntEnum):
	Telnet = 1
	SSH = 2
	RS232 = 3


class NetWeaverPlugin:
	protocol = None
	def _ssh_request(self):
		"""Make an ssh request and parse returncode"""

	def _build_ssh_client(self, hostname=None, accept_untrusted=False, username=None, password=None, port=22):
		"""Returns a paramiko ssh client object"""
		ssh = SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(WarningPolicy)
		ssh.connect(hostname=hostname, port=port, username=username, password=password)
		return ssh

	def _ssh_command(self, command):
		stdin, stdout, stderr = self.ssh.exec_command(command)
		if stderr.read():
			raise SSHCommandError(stderr.read()) #TODO For some reason this line returns empty on error when run from a child instance
		return stdout.read().decode('utf-8')

	def _generic_command(self, command):
		if self.protocol == 2:
			return self._ssh_command(command)

	def not_supported(self):
		raise FeatureNotSupported

	def define_port_layout(self):
		self.not_supported()

	"""Override these functions to enable each feature"""

	def get_hostname(self):
		self.not_supported()

	def set_hostname(self, hostname, execute=True):
		self.not_supported()

	def get_current_config(self):
		self.not_supported()

	def get_interface(self, speed, interface):
		self.not_supported()

	def get_dns(self):
		self.not_supported()

	def get_dns_nameservers(self):
		self.not_supported()

	def set_dns_nameservers(self, nameserverlist, execute=True):
		self.not_supported()

	def add_dns_nameserver(self, ip, execute=True):
		self.not_supported()

	def rm_dns_nameserver(self, ip, execute=True):
		self.not_supported()

	def pull_state(self):
		self.not_supported()

	def push_state(self, execute=True):
		self.not_supported()

	def set_ntp_client_timezone(self, timezone, execute=True):
		self.not_supported()

	def add_ntp_client_server(self, ntpserver, execute=True):
		self.not_supported()

	def rm_ntp_client_server(self, ntpserver, execute=True):
		self.not_supported()

	def set_ntp_client_servers(self, ntpserverlist, execute=True):
		self.not_supported()

	def set_interface_config(self, interfaces, profile=None, execute=True):
		self.not_supported()

	def set_vlan_config(self, vlans, execute=True):
		self.not_supported()