#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_DIR="${CONDA_ENV_DIR:-$SCRIPT_DIR/.conda/elbench}"

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda is not available on PATH." >&2
  exit 1
fi

if [ ! -x "$ENV_DIR/bin/python" ]; then
  echo "Error: conda environment not found at: $ENV_DIR" >&2
  echo "Run ./setup.sh first, or set CONDA_ENV_DIR to the environment path." >&2
  exit 1
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_DIR"

python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test
