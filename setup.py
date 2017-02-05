#!/usr/bin/env python3
"""Setup module for spectrumuc_lamp on Raspberry Pi
See:
https://github.com/sudouc/spectrumuc_lamp
"""

# TODO: Remove most unnecessary fluff from here

raise NotImplementedError("""setup.py has not been fully tested, please just"""
                          """ use run-lamp.py for now rather than installing""")

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from setuptools.command.install import install
# To use a consistent encoding
from codecs import open
import re
import os
import sys
from os import path
import shutil
from subprocess import call

here = path.abspath(path.dirname(__file__))

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('lamp/lamp.py').read(),
    re.M
    ).group(1)

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

class CustomInstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    def run(self):
        if os.uname()[4].startswith("arm"):
            # Only try to install startup scripts on raspberry pi
            print("Setting up run-on startup service")
            try:
                # TODO: What if we don't have systemd? we don't have it by default on wheezy
                src_file = path.join(path.dirname(__file__), 'systemd/spectrumuc.service')
                call(['cp', src_file, '/lib/systemd/system'])
                call(['systemctl', 'enable', 'spectrumuc.service'])
                print("Done setting up run-on startup scripts")
            except IOError:
                sys.stderr.write("Unable to copy service file to /etc/systemd/system, maybe you're not on the right system for it")
                sys.stderr.flush()
        install.run(self)

setup(
    name='lamp',

    # TODO: Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    description='Python code for the control units of Spectrum, calls firebase backend',
    long_description=long_description,

    # Author details
    author='Alisdair Robertson',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Utilities',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.3',
        # 'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'spectrumuc_lamp': ['firebase.cfg'],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'spectrumuc=spectrumuc_lamp.spectrumuc:main',
        ],
    },

    # Custom install class to allow us to copy the service script and register with update-rc.d
    cmdclass={
        'install': CustomInstallCommand,
    },
)