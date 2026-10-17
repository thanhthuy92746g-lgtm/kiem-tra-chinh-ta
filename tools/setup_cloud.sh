#!/usr/bin/env bash
set -euo pipefail

cd /workspace/kiem-tra-chinh-ta
export PIP_CACHE_DIR=/workspace/scratch/pip-cache
export XDG_CACHE_HOME=/workspace/scratch/cache
mkdir -p "$PIP_CACHE_DIR" "$XDG_CACHE_HOME"
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Cần Python 3.11+"'
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
if [ ! -f data/ngram.sqlite ] && [ -f resources/trained-model.zip ]; then
  .venv/bin/python tools/ci_model.py restore
else
  .venv/bin/python tools/bootstrap_data.py
fi
.venv/bin/python -m vietspell doctor
