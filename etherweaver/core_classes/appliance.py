from etherweaver.core_classes.config_object import ConfigObject
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
			for fab in self.fabric_tree[::-1]:
				dstate = dstate.merge_configs(FabricConfig(fab.config, validate=False))
		if dstate:
			dstate = dstate.merge_configs(ApplianceConfig(self.config), validate=False)

		else:
			dstate = ApplianceConfig(self.config)
		dstate.apply_profiles()
		self.dstate = dstate.get_full_config()
		self.plugin._set_plugin_options()

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
				'allowed_functions': ['get', 'apply'],
				'description': "Interact with the desired state of the appliance, either viewing the desired state"
				" or applying it non-interactively."
			},
			'cstate': {
				'get': self.cstate,
				'allowed_functions': ['get']
			},
			'hostname': {
				'set': self.plugin.set_hostname,
				'get': self.plugin.cstate['hostname'],
				'data_type': str,
				'allowed_functions': ['get', 'set', 'del']
			},
			'vlans': {
				'get': self.plugin.cstate['vlans'],
				'set': self.plugin.set_vlans,
				'allowed_functions': ['get', 'set', 'add', 'del']
			},
			'clag': {
				'get': self.cstate['clag'],
				'allowed_functions': ['get'],
				'shared_mac': {
					'get': self.cstate['clag']['shared_mac'],
					'set': self.plugin.set_clag_shared_mac,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				},
				'priority': {
					'get': self.cstate['clag']['priority'],
					'set': self.plugin.set_clag_priority,
					'data_type': int,
					'allowed_functions': ['get', 'set', 'del']
				},
				'backup_ip': {
					'get': self.cstate['clag']['backup_ip'],
					'set': self.plugin.set_clag_backup_ip,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				},
				'clag_cidr': {
					'get': self.cstate['clag']['clag_cidr'],
					'set': self.plugin.set_clag_cidr,
					'data_type': list,
					'list_subtype': str,
					'allowed_functions': ['get', 'set', 'del', 'add']
				},
				'peer_ip': {
					'get': self.cstate['clag']['peer_ip'],
					'set': self.plugin.set_clag_peer_ip,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				}
			},
			'interfaces': {
				'get': self.cstate['interfaces'],
				'allowed_functions': ['get'],
				'1G': {
					'get': self.cstate['interfaces']['1G'],
					'allowed_functions': ['get']
				},
				'10G': {
					'get': self.cstate['interfaces']['10G'],
					'allowed_functions': ['get']
				},
				'40G': {
					'get': self.cstate['interfaces']['40G'],
					'allowed_functions': ['get']
				},
				'100G': {
					'get': self.cstate['interfaces']['100G'],
					'allowed_functions': ['get']
				},
				'bond': {
					'get': self.cstate['interfaces']['bond'],
					'allowed_functions': ['get']
				}
			},
			'protocols': {
				'ntp': {
					'get': self.cstate['protocols']['ntp'],
					'allowed_functions': ['get'],
					'client':
						{
							'timezone': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['timezone'],
								'set': self.plugin.set_ntp_client_timezone,
								'data_type': str,
								'allowed_functions': ['get', 'set']
							},
							'servers': {
								'get': self.plugin.cstate['protocols']['ntp']['client']['servers'],
								'set': self.plugin.set_ntp_client_servers,
								'data_type': list,
								'list_subtype': str,
								'allowed_functions': ['get', 'set', 'del', 'add']
							},
							'get': self.plugin.cstate['protocols']['ntp']['client'],
							'allowed_functions': ['get']
						}
				},
				'dns': {
					'get': self.plugin.cstate['protocols']['dns'],
					'allowed_functions': ['get'],
					'nameservers': {
						'get': self.plugin.cstate['protocols']['dns']['nameservers'],
						'set': self.plugin.set_dns_nameservers,
						'data_type': list,
						'data_subtype': str,
						'allowed_functions': ['get', 'set', 'del', 'add']
					}
				}
			}
		}

	def interface_dispatch(self, int_type, int_id):
		""" This builds a dispatch dict with the correct get values for the specified interface """
		# In cstate, bonds are strings (names) and interfaces are always integers
		try:
			int_cstate = self.cstate['interfaces'][int_type][int_id]
		except KeyError:
			if int_type != 'bond':
				int_cstate = WeaverConfig.gen_portskel()
			else:
				int_cstate = WeaverConfig.gen_bondskel()
			self.cstate['interfaces'][int_type][int_id] = int_cstate
		int_dispatch_dict = {
				'get': int_cstate,
				'set': self.plugin.set_interface,
				'allowed_functions': ['set', 'get'],
				'ip': {
					'get': int_cstate['ip'],
					'allowed_functions': ['get'],
					'addresses': {
						'get': int_cstate['ip']['addresses'],
						'set': self.plugin.set_interface_ip_addresses,
						'data_type': list,
						'list_subtype': str,
						'allowed_functions': ['get', 'add', 'set', 'del']
					}
				},
				'untagged_vlan': {
					'get': int_cstate['untagged_vlan'],
					'set': self.plugin.set_interface_untagged_vlan,
					'data_type': int,
					'allowed_functions': ['get', 'set', 'del']
				},
				'tagged_vlans': {
					'get': int_cstate['tagged_vlans'],
					'set': self.plugin.set_interface_tagged_vlans,
					'data_type': list,
					'list_subtype': int,
					'allowed_functions': ['get', 'set', 'add', 'del']
				}
			}
		# Some of these don't apply to bonds, so we append physical interface specific ones afterwords
		if int_type != 'bond':
			physical_specific_dict = {
				'stp': {
					'get': int_cstate['stp'],
					'allowed_functions': ['get'],
					'port_fast': {
						'get': int_cstate['stp']['port_fast'],
						'set': self.plugin.set_portfast,
						'allowed_functions': ['get', 'set']
					}
				},
				'bond_slave': {
					'get': int_cstate['bond_slave'],
					'set': self.plugin.set_bond_slaves,
					'data_type': str,
					'allowed_functions': ['get', 'delete', 'set']
				},
				'mtu': {
					'get': int_cstate['mtu'],
					'set': self.plugin.set_interface_mtu,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				},
				'admin_down': {
					'get': int_cstate['admin_down'],
					'set': self.plugin.set_interface_admin_down,
					'data_type': bool,
					'allowed_functions': ['get', 'set']
				}
			}
			int_dispatch_dict.update(physical_specific_dict)
		# some of these only apply to bonds
		if int_type == 'bond':
			bond_specific_dict = {
				'clag_id': {
					'get': int_cstate['clag_id'],
					'set': self.plugin.set_bond_clag_id,
					'data_type': int,
					'allowed_functions': ['get', 'set', 'del']
				},
				'mtu': {
					'get': int_cstate['mtu'],
					'set': self.plugin.set_bond_mtu,
					'data_type': str,
					'allowed_functions': ['get', 'set', 'del']
				},
				'admin_down': {
					'get': int_cstate['admin_down'],
					'set': self.plugin.set_bond_admin_down,
					'data_type': bool,
					'allowed_functions': ['get', 'set']
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
				if 'get' in level['allowed_functions']:
					return level[com]
			elif com == 'add':
				if 'add' in level['allowed_functions']:
					if is_interface:
						return level['set'](int_type, int_id, value_detect(value), add=True)
					else:
						return level['set'](value_detect(value), add=True)
				else:
					raise InvalidNodeFunction(com, ".".join(sfunc[:-1]))
			elif com == 'set':
				if 'set' in level['allowed_functions']:
					if is_interface:
						return level[com](
							int_type,
							int_id,
							value_detect(value),
						)
					else:
						return level[com](value_detect(value))
				else:
					raise InvalidNodeFunction(com, ".".join(sfunc[:-1]))
			elif com == 'del':
				if 'del' in level['allowed_functions']:
					if is_interface:
						return level['set'](int_type, int_id, value_detect(value), delete=True)
					else:
						return level['set'](value_detect(value), delete=True)
				else:
					raise InvalidNodeFunction(com, ".".join(sfunc[:-1]))
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
		self.plugin.add_command(self._interfaces_push(dstate, cstate))
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

	@staticmethod
	def _compare_state(dstate, cstate, func, interface=None, int_type=None, data_type=str, bool_val=False):
		# Case0
		try:
			dstate
		except KeyError:
			return
		# if dstate is False or dstate is None or bool(dstate) is False:
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
					if dstate is False and not bool_val:
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
		commands = []
		dispatcher = {
			'tagged_vlans': self.plugin.set_interface_tagged_vlans,
			'untagged_vlan': self.plugin.set_interface_untagged_vlan,
			'stp': self._stp_options_push,
			'bond_slave': self.plugin.set_bond_slaves,
			'mtu': self.plugin.set_interface_mtu,
			'admin_down': self.plugin.set_interface_admin_down
		}
		bool_keys = ['admin_down']
		for ktyp, vtyp in dstate['interfaces'].items():
			if ktyp in ['1G', '10G', '100G', '40G', 'mgmt']:
				for kint, vint in vtyp.items():
					try:
						int_dstate = dstate['interfaces'][ktyp][kint]
					except KeyError:
						int_dstate = None
					try:
						int_cstate = cstate['interfaces'][ktyp][kint]
					except KeyError:
						int_cstate = None
					if vint['delete'] is True:
						# Todo: add interface deletion like bonds
						pass
					else:
						for key, func in dispatcher.items():
							if key == 'mtu':
								# If the desired state is false (unconfigure) and the cstate is 1500, its probably safe to assume its
								# deconfigured on most platforms
								if int_dstate['mtu'] is False and int_cstate['mtu'] == 1500:
									continue
							if int_dstate is not None:
								ds = int_dstate[key]
							else:
								ds = int_dstate
							if int_cstate is not None:
								cs = int_cstate[key]
							else:
								cs = int_cstate
							if key in bool_keys:
								smart_append(commands, self._compare_state(ds, cs, func, int_type=ktyp, interface=kint, bool_val=True))
							else:
								smart_append(commands, self._compare_state(ds, cs, func, int_type=ktyp, interface=kint))
		return commands

	def _interface_admin_down_push(self, cstate, dstate, kspd, kint):
		inter_dstate = dstate['interfaces'][kspd][kint]['admin_down']
		try:
			inter_cstate = cstate['interfaces'][kspd][kint]['admin_down']
		except KeyError:
			inter_cstate = False
		return self._compare_state(
			inter_dstate,
			inter_cstate,
			self.plugin.set_interface_admin_down,
			int_type=kspd,
			interface=kint,
			bool_val=True
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
				'mtu': self.plugin.set_bond_mtu
			}
			if vbnd['delete'] is True:
				smart_append(commands, self._push_bond_delete(kbnd))
				continue
			else:
				for key, func in dispatcher.items():
					if key == 'mtu':
						# If the desired state is false (unconfigure) and the cstate is 1500, its probably safe to assume its
						# deconfigured on most platforms
						if bnd_dstate['mtu'] is False and bnd_cstate['mtu'] == 1500:
							continue
					else:
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

	def _push_bond_delete(self, kbnd):
		if kbnd in self.cstate['interfaces']['bond']:
			return self.plugin.set_bond('bond', kbnd, delete=True, execute=False)

	def _stp_options_push(self, kspd, kint, dstate, execute=False):
		# TODO: update this function to follow conventions
		for v in WeaverConfig.gen_portskel()['stp']:
			ds = dstate[v]
			# Assume false on keyerror
			try:
				cs = self.cstate['interfaces'][kspd][kint]['stp'][v]
			except KeyError:
				cs = False
			if v == 'port_fast':
				return self._compare_state(ds, cs, self.plugin.set_portfast, interface=kint, int_type=kspd, bool_val=True)

	def _protocol_dns_nameservers_push(self, dstate, cstate):
		try:
			dstate = dstate['protocols']['dns']['nameservers']
		except KeyError:
			dstate = None
		cstate = cstate['protocols']['dns']['nameservers']
		return self._compare_state(dstate, cstate, self.plugin.set_dns_nameservers)
