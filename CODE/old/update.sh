#!/bin/bash

# Fetch the latest changes from the remote repository
git fetch origin

# Reset the local repository to match the remote repository
git reset --hard origin/main

# Find all bash and python scripts in the directory and make them executable
find . -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \;

echo "stereo_repo updated and all scripts are now executable."