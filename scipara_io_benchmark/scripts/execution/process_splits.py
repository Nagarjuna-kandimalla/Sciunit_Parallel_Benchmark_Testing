#!/usr/bin/env python3

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


# Keep only these weather elements
KEEP_ELEMENTS = {"TMAX", "TMIN", "PRCP"}


def log(msg, logfile):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logfile.write(f"[{timestamp}] {msg}\n")
    logfile.flush()


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def process_split(input_path, output_path, metrics_path, log_path):

    ensure_parent(output_path)
    ensure_parent(metrics_path)
    ensure_parent(log_path)

    with open(log_path, "w") as logf:

        log(f"START processing splits: {input_path}", logf)

        start_time = time.time()
        start_iso = datetime.now().isoformat()

        input_lines = 0
        output_lines = 0
        bad_lines = 0

        input_bytes = os.path.getsize(input_path)
        log(f"Input file size: {input_bytes} bytes", logf)

        with open(input_path, "r", encoding="utf-8", errors="replace") as fin, \
             open(output_path, "w", encoding="utf-8") as fout:

            for line in fin:
                input_lines += 1
                line = line.rstrip("\n")

                if not line:
                    continue

                parts = line.split(",")

                if len(parts) != 4:
                    bad_lines += 1
                    continue

                station_id, date_str, element, value = parts

                if element in KEEP_ELEMENTS:
                    fout.write(line + "\n")
                    output_lines += 1

                # Log progress every 500k lines
                if input_lines % 500000 == 0:
                    log(f"Processed {input_lines} lines...", logf)

        end_time = time.time()
        end_iso = datetime.now().isoformat()

        duration = end_time - start_time

        output_bytes = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        log(f"Finished processing", logf)
        log(f"Total input lines: {input_lines}", logf)
        log(f"Total output lines: {output_lines}", logf)
        log(f"Bad lines: {bad_lines}", logf)
        log(f"Output size: {output_bytes} bytes", logf)
        log(f"Duration: {duration:.4f} sec", logf)

        metrics = {
            "input_file": input_path,
            "output_file": output_path,
            "metrics_file": metrics_path,
            "log_file": log_path,
            "input_bytes": input_bytes,
            "output_bytes": output_bytes,
            "input_lines": input_lines,
            "output_lines": output_lines,
            "bad_lines": bad_lines,
            "kept_elements": sorted(KEEP_ELEMENTS),
            "start_time": start_iso,
            "end_time": end_iso,
            "duration_sec": round(duration, 6)
        }

        with open(metrics_path, "w") as mf:
            json.dump(metrics, mf, indent=2)

        log("Metrics written successfully", logf)
        log("END", logf)


def main():
    if len(sys.argv) != 5:
        print("Usage: process_splits.py <input> <output> <metrics> <log>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    metrics_path = sys.argv[3]
    log_path = sys.argv[4]

    process_split(input_path, output_path, metrics_path, log_path)


if __name__ == "__main__":
    main()
