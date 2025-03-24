#!/bin/bash

# This script is used to start the development environment.
# It will chack for the existence of a .env file and if it does not exist, it will create one.
# If a new .env file is created or the existing file is empty, the user will be prompted for an API key and the key will be added to the .env file.

# Check for .env file
env_file="config.env"

if [ -f "$env_file" ]; then
    # if the file is empty, prompt for API key
    if [ ! -s "$env_file" ]; then
        echo "$env_file is empty."
        echo "Please enter your API key:"
        read -s api_key
        echo "API_KEY='$api_key'" >> $env_file
        echo "API_KEY added to $env_file"
    # otherwise, continue
    else
        echo "$env_file found."
    fi
else
    echo "$env_file not found."
    echo "Creating $env_file..."
    touch $env_file
    echo "Please enter your API key:"
    read -s api_key
    echo "API_KEY='$api_key'" >> $env_file
    echo "API_KEY added to $env_file"
fi
