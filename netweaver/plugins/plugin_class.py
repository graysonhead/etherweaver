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

	"""Override these functions to enable each feature"""

	def get_hostname(self):
		self.not_supported()

	def set_hostname(self, hostname):
		self.not_supported()

	def get_current_config(self):
		self.not_supported()

	def get_interface(self, speed, interface):
		self.not_supported()