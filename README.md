# Jupyter Notebook Diff and Merge tools

[![Build Status](https://travis-ci.org/jupyter/nbdime.svg?branch=master)](https://travis-ci.org/jupyter/nbdime)

`nbdime` contains tools for diffing and merging of Jupyter Notebooks.

NB! This project is highly experimental and rapidly changing.

See the latest documentation at http://nbdime.readthedocs.org.

See also description and discussion in the [Jupyter Enhancement Proposal](https://github.com/jupyter/enhancement-proposals/pull/8).

Install the [codecov browser extension](https://github.com/codecov/browser-extension#codecov-extension) to view test coverage in the source browser on github.

## Installation:

    git clone https://github.com/jupyter/nbdime
    cd nbdime
    # for web-based diff tool:
      cd nbdime/webapp
      npm install && npm run build
      cd ../..
    pip install .
    