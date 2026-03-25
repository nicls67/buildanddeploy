#!/bin/bash
set -e

echo "Setting up virtual environment..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing project dependencies..."
pip install PyYAML GitPython

echo "Installing checkers and testing tools..."
pip install ruff mypy pytest types-PyYAML

echo "Setup complete! You can activate your environment by running:"
echo "source .venv/bin/activate"
