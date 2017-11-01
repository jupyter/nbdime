Testing
=======

See the latest automated build, test, and coverage status at:

    - `Build and test on Travis <https://travis-ci.org/jupyter/nbdime>`_
    - `Coverage on codecov <https://codecov.io/github/jupyter/nbdime?branch=master>`_

Dependencies
------------

Install the test dependencies::

    pip install "nbdime[test]"

Running tests locally
---------------------

To run python tests, locally, enter::

    pytest

from the project root. If you have Python 2 and Python 3 installed,
you may need to enter::

    python3 -m pytest

to run the tests with Python 3. See the `pytest documentation`_ for more
options.

To run javascript/typescript tests, enter::

    npm test

Submitting test cases
---------------------

If you have notebooks with interesting merge challenges,
please consider `contributing them <https://github.com/jupyter/nbdime/issues/new>`_
to nbdime as test cases!

.. _pytest documentation: http://pytest.org/latest/
