#!/usr/bin/env bash

head="${1:-./nbdime/tests/files/apap--1.ipynb}"
base="${2:-./nbdime/tests/files/apap.ipynb}"
python -m nbdime diff-web $head $base
