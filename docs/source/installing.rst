============
Installation
============

Dependencies
------------

  - Python version 2.7.1, 3.3, 3.4, 3.5
  - six
  - nbformat

Note the requirement 2.7.1, not 2.7.0, this is because
2.7.1 fixes a bug in :mod:`difflib <py3.difflib>` in an interface-breaking way.

Installing nbdime
-----------------
Clone the `nbdime repository <https://github.com/jupyter/nbdime.git>`_::

    git clone https://github.com/jupyter/nbdime.git

Use pip to install. See the `pip documentation <https://pip.pypa.io/en/stable/>`_
for options.

Installing stable version
~~~~~~~~~~~~~~~~~~~~~~~~~
Install requirements for the current user only::

    pip install --user --upgrade -r requirements.txt

Install nbdime for the current user only::

    pip install --user --upgrade .

Installing development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Make a local developer install for the current user only::

    pip install --user --upgrade -e .
