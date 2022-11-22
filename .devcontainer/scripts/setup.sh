#!/usr/bin/env bash

pip install .
python setup.py build

# sudo mkdir /usr/local/share/jupyter
# sudo chown vscode /usr/local/share/jupyter
# jupyter labextension develop . --overwrite --no-build
jupyter server extension enable nbdime # if developing for jupyter lab or nbclassic
jupyter labextension develop . --overwrite
