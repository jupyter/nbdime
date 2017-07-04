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
if v[:2] < (2, 7) or (v[0] >= 3 and v[:2] < (3, 3)):
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

from setuptools import setup, find_packages

from setupbase import (create_cmdclass, install_npm, ensure_targets,
    combine_commands, BaseCommand, skip_npm)

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))

# Representative files that should exist after a successful build
jstargets = [
    os.path.join(here, name, 'webapp', 'static', 'nbdime.js'),
]


package_data = {
    name: [
        'tests/files/*.*',
        '*.schema.json',
        'webapp/static/*.*',
        'webapp/templates/*.*',
        'webapp/testnotebooks/*.*',
        'notebook_ext/*.*',
    ]
}

version_ns = {}
with io.open(pjoin(here, name, '_version.py'), encoding="utf8") as f:
    exec(f.read(), {}, version_ns)


cmdclass = create_cmdclass(('jsdeps',))
cmdclass['jsdeps'] = combine_commands(
    install_npm(here),
    ensure_targets(jstargets),
)


setup_args = dict(
    name            = name,
    description     = "Diff and merge of Jupyter Notebooks",
    version         = version_ns['__version__'],
    scripts         = glob(pjoin('scripts', '*')),
    cmdclass        = cmdclass,
    packages        = find_packages(here),
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
        'Framework :: Jupyter',
    ],
)


setuptools_args = {}
install_requires = setuptools_args['install_requires'] = [
    'nbformat',
    'six',
    'colorama',
    'tornado',
    'requests',
    'GitPython!=2.1.4, !=2.1.5, !=2.1.6',  # For difftool taking git refs
    'notebook',
    'jinja2',
]

extras_require = setuptools_args['extras_require'] = {
    'test': [
        'pytest',
        'pytest-cov',
        'pytest-timeout',
        'pytest-tornado',
        'jsonschema',
        'mock',
        'requests',
        'tabulate',  # For profiling
    ],
    'docs': [
        'sphinx',
        'recommonmark',
        'sphinx_rtd_theme'
    ],

    ':python_version == "2.7"': [
        'backports.shutil_which',
        'backports.functools_lru_cache',
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
            'git-nbdiffdriver = nbdime.vcs.git.diffdriver:main',
            'git-nbdifftool = nbdime.vcs.git.difftool:main',
            'git-nbmergedriver = nbdime.vcs.git.mergedriver:main',
            'git-nbmergetool = nbdime.vcs.git.mergetool:main',
            'hg-nbdiff = nbdime.vcs.hg.diff:main',
            'hg-nbdiffweb = nbdime.vcs.hg.diffweb:main',
            'hg-nbmerge = nbdime.vcs.hg.merge:main',
            'hg-nbmergeweb = nbdime.vcs.hg.mergeweb:main',
        ]
    }
    setup_args.pop('scripts', None)

    setup_args.update(setuptools_args)

if __name__ == '__main__':
    setup(**setup_args)
