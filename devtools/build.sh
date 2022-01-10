#!/bin/bash
rm -f dist/*.gz
rm -f dist/*.whl
python setup.py clean --all
python setup.py sdist bdist_wheel