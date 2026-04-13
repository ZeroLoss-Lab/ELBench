#!/usr/bin/env bash

SOURCED=0
if [ -n "${BASH_VERSION-}" ]; then
  [[ "${BASH_SOURCE[0]}" != "$0" ]] && SOURCED=1
elif [ -n "${ZSH_VERSION-}" ]; then
  [[ "$ZSH_EVAL_CONTEXT" == *:file ]] && SOURCED=1
fi

if [ "$SOURCED" -eq 0 ]; then
  set -euo pipefail
fi

if [ -n "${BASH_VERSION-}" ]; then
  SCRIPT_PATH="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION-}" ]; then
  SCRIPT_PATH="${(%):-%x}"
else
  SCRIPT_PATH="$0"
fi

SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

main() {
cd "$SCRIPT_DIR" || return 1

ENV_DIR="${CONDA_ENV_DIR:-$SCRIPT_DIR/.conda/elbench}"
if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda is not available on PATH." >&2
  return 1
fi

if [ ! -x "$ENV_DIR/bin/python" ]; then
  echo "Error: conda environment not found at: $ENV_DIR" >&2
  echo "Run ./setup.sh first, or set CONDA_ENV_DIR to the environment path." >&2
  return 1
fi

if [ -n "${ZSH_VERSION-}" ]; then
  eval "$(conda shell.zsh hook)" || return 1
else
  eval "$(conda shell.bash hook)" || return 1
fi
conda activate "$ENV_DIR" || return 1
python -m pip install regex sympy word2number latex2sympy2_extended

python scripts/run_benchmark.py run --model-id mock.default --max-samples 3 --run-id smoke-test
}

main "$@"
