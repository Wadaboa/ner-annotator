#!/bin/bash

pip install -r requirements-deploy.txt

_PATH=$(dirname "$(realpath $0)")
cd $_PATH/..

pip install .
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*

cd $_PATH
