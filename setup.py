#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

# the name of the project
name = 'nbdime'

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,3)):
    error = "ERROR: %s requires Python version 2.7 or 3.3 or above." % name
    print(error, file=sys.stderr)
    sys.exit(1)

PY3 = (sys.version_info[0] >= 3)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import io
import os
from glob import glob
from subprocess import check_call


from distutils import log
from distutils.cmd import Command
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist
from distutils.spawn import find_executable

from setuptools import setup
from setuptools.command.bdist_egg import bdist_egg

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
is_repo = os.path.exists(os.path.join(here, '.git'))
pkg_root = pjoin(here, name)

# Representative files that should exist after a successful build
jstargets = [
    os.path.join(here, 'nbdime', 'webapp', 'static', 'nbdime.js'),
]


if "--skip-npm" in sys.argv:
    print("Skipping install of webtools as requested.")
    skip_npm = True
    sys.argv.remove("--skip-npm")
else:
    skip_npm = False


def run(cmd, cwd=None):
    """Run a command

    >>> run('npm install', cwd='./subdir')
    """
    # On Windows, shell should be True so that the path is searched for the command.
    shell = (sys.platform == 'win32')
    check_call(cmd.split(), shell=shell, cwd=cwd, stdout=sys.stdout, stderr=sys.stderr)


def js_prerelease(command, strict=False):
    """Decorator for building minified js/css prior to another command"""
    class DecoratedCommand(command):
        def run(self):
            jsdeps = self.distribution.get_command_obj('jsdeps')
            if not is_repo and all(os.path.exists(t) for t in jstargets):
                # sdist, nothing to do
                command.run(self)
                return

            try:
                self.distribution.run_command('jsdeps')
            except Exception as e:
                missing = [t for t in jstargets if not os.path.exists(t)]
                if strict or missing:
                    log.warn('rebuilding js and css failed')
                    if missing:
                        log.error('missing files: %s' % missing)
                    raise e
                else:
                    log.warn('rebuilding js and css failed (not a problem)')
                    log.warn(str(e))
            command.run(self)
    return DecoratedCommand


def install_npm(path):
    """Return a Command for running npm install and npm build at a given path."""

    class NPM(Command):
        description = 'install package.json dependencies using npm'
        user_options = []

        node_package = path
        node_modules = pjoin(node_package, 'node_modules')

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def has_npm(self):
            return find_executable("npm")

        def run(self):
            if (skip_npm):
                log.info('Skipping npm-installation')
                return
            log.info('Checking npm-installation:')
            has_npm = self.has_npm()
            if not has_npm:
                log.error("`npm` unavailable.  If you're running this command "
                          "using sudo, make sure `npm` is availble to sudo")
            log.info('Installing build dependencies with npm.  This may '
                        'take a while...')
            run('npm install', cwd=self.node_package)
            run('npm run build', cwd=self.node_package)
    return NPM

def combine_commands(*commands):
    """Return a Command that combines several commands."""

    class CombinedCommand(Command):

        def initialize_options(self):
            self.commands = []
            for C in commands:
                self.commands.append(C(self.distribution))
            for c in self.commands:
                c.initialize_options()

        def finalize_options(self):
            for c in self.commands:
                c.finalize_options()

        def run(self):
            for c in self.commands:
                c.run()
    return CombinedCommand

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

package_data = {
    'nbdime': [
        'tests/files/*.*',
        '*.schema.json',
        'webapp/static/*.*',
        'webapp/templates/*.*',
        'webapp/testnotebooks/*.*',
    ]
}

version_ns = {}
with io.open(pjoin(here, name, '_version.py'), encoding="utf8") as f:
    exec(f.read(), {}, version_ns)


setup_args = dict(
    name            = name,
    description     = "Diff and merge of Jupyter Notebooks",
    version         = version_ns['__version__'],
    scripts         = glob(pjoin('scripts', '*')),
    packages        = packages,
    package_data    = package_data,
    author          = 'Jupyter Development Team',
    author_email    = 'jupyter@googlegroups.com',
    url             = 'http://jupyter.org',
    license         = 'BSD',
    platforms       = "Linux, Mac OS X, Windows",
    keywords        = ['Interactive', 'Interpreter', 'Shell', 'Web'],
    classifiers     = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)

class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg

    Prevents setup.py install performing setuptools' default easy_install,
    which it should never ever do.
    """
    def run(self):
        sys.exit("Aborting implicit building of eggs. Use `pip install .` to install from source.")


cmdclass = dict(
    build_ext = js_prerelease(build_ext),
    sdist  = js_prerelease(sdist, strict=True),
    jsdeps = combine_commands(
        install_npm(pjoin(here, 'nbdime-web')),
        install_npm(pjoin(here, 'nbdime', 'webapp')),
    ),
    bdist_egg = bdist_egg if 'bdist_egg' in sys.argv else bdist_egg_disabled,
)
try:
    from wheel.bdist_wheel import bdist_wheel
    cmdclass['bdist_wheel'] = js_prerelease(bdist_wheel, strict=True)
except ImportError:
    pass


setup_args['cmdclass'] = cmdclass


setuptools_args = {}
install_requires = setuptools_args['install_requires'] = [
    'nbformat',
    'six',
    'colorama',
    'tornado',
    'requests'
]

extras_require = setuptools_args['extras_require'] = {
    'test': [
        'pytest',
        'pytest-cov',
        'pytest-timeout',
        'jsonschema',
        'mock',
        'requests',
    ],
    'docs': [
        'sphinx',
        'recommonmark',
        'sphinx_rtd_theme'
    ],

    ':python_version == "2.7"': [
        'backports.shutil_which',
    ],
}

if 'setuptools' in sys.modules:
    setup_args.update(setuptools_args)

    # force entrypoints with setuptools (needed for Windows, unconditional because of wheels)
    setup_args['entry_points'] = {
        'console_scripts': [
            'nbdime = nbdime.__main__:main_dispatch',
            'nbshow = nbdime.nbshowapp:main',
            'nbdiff = nbdime.nbdiffapp:main',
            'nbdiff-web = nbdime.webapp.nbdiffweb:main',
            'nbmerge = nbdime.nbmergeapp:main',
            'nbmerge-web = nbdime.webapp.nbmergeweb:main',
            'git-nbdifftool = nbdime.gitdifftool:main',
            'git-nbmergetool = nbdime.gitmergetool:main',
            'git-nbdiffdriver = nbdime.gitdiffdriver:main',
            'git-nbmergedriver = nbdime.gitmergedriver:main',
        ]
    }
    setup_args.pop('scripts', None)

    setup_args.update(setuptools_args)

if __name__ == '__main__':
    setup(**setup_args)
