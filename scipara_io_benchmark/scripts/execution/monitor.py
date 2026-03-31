#!/usr/bin/env python3

import csv
import psutil
import signal
import sys
import time
from datetime import datetime
from pathlib import Path


STOP_REQUESTED = False


def request_stop(signum, frame):
    del signum, frame
    global STOP_REQUESTED
    STOP_REQUESTED = True


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def monitor(output_file, interval=1):
    global STOP_REQUESTED
    STOP_REQUESTED = False

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    ensure_parent(output_file)

    print(f"[MONITOR] Writing to {output_file}")
    print(f"[MONITOR] Interval: {interval}s")

    prev_disk = psutil.disk_io_counters()

    with open(output_file, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)
        writer.writerow([
            "timestamp",
            "cpu_percent",
            "mem_percent",
            "disk_read_bytes",
            "disk_write_bytes",
            "load_avg_1min"
        ])

        while not STOP_REQUESTED:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent

            disk = psutil.disk_io_counters()

            read_bytes = disk.read_bytes - prev_disk.read_bytes
            write_bytes = disk.write_bytes - prev_disk.write_bytes

            prev_disk = disk

            load1, _, _ = psutil.getloadavg()

            writer.writerow([
                timestamp,
                cpu,
                mem,
                read_bytes,
                write_bytes,
                load1
            ])

            csvfile.flush()
            time.sleep(interval)

    print("[MONITOR] Stopped.")


def main():
    if len(sys.argv) != 2:
        print("Usage: monitor.py <output_csv>")
        sys.exit(1)

    output_file = sys.argv[1]

    monitor(output_file)


if __name__ == "__main__":
    main()
