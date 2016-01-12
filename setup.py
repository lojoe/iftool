#!/usr/bin/env python
__author__ = 'Joe Baldwin'
__author_email__ = 'joe@joebaldwin.com'
__credit__ = 'Adknowledge, Inc.'
__license__ = 'MIT'
__version__ = '0.1'


from setuptools import setup


setup(
    name='iftool',
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=['Tool for generating interface configuration files.'],
    license=__license__,
    py_modules=['iftool'],
    scripts=['iftool'],
    install_requires=[
        'docopt',
        'ipaddress',
        'jinja2',
        'pyyaml',
    ]
)
