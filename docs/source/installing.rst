============
Installation
============

Installing nbdime
-----------------

To install nbdime you need python version 2.7.1+, or 3.3 or higher, as
well as node.js. Note the requirement python 2.7.1, not 2.7.0, this is
because 2.7.1 fixes a bug in :mod:`difflib <py3.difflib>` in an
interface-breaking way.

Installing nbdime using `standard pip options <https://pip.pypa.io/en/stable/>`_
will automatically run npm to install the required node.js packages
as well as the python package dependencies.

Dependencies
------------
Nbdime depends the following python packages:

  - six
  - nbformat
  - tornado
  - colorama
  - backports.shutil_which (on python 2.7)

and the following npm packages:

  - codemirror
  - json-stable-stringify
  - jupyter-js-services
  - jupyterlab
  - phosphor

Setting up a virtualenv with node.js before installing nbdime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following steps will create a virtualenv in the current
directory named 'myenv' and install npm inside the virtualenv::

    virtualenv myenv
    source myenv/bin/activate
    pip install nodeenv
    nodeenv -p

With this environment active you can install nbdime with all
dependencies using pip as usual.

Installing latest release
~~~~~~~~~~~~~~~~~~~~~~~~~

Install latest release from pypi::

    pip install nbdime

Installing latest development version of nbdime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Download and install directly from source::

    pip install git+https://github.com/jupyter/nbdime/archive/master.zip

Or clone the `nbdime repository <https://github.com/jupyter/nbdime.git>`_
and use pip to install::

    git clone https://github.com/jupyter/nbdime.git
    cd nbdime
    pip install .

