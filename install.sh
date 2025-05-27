#!/bin/bash
# install.sh
# This script installs GStreamer and required libraries, then runs uv sync.


sudo wget -qO- https://astral.sh/uv/install.sh | sh

set -e

echo "Installing GStreamer and required libraries..."
sudo apt-get update
sudo apt-get install -y \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly

echo "Running UV sync..."
uv sync
echo "Installation complete."


