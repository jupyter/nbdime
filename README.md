This is nbdime, tools for diff and merge of Jupyter Notebooks
=============================================================

NB! This is currently experimental and rapidly changing.

Dependencies
------------

  - Python version 2.7.1, Python 3 support is coming
  - six
  - nbformat
  - pytest
  - numpy
  - (Levenshtein)

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
If you have notebooks with interesting merge challenges,
please consider contributing them to nbdime as test cases!

Run

    py.test

from the root of the nbdime project.

While developing,

    py.test -f -l -s

can be useful. See the pytest documentation for more options.
