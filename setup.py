import setuptools


setuptools.setup(
	name='etherweaver',
	#version='0.2.0dev0',
	use_scm_version=True,
	setup_requires=['setuptools_scm'],
	author='Grayson Head',
	author_email='grayson@graysonhead.net',
	url="https://github.com/graysonhead/etherweaver",
	packages=setuptools.find_packages(),
	license='GPL V3',
	install_requires = [
		'paramiko>=2.4.2',
		'PyYAML>=3.12',
		'tqdm>=4.25.0',
		'pytz>=2018.5'
	],
	long_description=open('README.md').read(),
	entry_points={
		'console_scripts': [
			'etherweaver = etherweaver.__main__:main'
		]
	}
)
