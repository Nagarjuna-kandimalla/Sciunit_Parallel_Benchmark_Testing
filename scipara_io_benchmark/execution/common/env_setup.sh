#!/bin/bash

set -euo pipefail

echo "[ENV] ===== START ENVIRONMENT SETUP ====="

# -----------------------------
# 1. Load modules (HPC safe)
# -----------------------------
module purge || true

PYTHON_MODULE_CANDIDATES=()
if [ -n "${SCIPARA_PYTHON_MODULE:-}" ]; then
    PYTHON_MODULE_CANDIDATES+=("$SCIPARA_PYTHON_MODULE")
fi
PYTHON_MODULE_CANDIDATES+=("python/3.13.3" "python/3.10")

MODULE_LOADED=false
for module_name in "${PYTHON_MODULE_CANDIDATES[@]}"; do
    if module load "$module_name"; then
        echo "[ENV] Loaded Python module: $module_name"
        MODULE_LOADED=true
        break
    fi
done

if [ "$MODULE_LOADED" = false ]; then
    echo "[ENV] No configured Python module loaded; continuing with virtualenv Python"
fi

# -----------------------------
# 2. Activate REQUIRED venv
# -----------------------------
DEFAULT_VENV_PATH="/cluster/pixstor/data/nkmh5/parasci"
if [ -n "${SCIPARA_VENV:-}" ]; then
    VENV_PATH="$SCIPARA_VENV"
elif [ -d "$HOME/scipara" ]; then
    VENV_PATH="$HOME/scipara"
else
    VENV_PATH="$DEFAULT_VENV_PATH"
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "[ENV ERROR] Virtual environment not found at $VENV_PATH"
    exit 1
fi

echo "[ENV] Activating virtual environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# -----------------------------
# 3. Verify Python
# -----------------------------
PYTHON_BIN=$(which python)

echo "[ENV] Python path: $PYTHON_BIN"
python --version

# Ensure Python is from venv
if [[ "$PYTHON_BIN" != "$VENV_PATH"* ]]; then
    echo "[ENV ERROR] Python is NOT from the configured virtual environment"
    exit 1
fi

# -----------------------------
# 4. Verify Sciunit
# -----------------------------
echo "[ENV] Checking Sciunit..."

if ! python -m sciunit2 --help > /dev/null 2>&1; then
    echo "[ENV ERROR] Sciunit is NOT available in this environment"
    exit 1
fi

echo "[ENV] Sciunit OK"

# -----------------------------
# 5. Verify GNU Parallel
# -----------------------------
echo "[ENV] Checking GNU Parallel..."

DEFAULT_PARALLEL_BIN="/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/libexec"
if [ -n "${SCIPARA_PARALLEL_BIN:-}" ]; then
    export PATH="$SCIPARA_PARALLEL_BIN:$PATH"
elif [ -x "$DEFAULT_PARALLEL_BIN/parallel" ]; then
    export PATH="$DEFAULT_PARALLEL_BIN:$PATH"
fi

if ! command -v parallel > /dev/null 2>&1; then
    echo "[ENV ERROR] GNU Parallel NOT found"
    exit 1
fi

echo "[ENV] GNU Parallel OK"

# -----------------------------
# 6. Verify required Python packages
# -----------------------------
echo "[ENV] Checking required Python packages..."

python - <<EOF
import sys
import psutil
print("[ENV] psutil OK")
EOF

# -----------------------------
# 7. Set environment variables
# -----------------------------
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1

# Important for reproducibility
export LC_ALL=C
export LANG=C

# -----------------------------
# 8. Log node info (VERY USEFUL)
# -----------------------------
echo "[ENV] Running on node: $(hostname)"
echo "[ENV] SLURM_JOB_ID: ${SLURM_JOB_ID:-N/A}"

# -----------------------------
# 9. Disk check (optional but useful)
# -----------------------------
echo "[ENV] Checking disk space..."
df -h .

# -----------------------------
# 10. Done
# -----------------------------
echo "[ENV] ===== ENVIRONMENT READY ====="
