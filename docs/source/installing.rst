============
Installation
============

Installing nbdime
=================

To install the latest stable release using :command:`pip`::

    pip install --upgrade nbdime

To install and enable the nbdime notebook extensions, run::

    nbdime reg-extensions [--sys-prefix/--user/--system]

The ``--system`` (default) and ``--user`` flags determine which users
the extensions will be installed and enabled for. Note that you should
use ``--sys-prefix`` to only enable it for the currently active
virtual environment (e.g. with conda or virtualenv). For manual registration
see :doc:`extensions`.


Dependencies
------------

nbdime requires Python version 3.3 or higher. If you are using Python 2,
nbdime requires 2.7.1 or higher.

nbdime depends on the following Python packages,
which will be installed by :command:`pip`:

  - six
  - nbformat
  - tornado
  - colorama
  - backports.shutil_which (on python 2.7)

and nbdime's web-based viewers depend on the following Node.js packages:

  - codemirror
  - json-stable-stringify
  - jupyter-js-services
  - jupyterlab
  - phosphor

Installing latest development version
=====================================

Installing a development version of nbdime requires `Node.js <https://nodejs.org>`_.

Installing nbdime using :command:`pip` will install the Python package
dependencies and
will automatically run ``npm`` to install the required Node.js packages.

Setting up a virtualenv with Node.js
------------------------------------

The following steps will: create a virtualenv, named ``myenv``, in the current
directory; activate the virtualenv; and install npm inside the virtualenv
using ``nodeenv``::

    python3 -m venv myenv          # For Python 2: python2 -m virtualenv myenv
    source myenv/bin/activate
    pip install nodeenv
    nodeenv -p

With this environment active, you can now install nbdime and its
dependencies using :command:`pip`.

For example with Python 3.5, the steps with output are::

    $ python3 -m venv myenv
    $ source myenv/bin/activate
    (myenv) $ pip install nodeenv
    Collecting nodeenv
      Downloading nodeenv-1.0.0.tar.gz
    Installing collected packages: nodeenv
      Running setup.py install for nodeenv ... done
    Successfully installed nodeenv-1.0.0
    (myenv) $ nodeenv -p
     * Install prebuilt node (7.2.0) ..... done.
     * Appending data to /Users/username/myenv/bin/activate
    (myenv) $

Using Python 2.7, the steps with output are (note: you may need to install
virtualenv as shown here)::

    $ python2 -m pip install virtualenv
    Collecting virtualenv
      Downloading virtualenv-15.1.0-py2.py3-none-any.whl (1.8MB)
        100% |████████████████████████████████| 1.8MB 600kB/s
    Installing collected packages: virtualenv
    Successfully installed virtualenv-15.1.0
    $ python2 -m virtualenv myenv
    New python executable in /Users/username/myenv/bin/python
    Installing setuptools, pip, wheel...done.
    $ source myenv/bin/activate
    (myenv) $ pip install nodeenv
    Collecting nodeenv
      Downloading nodeenv-1.0.0.tar.gz
    Installing collected packages: nodeenv
      Running setup.py install for nodeenv ... done
    Successfully installed nodeenv-1.0.0
    (myenv) $ nodeenv -p
     * Install prebuilt node (7.2.0) ..... done.
     * Appending data to /Users/username/myenv/bin/activate
    (myenv) $

Install the development version
-------------------------------

Download and install directly from source::

    pip install -e git+https://github.com/jupyter/nbdime#egg=nbdime

Or clone the `nbdime repository <https://github.com/jupyter/nbdime>`_
and use ``pip`` to install::

    git clone https://github.com/jupyter/nbdime
    cd nbdime
    pip install -e .
