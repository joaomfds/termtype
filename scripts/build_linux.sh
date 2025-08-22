#!/usr/bin/env bash
set -euo pipefail

# Build a one-file Linux executable for typeterm using PyInstaller.
# Outputs dist/typeterm (single ELF binary)

if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Upgrading pip..."
python -m pip install --upgrade pip >/dev/null

echo "Installing build dependencies..."
python -m pip install pyinstaller -r requirements.txt

echo "Building one-file executable..."
pyinstaller --onefile --name typeterm typeterm/__main__.py

echo
echo "Build complete: dist/typeterm"
echo "You can run it via: ./dist/typeterm --mode time --seconds 60"

