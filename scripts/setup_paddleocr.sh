#!/usr/bin/env bash
# Setup Python 3.10 via pyenv and install PaddleOCR
# Note: ignore HyDE shell function import errors by NOT using set -e

PYENV_ROOT="$HOME/.pyenv"
PATH="$PYENV_ROOT/bin:$PATH"

echo "=== pyenv version ==="
"$PYENV_ROOT/bin/pyenv" --version 2>&1

echo "=== Installing Python 3.10.14 (skip if exists) ==="
"$PYENV_ROOT/bin/pyenv" install 3.10.14 --skip-existing 2>&1

echo "=== Checking Python 3.10.14 binary ==="
PY310="$PYENV_ROOT/versions/3.10.14/bin/python3.10"
$PY310 --version 2>&1

echo "=== Creating venv_paddle with Python 3.10 ==="
$PY310 -m venv /home/rudnibh/Projects/TeevrGati/venv_paddle 2>&1

PADDLE_PIP="/home/rudnibh/Projects/TeevrGati/venv_paddle/bin/pip"

echo "=== Installing paddlepaddle 2.6.2 ==="
$PADDLE_PIP install -q "paddlepaddle==2.6.2" 2>&1 | tail -3

echo "=== Installing paddleocr ==="
$PADDLE_PIP install -q "paddleocr>=2.7.0" 2>&1 | tail -3

echo "=== Verifying PaddleOCR import ==="
/home/rudnibh/Projects/TeevrGati/venv_paddle/bin/python -c "
from paddleocr import PaddleOCR
print('PaddleOCR import OK')
" 2>&1

echo "=== DONE ==="
