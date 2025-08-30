#!/usr/bin/env bash
# install_optional.sh
# Create (or reuse) a virtualenv and install optional requirements.

set -euo pipefail
VENV_DIR=".venv_optional"
REQ_FILE="requirements_optional.txt"

echo "Installing optional dependencies (this may take a while)..."

# macOS helper hints
if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "Detected macOS. If you plan to install face_recognition/dlib, ensure Xcode CLI tools and Homebrew are installed."
  echo "Suggested brew packages: cmake pkg-config openblas"
  echo "Run: brew install cmake pkg-config openblas"
fi

if [ ! -f "$REQ_FILE" ]; then
  echo "Requirements file $REQ_FILE not found in current directory." >&2
  exit 1
fi

if [ -d "$VENV_DIR" ]; then
  echo "Using existing virtualenv: $VENV_DIR"
else
  echo "Creating virtualenv: $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# Activate virtualenv in this shell
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel

# Install requirements; allow failures to be visible to user
echo "Installing packages from $REQ_FILE..."
if ! pip install -r "$REQ_FILE"; then
  echo "One or more packages failed to install. Check the output above for errors." >&2
  echo "Common fixes on macOS include installing: brew install cmake pkg-config openblas" >&2
  echo "You can retry the script after resolving system prerequisites." >&2
  exit 1
fi

echo "Optional dependencies installed in virtualenv: $VENV_DIR"
echo "To use it in your shell: source $VENV_DIR/bin/activate"
