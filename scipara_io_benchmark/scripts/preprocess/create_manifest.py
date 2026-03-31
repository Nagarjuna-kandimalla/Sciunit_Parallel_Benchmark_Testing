#!/usr/bin/env python3

import glob
import argparse
from pathlib import Path
from logger import get_logger
from paths import PROJECT_ROOT, size_label

logger = get_logger("create_manifest")
parser = argparse.ArgumentParser()
parser.add_argument("--size_gb", type=float, required=True)
args = parser.parse_args()
SIZE_GB = args.size_gb
SIZE_LABEL = size_label(SIZE_GB)
SPLIT_DIR = PROJECT_ROOT / "data" / "splits" / SIZE_LABEL
OUTPUT_FILE = PROJECT_ROOT / "data" / "manifests" / f"splits_{SIZE_LABEL}.txt"


def main():
    logger.info("Creating manifest")

    splits = sorted(Path(path).resolve() for path in glob.glob(str(SPLIT_DIR / "*.txt")))
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w") as f:
        for split_path in splits:
            f.write(str(split_path) + "\n")

    logger.info(f"Manifest created with {len(splits)} splits")


if __name__ == "__main__":
    main()
