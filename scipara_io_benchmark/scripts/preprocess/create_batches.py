#!/usr/bin/env python3

import os
import argparse
from pathlib import Path
from logger import get_logger
from paths import PROJECT_ROOT, size_label

logger = get_logger("create_batches")
parser = argparse.ArgumentParser()
parser.add_argument("--size_gb", type=float, required=True)
args = parser.parse_args()
SIZE_GB = args.size_gb
SIZE_LABEL = size_label(SIZE_GB)
MANIFEST = PROJECT_ROOT / "data" / "manifests" / f"splits_{SIZE_LABEL}.txt"
OUTPUT_DIR = PROJECT_ROOT / "batches" / SIZE_LABEL
BATCH_SIZE = 5


def main():
    logger.info("Creating batches")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(MANIFEST) as f:
        splits = []
        for line in f:
            split_path = line.strip()
            if not split_path:
                continue

            split = Path(split_path)
            if not split.is_absolute():
                split = (PROJECT_ROOT / split).resolve()

            splits.append(str(split))

    batch_count = 0

    for i in range(0, len(splits), BATCH_SIZE):
        batch = splits[i:i+BATCH_SIZE]
        batch_id = i // BATCH_SIZE + 1

        path = OUTPUT_DIR / f"batch_{batch_id:03d}.txt"

        with open(path, "w") as out:
            for s in batch:
                out.write(s + "\n")

        logger.info(f"Created batch {batch_id} with {len(batch)} splits")
        batch_count += 1

    logger.info(f"Total batches created: {batch_count}")


if __name__ == "__main__":
    main()
