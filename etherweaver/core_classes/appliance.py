from etherweaver.core_classes.config_object import ConfigObject
import unittest
from etherweaver.server_config_loader import get_server_config
from importlib.machinery import SourceFileLoader
from etherweaver.core_classes.utils import smart_append, parse_input_value
from etherweaver.plugins.plugin_class_errors import *
from etherweaver.core_classes.datatypes import ApplianceConfig, FabricConfig, WeaverConfig
import os
import inspect
from tqdm import tqdm

from .errors import *


class Appliance(ConfigObject):

	def __init__(self, name, appliance_dict):
		self.name = name
		self.config = appliance_dict
		self.fabric = None
		# self.role = None
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
			'dstate': {
				'apply': self.push_state,
				'get': self.dstate,
			},
			'cstate': {
				'get': self.cstate
			},
			'hostname': {
				'set': self.plugin.set_hostname,
				'get': self.plugin.cstate['hostname'],
				'data_type': str
			},
			'vlans': {
				'get': self.plugin.cstate['vlans'],
				'set': self.plugin.set_vlans
			},
			'clag': {
				'get': self.cstate['clag'],
				'shared_mac': {
					'get': self.cstate['clag']['shared_mac'],
					'set': self.plugin.set_clag_shared_mac,
					'data_type': str
				},
				'priority': {
					'get': self.cstate['clag']['priority'],
					'set': self.plugin.set_clag_priority,
					'data_type': int
				},
				'backup_ip': {
					'get': self.cstate['clag']['backup_ip'],
					'set': self.plugin.set_clag_backup_ip,
					'data_type': str
				},
				'clag_cidr': {
					'get': self.cstate['clag']['clag_cidr'],
					'set': self.plugin.set_clag_cidr,
					'data_type': str
				},
				'peer_ip': {
					'get': self.cstate['clag']['peer_ip'],
					'set': self.plugin.set_clag_peer_ip,
					'data_type': str
				}
			},
			'interfaces': {
				'get': self.cstate['interfaces'],
				'1G': {
					'get': self.cstate['interfaces']['1G']
				},
				'10G': {
					'get': self.cstate['interfaces']['10G']
				},
				'40G': {
					'get': self.cstate['interfaces']['40G']
				},
				'100G': {
					'get': self.cstate['interfaces']['100G']
				},
				'bond': {
					'get': self.cstate['interfaces']['bond']
				}
			},
			'protocols': {
				'ntp': {
					'get': self.cstate['protocols']['ntp'],
					'client':
						{
							'timezone': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['timezone'],
								'set': self.plugin.set_ntp_client_timezone,
								'data_type': str
							},
							'servers': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['servers'],
								'set': self.plugin.set_ntp_client_servers,
								'data_type': list,
								'list_subtype': str
							},
							'get': self.plugin.cstate['protocols']['ntp']['client'],
						}
				},
				'dns': {
					'get': self.plugin.cstate['protocols']['dns'],
					'nameservers': {
						'get': self.plugin.cstate['protocols']['dns']['nameservers'],
						'set': self.plugin.set_dns_nameservers,
						'data_type': list,
						'data_subtype': str
					}
				}
			}
		}

	def interface_dispatch(self, int_type, int_id):
		""" This builds a dispatch dict with the correct get values for the specified interface """
		# In cstate, bonds are strings (names) and interfaces are always integers
		int_cstate = self.cstate['interfaces'][int_type][int_id]
		int_dispatch_dict = {
				'get': int_cstate,
				'ip': {
					'get': int_cstate['ip'],
				},
				'untagged_vlan': {
					'get': int_cstate['untagged_vlan'],
					'set': self.plugin.set_interface_untagged_vlan,
					'data_type': int
				},
				'tagged_vlans': {
					'get': int_cstate['tagged_vlans'],
					'set': self.plugin.set_interface_tagged_vlans,
					'data_type': list,
					'list_subtype': int
					# TODO left off here
				}
			}
		# Some of these don't apply to bonds, so we append physical interface specific ones afterwords
		if int_type != 'bond':
			physical_specific_dict = {
				'stp': {
					'get': int_cstate['stp'],
					'port_fast': {
						'get': int_cstate['stp']['port_fast'],
						'set': self.plugin.set_portfast
					}
				},
			}
			int_dispatch_dict.update(physical_specific_dict)
		# some of these only apply to bonds
		if int_type == 'bond':
			bond_specific_dict = {
				'clag_id': {
					'get': int_cstate['clag_id'],
					'set': self.plugin.set_bond_clag_id,
					'data_type': int
				}
			}
			int_dispatch_dict.update(bond_specific_dict)
		return int_dispatch_dict

	def run_individual_command(self, func, value):
		# If value is a string named "False" convert that to a python False

		def value_detect(value):
			type = None,
			list_subtype = None

			if 'data_type' in level:
				type = level['data_type']
			if 'list_subtype' in level:
				list_subtype = level['list_subtype']
			return parse_input_value(value, type, list_subtype=list_subtype)

		if value == 'False':
			value = False
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
		is_interface = False
		skip_count = 0
		int_type = None
		int_id = None
		for com in sfunc:
			if skip_count > 0:
				skip_count = skip_count - 1
				continue
			elif com == 'apply':
				return level[com]()
			elif com == 'get':
				return level[com]
			elif com == 'add':
				# TODO: More robust error handling for this whole section
				try:
					if is_interface:
						return level['set'](int_type, int_id, value_detect(value), add=True)
					else:
						return level['set'](value_detect(value), add=True)
				except TypeError:
					raise InvalidNodeFunction(com, ".".join(sfunc[:-1]))
			elif com == 'set':
				if is_interface:
					return level[com](
						int_type,
						int_id,
						value_detect(value),
					)
				else:
					return level[com](value_detect(value))
			elif com == 'del':
				if is_interface:
					return level['set'](int_type, int_id, value_detect(value), delete=True)
				else:
					return level['set'](value_detect(value), delete=True)
			elif com == 'interfaces' and sfunc[1] != 'get' and sfunc[2] != 'get':
				int_type = sfunc[1]
				if int_type != 'bond':
					int_id = int(sfunc[2])
				else:
					int_id = sfunc[2]
				# Since we consumed the next two values in the loop, we need to skip the next 2 iterations
				skip_count = 2
				is_interface = True
				level = self.interface_dispatch(int_type, int_id)
			else:
				try:
					level = level[com]
				except KeyError:
					raise KeyError('Node {} does not exist in {}'.format(com, ".".join(sfunc)))

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
		self.plugin.add_command(self._protocol_ntpclient_push(dstate, cstate))
		self.plugin.add_command(self._vlans_push(dstate, cstate))
		# Interfaces depend on vlans, so they are run after vlans
		self._interfaces_push(dstate, cstate)
		# Bonds depend on interfaces, so they are run after interfaces
		self.plugin.add_command(self._clag_push(dstate, cstate))
		self.plugin.add_command(self._bonds_push(dstate, cstate))
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

	def _compare_state(self, dstate, cstate, func, interface=None, int_type=None, data_type=str):
		# Case0
		try:
			dstate
		except KeyError:
			return
		#if dstate is False or dstate is None or bool(dstate) is False:
		if dstate == [] or dstate == '' or dstate == {} or dstate is None:
			return
		# If the dstate specifies a value shouldn't exist with False, but the cstate is None, we have already done our
		# job
		if dstate is False and cstate is None:
			return
		# Case1
		# If data_type is set to list, we cast the list to a set while comparing it so order doesn't matter
		if data_type == list:
			if cstate is None:
				return func(int_type, interface, dstate, execute=False)
			elif set(dstate) == set(cstate):
				return
			# Case2 and 3 create
			elif set(dstate) != set(cstate):
				if not int or not int_type:
					if dstate is False:
						return func(dstate, execute=False, delete=True)
					else:
						return func(dstate, execute=False)
				elif int and int_type:
					if dstate is False:
						return func(int_type, interface, dstate, execute=False, delete=True)
					else:
						return func(int_type, interface, dstate, execute=False)
		elif data_type == str:
			if dstate == cstate:
				return
			# Case2 and 3 create
			elif dstate != cstate:
				if not int or not int_type:
					if dstate is False:
						return func(dstate, execute=False, delete=True)
					else:
						return func(dstate, execute=False)
				elif int and int_type:
					if dstate is False:
						return func(int_type, interface, dstate, execute=False, delete=True)
					else:
						return func(int_type, interface, dstate, execute=False)

	def _protocol_ntpclient_push(self, dstate, cstate):
		commands = []
		dstate = dstate['protocols']['ntp']['client']
		cstate = cstate['protocols']['ntp']['client']
		dispatcher = {
			'timezone': self.plugin.set_ntp_client_timezone,
			'servers': self.plugin.set_ntp_client_servers
		}
		for key, func in dispatcher.items():
			smart_append(commands, self._compare_state(dstate[key], cstate[key], func))
		return commands

	def _clag_push(self, dstate, cstate):
		# TODO Make all the push functions look like this one, I like it. It's pretty.
		commands = []
		dstate = dstate['clag']
		cstate = cstate['clag']
		dispatcher = {
			'backup_ip': self.plugin.set_clag_backup_ip,
			'clag_cidr': self.plugin.set_clag_cidr,
			'peer_ip': self.plugin.set_clag_peer_ip,
			'priority': self.plugin.set_clag_priority,
			'shared_mac': self.plugin.set_clag_shared_mac
		}
		for key, func in dispatcher.items():
			smart_append(commands, self._compare_state(dstate[key], cstate[key], func))
		return commands

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
		# TODO: This probably could be consolidated under the new convention
		i_dstate = dstate['interfaces']
		commands = []
		for kspd, vspd in i_dstate.items():
			if kspd in ['1G', '10G', '100G', '40G', 'mgmt']:
				for kint, vint in vspd.items():
					if 'tagged_vlans' in vint:
						smart_append(commands, self._interface_tagged_vlans_push(cstate, dstate, kspd, kint))
					if 'untagged_vlan' in vint:
						smart_append(commands, self._interface_untagged_vlan_push(cstate, dstate, kspd, kint))
					if 'stp' in vint:
						smart_append(commands, self._stp_options_push(cstate, dstate, kspd, kint))
					if 'bond_slave':
						smart_append(commands, self._bond_slave_push(cstate, dstate, kspd, kint))
		self.plugin.add_command(commands)

	def _bond_slave_push(self, cstate, dstate, kspd, kint):
		inter_dstate = dstate['interfaces'][kspd][kint]['bond_slave']
		try:
			inter_cstate = cstate['interfaces'][kspd][kint]['bond_slave']
		except KeyError:
			inter_cstate = None
		return self._compare_state(
			inter_dstate,
			inter_cstate,
			self.plugin.set_bond_slaves,
			int_type='bond',
			interface=kint
		)

	def _bonds_push(self, dstate, cstate):
		bonds_dstate = dstate['interfaces']['bond']
		commands = []
		for kbnd, vbnd in bonds_dstate.items():
			bnd_dstate = bonds_dstate[kbnd]
			try:
				bnd_cstate = cstate['interfaces']['bond'][kbnd]
			except KeyError:
				bnd_cstate = None
			dispatcher = {
				'clag_id': self.plugin.set_bond_clag_id,
				'tagged_vlans': self.plugin.set_interface_tagged_vlans,
				'untagged_vlan': self.plugin.set_interface_untagged_vlan,
			}
			for key, func in dispatcher.items():
				if bnd_dstate is not None:
					ds = bnd_dstate[key]
				else:
					ds = bnd_dstate
				if bnd_cstate is not None:
					cs = bnd_cstate[key]
				else:
					cs = bnd_cstate
				smart_append(commands, self._compare_state(ds, cs, func, int_type='bond', interface=kbnd))
		return commands


	def _stp_options_push(self, cstate, dstate, kspd, kint):
		# TODO: update this function to follow conventions
		for v in WeaverConfig.gen_portskel()['stp']:
			ds = dstate['interfaces'][kspd][kint]['stp'][v]
			# Assume false on keyerror
			try:
				cs = cstate['interfaces'][kspd][kint]['stp'][v]
			except KeyError:
				cs = False
			if v == 'port_fast':
				return self._compare_state(ds, cs, self.plugin.set_portfast, interface=kint, int_type=kspd)

	def _interface_untagged_vlan_push(self, cstate, dstate, speed, interface):
		dstate = dstate['interfaces'][speed][interface]['untagged_vlan']
		# Case 3
		try:
			cstate = cstate['interfaces'][speed][interface]['untagged_vlan']
		except KeyError:
			cstate = None
		return self._compare_state(dstate, cstate, self.plugin.set_interface_untagged_vlan, interface=interface, int_type=speed)

	def _interface_tagged_vlans_push(self, cstate, dstate, speed, interface):
		# Case 3
		dstate = dstate['interfaces'][speed][interface]['tagged_vlans']
		try:
			cstate = cstate['interfaces'][speed][interface]['tagged_vlans']
		except KeyError:
			cstate = None
		return self._compare_state(
			dstate,
			cstate,
			self.plugin.set_interface_tagged_vlans,
			interface=interface,
			int_type=speed,
			data_type=list
		)

	def _protocol_dns_nameservers_push(self, dstate, cstate):
		try:
			dstate = dstate['protocols']['dns']['nameservers']
		except KeyError:
			dstate = None
		cstate = cstate['protocols']['dns']['nameservers']
		return self._compare_state(dstate, cstate, self.plugin.set_dns_nameservers)
