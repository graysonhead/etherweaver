from paramiko import SSHClient, WarningPolicy
from scp import SCPClient

class NetWeaverPlugin:

	def _ssh_request(self):
		"""Make an ssh request and parse returncode"""

	def _build_ssh_client(self, hostname=None, accept_untrusted=False, username=None, password=None, port=22):
		"""Returns a paramiko ssh client object"""
		ssh = SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(WarningPolicy)
		ssh.connect(hostname=hostname, port=port, username=username, password=password)
		return ssh