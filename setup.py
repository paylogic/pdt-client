"""Setuptools entry point."""

import codecs
from os.path import abspath, dirname, join
import sys

from setuptools import setup, find_packages

from pdt_client import __version__

long_description = []

install_requires = [
    'alembic',
    'alembic-offline>=1.2.0',
    'capturer>=2.1',
    'requests',
    'six',
    'sqlalchemy',
]

if sys.version_info < (3, 0, 0):
    install_requires.append('subprocess32')

tests_require = [
    "mock==1.0.1",
    "pylama==6.3.1",
    "pytest==2.7.0",
    "pytest-mock==0.4.3"
]

for text_file in ['README.rst', 'CHANGES.rst']:
    with codecs.open(join(dirname(abspath(__file__)), text_file), encoding='utf-8') as f:
        long_description.append(f.read())

setup(
    name="pdt-client",
    description="Client for paylogic deployment tool",
    long_description='\n'.join(long_description),
    author="Anatoly Bubenkov, Paylogic International and others",
    license="MIT license",
    author_email="developers@paylogic.com",
    url="https://github.com/paylogic/pdt-client",
    version=__version__,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    packages=find_packages(include=["pdt_client*"]),
    install_requires=install_requires,
    entry_points="""
    [console_scripts]
    pdt-client = pdt_client.script:main
    """,
    tests_require=tests_require,
    extras_require=dict(test=tests_require)
)
