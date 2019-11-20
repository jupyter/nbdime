#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import os
from glob import glob

from setuptools import setup, find_packages

from setupbase import (create_cmdclass, install_npm, ensure_targets,
    combine_commands, ensure_python, get_version)

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))


# Minimal Python version sanity check
ensure_python(('2.7', '>=3.4'))

# the name of the project
name = 'nbdime'
version = get_version(pjoin(name, '_version.py'))

# Some paths
static_dir = pjoin(here, name, 'webapp', 'static')
packages_dir = pjoin(here, 'packages')

# Representative files that should exist after a successful build
jstargets = [
    pjoin(static_dir, 'nbdime.js'),
]


package_data = {
    name: [
        'tests/files/*.*',
        'tests/filters/*.py',
        '*.schema.json',
        'webapp/static/*.*',
        'webapp/templates/*.*',
        'webapp/testnotebooks/*.*',
        'notebook_ext/*.*',
    ]
}


data_spec = [
    ('share/jupyter/nbextensions/nbdime',
     name + '/notebook_ext',
     '*.js'),
    ('share/jupyter/lab/extensions',
     'packages/labextension/dist',
     'nbdime-jupyterlab-*.tgz'),
    ('etc/jupyter',
     'jupyter-config',
     '**/*.json'),
]


cmdclass = create_cmdclass('js', data_files_spec=data_spec)
cmdclass['js'] = combine_commands(
    install_npm(here, build_targets=jstargets, sources=packages_dir),
    ensure_targets(jstargets),
)


with open(pjoin(here, 'README.md')) as f:
    long_description = f.read().replace(
        'docs/source/images',
        'https://github.com/jupyter/nbdime/raw/{version}/docs/source/images'.format(version=version)
    )


setup_args = dict(
    name            = name,
    description     = "Diff and merge of Jupyter Notebooks",
    long_description=long_description,
    long_description_content_type='text/markdown',
    version         = version,
    scripts         = glob(pjoin('scripts', '*')),
    cmdclass        = cmdclass,
    packages        = find_packages(here),
    package_data    = package_data,
    author          = 'Jupyter Development Team',
    author_email    = 'jupyter@googlegroups.com',
    url             = 'https://nbdime.readthedocs.io',
    license         = 'BSD',
    platforms       = "Linux, Mac OS X, Windows",
    keywords        = ['Interactive', 'Interpreter', 'Shell', 'Web'],
    classifiers     = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Framework :: Jupyter',
    ],
)


install_requires = setup_args['install_requires'] = [
    'nbformat',
    'six',
    'colorama',
    'pygments',
    'tornado',
    'requests',
    'GitPython!=2.1.4, !=2.1.5, !=2.1.6',  # For difftool taking git refs
    'notebook',
    'jinja2>=2.9',
]

extras_require = setup_args['extras_require'] = {
    'test': [
        'pytest>=3.6',
        'pytest-cov',
        'pytest-timeout',
        'pytest-tornado5>=2',
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
}

setup_args['python_requires'] = '>=3.5'

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

if __name__ == '__main__':
    setup(**setup_args)
