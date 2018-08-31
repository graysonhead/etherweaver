from etherweaver.core_classes.config_object import ConfigObject
import unittest
from etherweaver.server_config_loader import get_server_config
from importlib.machinery import SourceFileLoader
from etherweaver.core_classes.utils import extrapolate_list, extrapolate_dict, smart_dict_merge
from etherweaver.plugins.plugin_class_errors import *
from etherweaver.core_classes.datatypes import ApplianceConfig, FabricConfig, RoleConfig, WeaverConfig
import os
import inspect
from tqdm import tqdm

from .errors import *


class Appliance(ConfigObject):

	def __init__(self, name, appliance_dict):
		self.name = name
		self.config = appliance_dict
		self.fabric = None
		self.role = None
		self.plugin = None
		self.progress_bar = None
		self.dtree = None
		self.dstate = {}
		self.cstate = {}
		self.is_appliance = True

		self.fabric_tree = []

	def get_cstate(self):
		self.cstate = self.plugin.pull_state()

	def _not_implemented(self):
		raise NotImplementedError

	def load_plugin(self):
		'''
		:return: plugin initialized with self.config, error otherwise (e.g. incompatible with config, plugin not found..).
		'''
		path = self.get_plugin_path()
		package = SourceFileLoader('package', '{}/{}'.format(path, '__init__.py')).load_module()
		module = SourceFileLoader('module', '{}/{}'.format(path, package.information['module_name'])).load_module()
		plugin = getattr(module, package.information['class_name'])
		self.plugin = plugin(self.cstate)
		self.plugin.appliance = self

	def build_dstate(self):
		dstate = None
		if self.fabric:
			self.fabric_tree.append(self.fabric)
			self.return_fabrics(self.fabric)
			dstate = FabricConfig(self.fabric_tree[-1].config, validate=False)
			for fab in self.fabric_tree[:-1]:
				dstate = dstate.merge_configs(FabricConfig(fab.config, validate=False))
		if self.role:
			if dstate:
				dstate = dstate.merge_configs(RoleConfig(self.role.config))
			else:
				dstate = RoleConfig(self.role.config).config
		if dstate:
			dstate = dstate.merge_configs(ApplianceConfig(self.config), validate=False)

		else:
			dstate = ApplianceConfig(self.config)
		dstate.apply_profiles()
		self.dstate = dstate.get_full_config()


	def return_fabrics(self, fabric):
		if fabric.parent_fabric:
			self.fabric_tree.append(fabric.parent_fabric)
			if fabric.parent_fabric.name != fabric.name:
				self.return_fabrics(fabric.parent_fabric)

	def _build_dispatch_tree(self):
		self.dtree = {
			'state': {
				'apply': self.push_state,
				'get': self.cstate,
			},
			'hostname': {
				'set': self.plugin.set_hostname,
				'get': self.plugin.cstate['hostname'],
			},
			'vlans': {
				'get': self.plugin.cstate['vlans'],
				'set': self.plugin.set_vlans,
				'add': self.plugin.add_vlan
			},
			'protocols': {
				'ntp': {
					'client':
						{
							'timezone': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['timezone'],
								'set': self.plugin.set_ntp_client_timezone
							},
							'servers': {
								'add': self.plugin.add_ntp_client_server,
								'get': self.plugin.cstate['protocols']['ntp']['client']['servers'],
								'del': self.plugin.rm_ntp_client_server,
								'set': self.plugin.set_ntp_client_servers
							},
							'get': self.plugin.cstate['protocols']['ntp']['client'],
						}
				},
				'dns': {
					'get': self.plugin.cstate['protocols']['dns'],
					'nameservers': {
						'get': self.plugin.cstate['protocols']['dns']['nameservers'],
						'set': self.plugin.set_dns_nameservers,
						'add': self.plugin.add_dns_nameserver,
						'del': self.plugin.rm_dns_nameserver
					}
				}
			},
			'interface': {
				'1g': {
					'get': self._not_implemented,
					'set': self._not_implemented,
				}
			}
		}

	def get_plugin_path(self):
		try:
			return '{}/{}'.format(get_server_config()['plugin_path'], self.config['plugin_package'])
		except KeyError:
			raise NonExistantPlugin
		except FileNotFoundError:
			try:
				return '{}/../plugins/{}'.format(os.path.dirname(inspect.getfile(Appliance)), self.config['plugin_package'])
			except KeyError:
				raise ConfigKeyMissing('plugin_package', 'appliance')

	def __repr__(self):
		return '<Appliance: {}>'.format(self.name)

	def set_up(self):
		self.plugin.connect()
		# Update current state before building dispatch tree
		self.cstate.update(self.plugin.pull_state())


	def run_individual_command(self, func, value):
		# Connect via whatever method is specified in protocols
		self.plugin.connect()
		# Update current state before building dispatch tree
		self.cstate.update(self.plugin.pull_state())
		self._build_dispatch_tree()
		sfunc = func.split('.')
		"""
		Iterate through each level of the config and stop when you get to a command (get, set, etc.)
		"""
		level = self.dtree
		for com in sfunc:
			if com == 'apply':
				return level[com]()
			elif com == 'get':
				return level[com]
			elif com == 'set' or com == 'add':
				return level[com](value)
			elif com == 'interfaces':
				try:
					return self.plugin.cstate['interfaces'][sfunc[1]][sfunc[2]]
				except KeyError:
					return "Interface {}/{} does not exist on {}".format(
						sfunc[1],
						sfunc[2],
						self.plugin.hostname
					)
			else:
				level = level[com]


	# State comparison methods

	def push_state(self, execute=True):
		# Run pre-push commands if the plugin writer overrode the class
		try:
			self.plugin.pre_push()
		except FeatureNotImplemented:
			pass
		dstate = self.dstate
		cstate = self.cstate
		self.plugin.add_command(self._hostname_push(dstate, cstate))
		self.plugin.add_command(self._protocol_dns_nameservers_push(dstate, cstate))
		self.plugin.add_command(self._protocol_ntpclient_timezone_push(dstate, cstate))
		self.plugin.add_command(self._protocol_ntpclient_servers(dstate, cstate))
		self.plugin.add_command(self._vlans_push(dstate, cstate))
		self.plugin.add_command(self._interfaces_push(dstate, cstate))

		if execute:
			for com in self.plugin.commands:
				self.plugin.command(com)
			self.plugin.commit()
			# self.plugin.reload_state()
			self.plugin.ssh.close()
		return self.plugin.commands

	def build_progress_bar(self, number):
		self.progress_bar = tqdm(total=self.plugin.commands.__len__(), position=number, desc=self.name)

	def run_command_queue(self):
		for com in self.plugin.commands:
			self.plugin.command(com)
			if self.progress_bar:
				self.progress_bar.update(1)
		self.plugin.commit()
		self.progress_bar.close()
		# self.plugin.reload_state()

	def close(self):
		if self.plugin.ssh:
			self.plugin.ssh.close()

	def _compare_state(self, dstate, cstate, func, interface=None, int_speed=None):
		# Case0
		try:
			dstate
		except KeyError:
			return
		#if dstate is False or dstate is None or bool(dstate) is False:
		if dstate == [] or dstate == '' or dstate == {} or dstate is None:
			return
		# Case1
		if dstate == cstate:
			return
		# Case2 and 3 create
		elif dstate != cstate:
			if not int or not int_speed:
				return func(dstate, execute=False)
			elif int and int_speed:
				return func(int_speed, interface, dstate, execute=False)

	def _protocol_ntpclient_servers(self, dstate, cstate):
		dstate = dstate['protocols']['ntp']['client']['servers']
		cstate = cstate['protocols']['ntp']['client']['servers']
		return self._compare_state(dstate, cstate, self.plugin.set_ntp_client_servers)

	def _hostname_push(self, dstate, cstate):
		try:
			dstate = dstate['hostname']
		except KeyError:
			dstate = None
		cstate = cstate['hostname']
		return self._compare_state(dstate, cstate, self.plugin.set_hostname)

	def _vlans_push(self, dstate, cstate):
		dstate = dstate['vlans']
		cstate = cstate['vlans']
		return self._compare_state(dstate, cstate, self.plugin.set_vlans)

	def _interfaces_push(self, dstate, cstate):
		# Todo, this wont work for other plugins
		i_dstate = dstate['interfaces']
		for kspd, vspd in i_dstate.items():
			for kint, vint in vspd.items():
				if 'tagged_vlans' in vint:
					self._interface_tagged_vlans_push(cstate, dstate, kspd, kint)
				if 'untagged_vlan' in vint:
					self._interface_untagged_vlan_push(cstate, dstate, kspd, kint)
				if 'stp' in vint:
					self._stp_options_push(cstate, dstate, kspd, kint)

	def _stp_options_push(self, cstate, dstate, kspd, kint):
		for v in WeaverConfig.gen_portskel()['stp']:
			ds = dstate['interfaces'][kspd][kint]['stp'][v]
			cs = cstate['interfaces'][kspd][kint]['stp'][v]
			if v == 'port_fast':
				self.plugin.add_command(self._compare_state(ds, cs, self.plugin.set_portfast, interface=kint, int_speed=kspd))



	def _interface_untagged_vlan_push(self, cstate, dstate, speed, interface):
		dstate = dstate['interfaces'][speed][interface]['untagged_vlan']
		# Case 3
		try:
			cstate = cstate['interfaces'][speed][interface]['untagged_vlan']
		except KeyError:
			self.plugin.add_command(self.plugin.set_interface_untagged_vlan(interface, dstate, execute=False))
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
			self.plugin.add_command(
				self.plugin.set_interface_untagged_vlan(interface, dstate, execute=False))

	def _interface_tagged_vlans_push(self, cstate, dstate, speed, interface):
		# Case 3
		dstate = set(dstate['interfaces'][speed][interface]['tagged_vlans'])
		try:
			cstate = set(cstate['interfaces'][speed][interface]['tagged_vlans'])
		except KeyError:
			self.plugin.add_command(self.plugin.set_interface_tagged_vlans(speed, interface, dstate, execute=False))
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
			self.plugin.add_command(self.plugin.set_interface_tagged_vlans(speed, interface, dstate, execute=False))

	def _protocol_ntpclient_timezone_push(self, dstate, cstate):
		cstate = cstate['protocols']['ntp']['client']['timezone']
		dstate = dstate['protocols']['ntp']['client']['timezone']
		return self._compare_state(dstate, cstate, self.plugin.set_ntp_client_timezone)

	def _protocol_dns_nameservers_push(self, dstate, cstate):
		try:
			dstate = dstate['protocols']['dns']['nameservers']
		except KeyError:
			dstate = None
		cstate = cstate['protocols']['dns']['nameservers']
		return self._compare_state(dstate, cstate, self.plugin.set_dns_nameservers)
