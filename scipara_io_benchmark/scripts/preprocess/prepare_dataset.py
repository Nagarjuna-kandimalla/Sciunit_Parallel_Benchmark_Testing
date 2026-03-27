#!/usr/bin/env python3

import os
from datetime import datetime
from logger import get_logger
import argparse
from paths import PROJECT_ROOT, size_label

parser = argparse.ArgumentParser()
parser.add_argument("--size_gb", type=float, required=True)
args = parser.parse_args()
SIZE_GB = args.size_gb
SIZE_LABEL = size_label(SIZE_GB)
TARGET_SIZE_BYTES = int(SIZE_GB * 1024 * 1024 * 1024)

logger = get_logger("prepare_dataset")

INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "ghcnd_all"
OUTPUT_FILE = PROJECT_ROOT / "data" / "prepared" / SIZE_LABEL / "input.txt"


def parse_line(line):
    station = line[0:11]
    year = int(line[11:15])
    month = int(line[15:17])
    element = line[17:21]

    values = []
    for i in range(31):
        start = 21 + i * 8
        value = line[start:start+5].strip()
        values.append(value)

    return station, year, month, element, values


def main():
    logger.info("Starting dataset preparation")

    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)

    total_bytes = 0
    files_processed = 0
    records_written = 0

    with open(OUTPUT_FILE, "w") as out:

        for fname in sorted(os.listdir(INPUT_DIR)):
            if not fname.endswith(".dly"):
                continue

            files_processed += 1
            path = INPUT_DIR / fname

            logger.info(f"Processing file: {fname}")

            with open(path) as f:
                for line in f:
                    if len(line) < 269:
                        continue

                    station, year, month, element, values = parse_line(line)

                    for day, val in enumerate(values, start=1):
                        if val == "-9999":
                            continue

                        try:
                            date = datetime(year, month, day).strftime("%Y-%m-%d")
                        except:
                            continue

                        out_line = f"{station},{date},{element},{val}\n"
                        out.write(out_line)

                        records_written += 1
                        total_bytes += len(out_line.encode("utf-8"))

                        if total_bytes >= TARGET_SIZE_BYTES:
                            logger.info("Target dataset size reached")
                            logger.info(f"Files processed: {files_processed}")
                            logger.info(f"Records written: {records_written}")
                            logger.info(f"Total bytes: {total_bytes}")
                            return

    logger.info("Dataset preparation complete")
    logger.info(f"Files processed: {files_processed}")
    logger.info(f"Records written: {records_written}")
    logger.info(f"Total bytes: {total_bytes}")


if __name__ == "__main__":
    main()
