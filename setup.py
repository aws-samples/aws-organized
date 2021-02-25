# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': '.'}

packages = \
['aws_organized',
 'aws_organized.extensions',
 'aws_organized.extensions.service_control_policies']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=5.3.1,<6.0.0',
 'awacs>=1.0.1,<2.0.0',
 'better-boto==0.36.0',
 'boto3>=1.16.4,<2.0.0',
 'click>=7.1.2,<8.0.0',
 'troposphere>=2.6.3,<3.0.0']

entry_points = \
{'console_scripts': ['aws-organized = aws_organized.cli:cli']}

setup_kwargs = {
    'name': 'aws-organized',
    'version': '0.0.1',
    'description': '',
    'long_description': None,
    'author': 'Eamonn Faherty',
    'author_email': 'eamonnf@amazon.co.uk',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
