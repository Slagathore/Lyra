#!/bin/bash

echo "Setting up Lyra environment for Linux/macOS..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10 or newer and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "lyra_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv lyra_env
else
    echo "Using existing virtual environment..."
fi

# Activate the environment and install dependencies
echo "Installing dependencies..."
source lyra_env/bin/activate
python -m pip install --upgrade pip setuptools wheel

# Install dependencies using the resolve_dependencies.py script
echo "Running dependency resolver..."
python resolve_dependencies.py --use-existing-venv --with-openai

echo ""
echo "Setup completed! To run Lyra:"
echo "1. Activate the environment: source lyra_env/bin/activate"
echo "2. Start Lyra: python -m lyra.main"
echo ""
