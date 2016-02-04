"""
Install traversalgroup.
"""

try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup
	
config = {
	'description': 'Generate traversal groups of graphs',
	'author': 'Matt Christie',
	# 'url': 'URL to get it at.',
	# 'download_url': 'Where to download it.',
	'author_email': 'mjchristie@wisc.edu',
	'version': '0.1',
	'install_requires': ['numpy', 'Pillow', 'sqlalchemy'],
	# 'packages': [],
	# 'scripts': [],
	'name': 'traversalgroup'
}

setup(**config)
