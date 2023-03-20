#!/bin/bash

# Set the desired Python version
PYTHON_VERSION="3.8.12"

# Set the path to the Python script
PYTHON_SCRIPT="/home/peter/source/iacraft/iacraft/cli/cli.py"

# Activate the Python version using pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

pyenv activate support-tools
python $PYTHON_SCRIPT "$@"

