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
		if 'fabrics' in config_dict:
			self.fabrics_conf = config_dict['fabrics']
		else:
			self.fabrics_conf = None
		self.appliances = []
		self.fabrics = []
		# self.roles = []
		self.is_infrastructure = True

		self._build_infrastructure()

	def _build_infrastructure(self):
		"""
		Builds the requisite classes and injects dependencies
		"""
		self._build_appliances()
		if self.fabrics_conf:
			self._build_fabrics()
		# if self.roles_conf:
		# 	self._build_roles()
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


	def _check_attribute(self, name, dictionary, attribute):
		try:
			dictionary[attribute]
		except:
			raise MissingRequiredAttribute(attribute, name)

	def _associate_dependencies(self):
		#Associate fabrics with their parent fabrics
		for fabric in self.fabrics:
			# If fabric is a key in the fabric's config, it has a parent fabric
			if 'fabric' in fabric.config:
				# Find the parent fabric based on it's name
				pfab = list(filter(lambda pf: pf.name == fabric.config['fabric'], self.fabrics))[0]
				fabric.parent_fabric = pfab
				pfab.child_fabrics.append(fabric)
		for app in self.appliances:
			if 'fabric' in app.config:
				# Find the parent fabric based on it's name
				pfab = list(filter(lambda pf: pf.name == app.config['fabric'], self.fabrics))[0]
				app.fabric = pfab
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