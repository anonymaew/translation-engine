#!/bin/bash

# This script is used to create a virtual environment for the project
# and install all the dependencies in the requirements.txt file.
# Author: Korben Tompkin

# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the dependencies
pip install -r requirements.txt

# Run the program
python3 main.py $1

# Deactivate the virtual environment
deactivate

# Remove the virtual environment
rm -rf venv
