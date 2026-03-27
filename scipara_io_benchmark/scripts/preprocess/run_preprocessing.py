#!/usr/bin/env python3

import subprocess
import argparse
import sys
from pathlib import Path
from logger import get_logger

parser = argparse.ArgumentParser()
parser.add_argument("--size_gb", type=float, required=True)
args = parser.parse_args()

logger = get_logger("run_preprocessing")
SIZE = args.size_gb
SCRIPT_DIR = Path(__file__).resolve().parent

SCRIPTS = [
    SCRIPT_DIR / "prepare_dataset.py",
    SCRIPT_DIR / "create_splits.py",
    SCRIPT_DIR / "create_manifest.py",
    SCRIPT_DIR / "create_batches.py",
]

def run_script(script_path: Path):
    cmd = [sys.executable, str(script_path), "--size_gb", str(SIZE)]
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        logger.error(f"Failed: {script_path}")
        exit(1)

    logger.info(f"Completed: {script_path}")


def main():
    logger.info("Starting full preprocessing pipeline")

    for script in SCRIPTS:
        run_script(script)

    logger.info("Preprocessing pipeline completed successfully")


if __name__ == "__main__":
    main()
