=============================
Installing and testing nbdime
=============================

Dependencies
------------

  - Python version 2.7.1, 3.3, 3.4, 3.5
  - six
  - nbformat

Dependencies for running tests:

  - pytest
  - pytest-cov


Install
-------
Use pip to install. See the pip documentation for options. Some examples:

Global install

    pip install .

Local install

    pip install --user .

Local developer install

    pip install -e --user .


Testing
-------

See latest build, test and coverage status at:

    https://travis-ci.org/martinal/nbdime
    https://coveralls.io/github/martinal/nbdime?branch=master

To run tests, locally, simply run

    py.test

from the project root. See the pytest documentation for more options.

If you have notebooks with interesting merge challenges,
please consider contributing them to nbdime as test cases!
