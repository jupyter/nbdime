#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from jupyter_packaging import get_data_files, get_version
from setuptools import setup
import pathlib
import json

HERE = pathlib.Path.cwd().absolute()


JUPYTER_SHARE_PATH = (
  pathlib.PurePath("share")
      / "jupyter"
)

JUPYTER_ETC_PATH = (
  pathlib.PurePath("share")
      / "jupyter"
)

NBDIME_PATH = HERE / "nbdime"


VERSION = get_version(NBDIME_PATH / '_version.py')

with open(HERE / 'README.md') as f:
    LONG_DESCRIPTION = f.read().replace(
        'docs/source/images',
        'https://github.com/jupyter/nbdime/raw/{version}/docs/source/images'.format(version=VERSION)
    )


if __name__ == '__main__':
    setup(
      version=VERSION, 
      long_description=LONG_DESCRIPTION,
      data_files=get_data_files(
              [
                  (JUPYTER_SHARE_PATH / "nbextensions" / "nbdime", NBDIME_PATH / "notebook_ext", "*.js"),
                  (JUPYTER_SHARE_PATH / "lab" / "extensions", HERE / "packages" / "labextension" / "dist", "nbdime-jupyterlab-*.tgz"),
                  (JUPYTER_SHARE_PATH / "labextensions" / "nbdime-jupyterlab", NBDIME_PATH / "labextension", "**"),
                  (JUPYTER_ETC_PATH, HERE / "jupyter-config", "**/*.json")                
              ]
          )
      )
