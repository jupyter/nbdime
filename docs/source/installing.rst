============
Installation
============

Installing nbdime
=================

To install latest release from pypi::

    pip install --upgrade nbdime


Dependencies
------------

nbdime requires python version 2.7.1+, or 3.3 or higher.

.. note::

    Python 2.7.1 is required, not 2.7.0, this is
    because 2.7.1 fixes a bug in :mod:`difflib <py3.difflib>` in an
    interface-breaking way.


nbdime depends the following python packages,
which will be pulled in by :command:`pip`:

  - six
  - nbformat
  - tornado
  - colorama
  - backports.shutil_which (on python 2.7)

and its web-based viewers use the following npm packages:

  - codemirror
  - json-stable-stringify
  - jupyter-js-services
  - jupyterlab
  - phosphor


Installing latest development version of nbdime
===============================================

Installing a development version of nbdime requires nodejs.

Installing nbdime using `standard pip options <https://pip.pypa.io/en/stable/>`_
will automatically run npm to install the required node.js packages
as well as the python package dependencies.


Setting up a virtualenv with node.js before installing nbdime
-------------------------------------------------------------

The following steps will create a virtualenv in the current
directory named 'myenv' and install npm inside the virtualenv::

    virtualenv myenv
    source myenv/bin/activate
    pip install nodeenv
    nodeenv -p

With this environment active you can install nbdime with all
dependencies using pip as usual.


Doing a development install
---------------------------

Download and install directly from source::

    pip install -e git+https://github.com/jupyter/nbdime

Or clone the `nbdime repository <https://github.com/jupyter/nbdime>`_
and use pip to install::

    git clone https://github.com/jupyter/nbdime
    cd nbdime
    pip install -e .

