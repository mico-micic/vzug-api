#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pip install -r $SCRIPT_DIR/dev_requirements.txt

pre-commit install