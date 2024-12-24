#!/usr/bin/env bash
# build.sh

# Exit on error
set -o errexit

# Update and install system dependencies (including GDAL)
apt-get update && apt-get install -y gdal-bin libgdal-dev

# Install Python dependencies
pip install -r requirements.txt