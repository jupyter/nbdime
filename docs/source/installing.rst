=============================
Installing and testing nbdime
=============================

Dependencies
------------

  - Python version 2.7.1, 3.3, 3.4, 3.5
  - six
  - nbformat

Note the requirement 2.7.1, not 2.7.0, this is because
2.7.1 fixes a bug in difflib in an interface-breaking way.

Dependencies for running tests:

  - pytest
  - pytest-cov


Install
-------
Use pip to install. See the pip documentation for options. Some examples:

Install requirements for the current user only:

    pip install --user --upgrade -r requirements.txt

Install nbdime for the current user only:

    pip install --user --upgrade .

Make a local developer install for the current user only:

    pip install --user --upgrade -e .


Testing
-------

See latest build, test and coverage status at:

    https://travis-ci.org/martinal/nbdime
    https://coveralls.io/github/martinal/nbdime?branch=master

To run tests, locally, simply run

    py.test

from the project root. If you have python 2 and python 3 installed,
you may need to run

    python3 -m pytest

to run the tests with python 3. See the pytest documentation for more options.

If you have notebooks with interesting merge challenges,
please consider contributing them to nbdime as test cases!
