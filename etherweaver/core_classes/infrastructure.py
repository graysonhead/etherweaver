from etherweaver.core_classes.fabric import Fabric
from etherweaver.core_classes.appliance import Appliance
from etherweaver.core_classes.role import NetworkRole
from etherweaver.core_classes.errors import MissingRequiredAttribute
from etherweaver.core_classes.utils import extrapolate_list, extrapolate_dict
import sys
import pprint

pp = pprint.PrettyPrinter(indent=4)


class Infrastructure:
	"""
	This is the constructor/dependency injector for the Appliance, Fabric, and Role classes
	"""

	def __init__(self, config_dict):
		self.appliances_conf = config_dict['appliances']
		if 'roles' in config_dict:
			self.roles_conf = self._extrapolate_config_dict('role', config_dict['roles'])
		else:
			self.roles_conf = None
		if 'fabrics' in config_dict:
			self.fabrics_conf = config_dict['fabrics']
		else:
			self.fabrics_conf = None
		self.appliances = []
		self.fabrics = []
		self.roles = []
		self.is_infrastructure = True

		self._build_infrastructure()

	def _extrapolate_config_dict(self, type, config):
		"""
		:param type: 'role', 'appliance', or 'dict'
		:param config:
		:return:
		"""

		if type == 'role':
			for rolek, rolev in config.items():
				if 'interfaces' in rolev:
					for spdk, spdv in rolev['interfaces'].items():
						config[rolek]['interfaces'][spdk] = extrapolate_dict(spdv)
					for spdk, spdv in rolev['interfaces'].items():
						for intk, intv in spdv.items():
							if 'tagged_vlans' in intv:
								config[rolek]['interfaces'][spdk][intk]['tagged_vlans'] = extrapolate_list(intv['tagged_vlans'])
		return config

	def _build_infrastructure(self):
		"""
		Builds the requisite classes and injects dependencies
		"""
		self._build_appliances()
		if self.fabrics_conf:
			self._build_fabrics()
		if self.roles_conf:
			self._build_roles()
		self._associate_dependencies()

	def _build_appliances(self):
		"""
		Builds appliance objects from config
		"""
		for app_key, app_dict in self.appliances_conf.items():
			self.appliances.append(Appliance(app_key, app_dict))

	def _build_fabrics(self):
		for fabric_key, fabric_dict in self.fabrics_conf.items():
			self.fabrics.append(Fabric(fabric_key, fabric_dict))

	def _build_roles(self):
		for role_key, role_dict in self.roles_conf.items():
			self.roles.append(NetworkRole(role_key, role_dict))

	def _check_attribute(self, name, dictionary, attribute):
		try:
			dictionary[attribute]
		except:
			raise MissingRequiredAttribute(attribute, name)

	def _check_required_attributes(self):
		"""Check config for missing attribute names"""
		required_app_atribs = [
			'role',
			'hostname',
			'plugin_package'
		]
		for atrib in required_app_atribs:
			for appkey, appdict in self.appliances_conf.items():
				self._check_attribute(appkey, appdict, atrib)
		required_role_atribs = [
			'fabric'
		]
		for atrib in required_role_atribs:
			for appkey, appdict in self.roles_conf.items():
				self._check_attribute(appkey, appdict, atrib)

	def _associate_dependencies(self):
		"""Attach appliances to roles"""
		for app in self.appliances:
			for role in self.roles:
				try:
					if app.config['role'] == role.name:
						app.role = role
						role.appliances.append(app)
				except KeyError:
					raise SyntaxError('Appliance {} has no associated role'.format(app.name))
			for fabric in self.fabrics:  # Attach Appliances to fabrics
				if app.role.config['fabric'] == fabric.name:
					app.fabric = fabric
					fabric.appliances.append(app)
				if 'fabric' in fabric.config:
					for pfab in self.fabrics:
						if pfab.name == fabric.config['fabric']:
							fabric.parent_fabric = pfab
							pfab.child_fabrics.append(fabric)
			app.load_plugin()
			app.build_dstate()

	def _parse_target(self, target):
		for a in self.appliances:
			if a.name == target:
				return a

	def run_command(self, target, func, value):
		if target == '*':
			# This contains the commands required to make any state changes
			retvals = {}
			# This contains a list of objects with pending commands
			apps_with_commands = []
			if func == 'state.apply':
				for app in self.appliances:
						# Set up appliance
						app.set_up()
						state = app.push_state(execute=False)
						if state:
							retvals.update({app.name: state})
							apps_with_commands.append(app)
				if apps_with_commands:
					print("If you continue, the following changes will be applied:")
					print("###################################")
					pp.pprint(retvals)
					prompt_to_continue = input("Do you want to continue? y/[n]")
					if prompt_to_continue.lower() == 'y':
						for app in apps_with_commands:
							# Build progress bars
							app.build_progress_bar(apps_with_commands.index(app))
						for app in apps_with_commands:
							# Run commands
							app.run_command_queue()
							app.close()
						print("\n\n\n")
						print("Run complete")
						sys.exit(0)
				else:
					# TODO: Exit gracefully
					print("All systems up to date")
					sys.exit()
				return
			else:
				for app in self.appliances:
					retvals.update({app.name: app.run_individual_command(func, value)})
				return retvals
		else:
			try:
				appliance = self._parse_target(target)
			except AttributeError:
				raise AttributeError('No appliance with name {} found in config'.format(target))
			return appliance.run_individual_command(func, value)