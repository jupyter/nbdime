#!/usr/bin/env bash

pip install -e .
python setup.py build

jupyter server extension enable nbdime # if developing for jupyter lab or nbclassic
jupyter labextension develop . --overwrite
