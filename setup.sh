#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-elbench}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
CONDA_CHANNEL="${CONDA_CHANNEL:-conda-forge}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export HOME="${CONDA_SETUP_HOME:-$SCRIPT_DIR/.conda/home}"
mkdir -p "$HOME"

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda is not available on PATH." >&2
  echo "Install Miniconda/Anaconda or initialize conda for this shell, then retry." >&2
  exit 1
fi

eval "$(conda shell.bash hook)"

ENV_DIR="${CONDA_ENV_DIR:-$SCRIPT_DIR/.conda/$ENV_NAME}"
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$SCRIPT_DIR/.conda/pkgs}"
mkdir -p "$CONDA_PKGS_DIRS"

if [ -d "$ENV_DIR" ] && [ ! -x "$ENV_DIR/bin/python" ]; then
  echo "Removing incomplete conda environment: $ENV_DIR"
  rm -rf "$ENV_DIR"
fi

if [ ! -d "$ENV_DIR" ]; then
  echo "Creating conda environment: $ENV_DIR (python=$PYTHON_VERSION)"
  conda create -y -p "$ENV_DIR" --override-channels -c "$CONDA_CHANNEL" "python=$PYTHON_VERSION"
else
  echo "Using existing conda environment: $ENV_DIR"
fi

conda activate "$ENV_DIR"

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .

echo
echo "Setup complete."
echo "Activate with: conda activate $ENV_DIR"
