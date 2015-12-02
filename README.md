This is nbdime, tools for diff and merge of Jupyter Notebooks
=============================================================

NB! This project is highly experimental and rapidly changing.


Documentation
-------------

To build documentation:

    cd docs
    make html

Also available at:
    
    http://nbdime.readthedocs.org


Dependencies
------------

  - Python version 2.7.1, 3.3, 3.4, 3.5
  - six
  - nbformat

Test dependencies:

  - pytest
  - pytest-cov


Install
-------
Insert standard pip install instructions here. Examples:

Global install

    pip install .

Local install

    pip install --user .

Local developer install

    pip install -e --user .


Commandline tools
-----------------
Nbdime adds three commands to jupyter. See

    jupyter nbdiff --help
    jupyter nbpatch --help
    jupyter nbmerge --help

for usage details.


Testing
-------

Run

    py.test

from the root of the nbdime project.

While developing,

    py.test -f -l -s

can be useful. See the pytest documentation for more options.

If you have notebooks with interesting merge challenges,
please consider contributing them to nbdime as test cases!

For latest test status see Travis:

    https://travis-ci.org/martinal/nbdime

And coverall:

[![Coverage Status](https://coveralls.io/repos/martinal/nbdime/badge.svg?branch=master&service=github)](https://coveralls.io/github/martinal/nbdime?branch=master)

