#!/usr/bin/env python3

import glob
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def log(msg, logfile):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logfile.write(f"[{timestamp}] {msg}\n")
    logfile.flush()


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def merge_files(input_pattern, output_file, log_file, metrics_file):

    ensure_parent(output_file)
    ensure_parent(log_file)
    ensure_parent(metrics_file)

    with open(log_file, "w") as logf:

        log(f"START merge step", logf)
        log(f"Input pattern: {input_pattern}", logf)

        start_time = time.time()
        start_iso = datetime.now().isoformat()

        files = sorted(glob.glob(input_pattern))

        if not files:
            log("ERROR: No input files found!", logf)
            sys.exit(1)

        log(f"Total files to merge: {len(files)}", logf)

        total_lines = 0
        total_input_bytes = 0

        with open(output_file, "w", encoding="utf-8") as fout:

            for idx, file in enumerate(files, 1):

                try:
                    file_size = os.path.getsize(file)
                    total_input_bytes += file_size

                    log(f"Merging {idx}/{len(files)}: {file} ({file_size} bytes)", logf)

                    with open(file, "r", encoding="utf-8", errors="replace") as fin:
                        for line in fin:
                            fout.write(line)
                            total_lines += 1

                except Exception as e:
                    log(f"ERROR processing file {file}: {str(e)}", logf)
                    continue

                if idx % 10 == 0:
                    log(f"Progress: {idx} files merged", logf)

        end_time = time.time()
        end_iso = datetime.now().isoformat()
        duration = end_time - start_time

        final_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0

        log("Merge completed successfully", logf)
        log(f"Total lines written: {total_lines}", logf)
        log(f"Total input bytes: {total_input_bytes}", logf)
        log(f"Final output size: {final_size}", logf)
        log(f"Duration: {duration:.4f} sec", logf)

        #  Metrics JSON
        metrics = {
            "step": "merge",
            "input_pattern": input_pattern,
            "output_file": output_file,
            "log_file": log_file,
            "total_files": len(files),
            "total_input_bytes": total_input_bytes,
            "final_output_bytes": final_size,
            "total_lines": total_lines,
            "start_time": start_iso,
            "end_time": end_iso,
            "duration_sec": round(duration, 6)
        }

        with open(metrics_file, "w") as mf:
            json.dump(metrics, mf, indent=2)

        log("Metrics written successfully", logf)
        log("END", logf)


def main():
    if len(sys.argv) != 5:
        print("Usage: merge_outputs.py <input_pattern> <output_file> <log_file> <metrics_file>")
        sys.exit(1)

    input_pattern = sys.argv[1]
    output_file = sys.argv[2]
    log_file = sys.argv[3]
    metrics_file = sys.argv[4]

    merge_files(input_pattern, output_file, log_file, metrics_file)


if __name__ == "__main__":
    main()
