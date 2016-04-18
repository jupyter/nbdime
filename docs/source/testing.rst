Testing
=======

See latest automated build, test and coverage status at:

    - `Build and test on Travis <https://travis-ci.org/jupyter/nbdime>`_
    - `Coverage on Coveralls <https://coveralls.io/github/jupyter/nbdime?branch=master>`_

Dependencies
------------
Dependencies for running tests:

  - pytest
  - pytest-cov

Running tests locally
---------------------
To run tests, locally, enter::

    py.test

from the project root. If you have Python 2 and Python 3 installed,
you may need to enter::

    python3 -m pytest

to run the tests with Python 3. See the `pytest documentation`_ for more
options.

Submitting test cases
---------------------
If you have notebooks with interesting merge challenges,
please consider contributing them to nbdime as test cases!

.. _pytest documentation: http://pytest.org/latest/