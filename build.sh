#!/bin/bash

set -o errexit

apt-get update
apt-get install -y tesseract-ocr

# Use the actual python environment Render uses
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "✅ build.sh completed"
