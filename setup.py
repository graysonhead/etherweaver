from setuptools import setup, find_packages


setup(
	name='EtherWeaver',
	version='0.1dev',
	packages=find_packages(),
	license='GPL V3',
	long_description=open('README.md').read(),
	entry_points={
		'console_scripts': [
			'etherweaver = etherweaver.__main__:main'
		]
	}
)