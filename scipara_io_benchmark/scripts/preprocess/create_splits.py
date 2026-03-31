#!/usr/bin/env python3

import os
import argparse
from logger import get_logger
from paths import PROJECT_ROOT, size_label

logger = get_logger("split_preprocessed_input")

parser = argparse.ArgumentParser()
parser.add_argument("--size_gb", type=float, required=True)
args = parser.parse_args()
SIZE_GB = args.size_gb
SIZE_LABEL = size_label(SIZE_GB)

INPUT_FILE = PROJECT_ROOT / "data" / "prepared" / SIZE_LABEL / "input.txt"
OUTPUT_DIR = PROJECT_ROOT / "data" / "splits" / SIZE_LABEL

LINES_PER_SPLIT = 200000


def write_split(lines, split_id):
    path = OUTPUT_DIR / f"split_{split_id:04d}.txt"
    with open(path, "w") as f:
        f.writelines(lines)

    logger.info(f"Created split: {path} with {len(lines)} lines")


def main():
    logger.info("Starting split creation")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    split_id = 1
    buffer = []
    total_lines = 0

    with open(INPUT_FILE) as f:
        for i, line in enumerate(f):
            buffer.append(line)
            total_lines += 1

            if (i + 1) % LINES_PER_SPLIT == 0:
                write_split(buffer, split_id)
                buffer = []
                split_id += 1

        if buffer:
            write_split(buffer, split_id)

    logger.info(f"Splits creation complete. Total lines: {total_lines}")


if __name__ == "__main__":
    main()
