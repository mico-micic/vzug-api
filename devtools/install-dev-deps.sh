#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Required because of aiohttp dependency to multidict version <5.0,>=4.5.0
pip uninstall -y multidict
pip install multidict==4.7.6

pip install -r $SCRIPT_DIR/dev_requirements.txt

pre-commit install