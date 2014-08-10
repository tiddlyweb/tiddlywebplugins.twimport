AUTHOR = 'Chris Dent'
AUTHOR_EMAIL = 'cdent@peermore.com'
NAME = 'tiddlywebplugins.twimport'
DESCRIPTION = 'TiddlyWiki and tiddler import tools for TiddyWeb'
VERSION = '1.1.1'


import os

from setuptools import setup, find_packages


CLASSIFIERS = """
Environment :: Web Environment
License :: OSI Approved :: BSD License
Operating System :: OS Independent
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.3
Topic :: Internet :: WWW/HTTP :: WSGI
""".strip().splitlines()


setup(
    namespace_packages = ['tiddlywebplugins'],
    name = NAME,
    version = VERSION,
    description = DESCRIPTION,
    long_description = open(os.path.join(os.path.dirname(__file__), 'README')).read(),
    author = AUTHOR,
    url = 'http://pypi.python.org/pypi/%s' % NAME,
    packages = find_packages(exclude=['test']),
    author_email = AUTHOR_EMAIL,
    classifiers = CLASSIFIERS,
    platforms = 'Posix; MacOS X; Windows',
    install_requires = ['setuptools',
        'tiddlyweb>=2.0.0',
        'tiddlywebplugins.utils',
        'html5lib'],
    zip_safe = False
    )
