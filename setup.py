import setuptools


setuptools.setup(
	name='etherweaver',
	version='0.1.1dev',
	author='Grayson Head',
	author_email='grayson@graysonhead.net',
	url="https://github.com/graysonhead/etherweaver",
	packages=setuptools.find_packages(),
	license='GPL V3',
	long_description=open('README.md').read(),
	entry_points={
		'console_scripts': [
			'etherweaver = etherweaver.__main__:main'
		]
	}
)