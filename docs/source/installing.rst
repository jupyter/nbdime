=============================
Installing and testing nbdime
=============================

Dependencies
------------

  - Python version 2.7.1, 3.3, 3.4, 3.5
  - six
  - nbformat

Note the requirement 2.7.1, not 2.7.0, this is because
2.7.1 fixes a bug in ``difflib`` in an interface-breaking way.

Dependencies for running tests:

  - pytest
  - pytest-cov


Install
-------
Use pip to install. See the `pip documentation <https://pip.pypa.io/en/stable/>`_
for options. Some examples:

Install requirements for the current user only::

    pip install --user --upgrade -r requirements.txt

Install nbdime for the current user only::

    pip install --user --upgrade .

Make a local developer install for the current user only::

    pip install --user --upgrade -e .


Testing
-------

See latest automated build, test and coverage status at:

    - `Build and test on Travis <https://travis-ci.org/martinal/nbdime>`_
    - `Coverage on Coveralls <https://coveralls.io/github/martinal/nbdime?branch=master>`_

To run tests, locally, enter::

    py.test

from the project root. If you have Python 2 and Python 3 installed,
you may need to enter::

    python3 -m pytest

to run the tests with Python 3. See the `pytest documentation`_ for more
options.

If you have notebooks with interesting merge challenges,
please consider contributing them to nbdime as test cases!

.. _pytest documentation: http://pytest.org/latest/