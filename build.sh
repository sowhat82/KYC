#!/usr/bin/env bash
echo "DEBUG: Starting render-build.sh script"
apt-get update && apt-get install -y tesseract-ocr
echo "DEBUG: Finished installing Tesseract"