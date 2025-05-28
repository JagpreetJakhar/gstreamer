#!/bin/bash
set -e

echo "Installing UV package manager..."
sudo wget -qO- https://astral.sh/uv/install.sh | sh

echo "Installing GStreamer and required libraries..."
sudo apt-get update
sudo apt-get install -y \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  python3-gi \
  gir1.2-gst-plugins-base-1.0 \
  gir1.2-gstreamer-1.0 \
  gir1.2-gtk-3.0

echo "Running UV sync..."
uv sync
echo "Installation complete."

