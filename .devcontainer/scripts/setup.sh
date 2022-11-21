#!/usr/bin/env bash

pip install .
python setup.py build

# sudo mkdir /usr/local/share/jupyter
# sudo chown vscode /usr/local/share/jupyter
# jupyter labextension develop . --overwrite --no-build
jupyter server extension enable nbdime # if developing for jupyter lab or nbclassic

jupyter nbextension install --py nbdime --sys-prefix [--sym-link]
jupyter nbextension enable --py nbdime --sys-prefix

jupyter labextension link ./packages/nbdime --no-build
jupyter labextension install ./packages/labextension
