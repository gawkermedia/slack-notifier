#!/bin/bash

rm -rf .venv
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
py.test --color=yes
pep8 --statistics --count --show-pep8 --show-source
