#!/usr/bin/env python3

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_monitor_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def collect_split_metrics(metrics_dir):
    split_files = []
    merge_file = None

    for name in sorted(os.listdir(metrics_dir)):
        if not name.endswith(".json"):
            continue
        full_path = os.path.join(metrics_dir, name)
        if name.startswith("merge"):
            merge_file = full_path
        else:
            split_files.append(full_path)

    split_metrics = [load_json(path) for path in split_files]
    merge_metrics = load_json(merge_file) if merge_file and os.path.exists(merge_file) else None

    return split_metrics, merge_metrics


def summarize_splits(split_metrics):
    if not split_metrics:
        return {
            "num_splits": 0,
            "total_split_duration_sec": 0.0,
            "avg_split_duration_sec": 0.0,
            "min_split_duration_sec": 0.0,
            "max_split_duration_sec": 0.0,
            "total_input_bytes": 0,
            "total_output_bytes": 0,
            "total_input_lines": 0,
            "total_output_lines": 0,
            "total_bad_lines": 0,
            "earliest_split_start": "",
            "latest_split_end": "",
        }

    durations = [safe_float(m.get("duration_sec", 0.0)) for m in split_metrics]
    input_bytes = [safe_int(m.get("input_bytes", 0)) for m in split_metrics]
    output_bytes = [safe_int(m.get("output_bytes", 0)) for m in split_metrics]
    input_lines = [safe_int(m.get("input_lines", 0)) for m in split_metrics]
    output_lines = [safe_int(m.get("output_lines", 0)) for m in split_metrics]
    bad_lines = [safe_int(m.get("bad_lines", 0)) for m in split_metrics]

    starts = sorted([m.get("start_time", "") for m in split_metrics if m.get("start_time")])
    ends = sorted([m.get("end_time", "") for m in split_metrics if m.get("end_time")])

    return {
        "num_splits": len(split_metrics),
        "total_split_duration_sec": round(sum(durations), 6),
        "avg_split_duration_sec": round(sum(durations) / len(durations), 6),
        "min_split_duration_sec": round(min(durations), 6),
        "max_split_duration_sec": round(max(durations), 6),
        "total_input_bytes": sum(input_bytes),
        "total_output_bytes": sum(output_bytes),
        "total_input_lines": sum(input_lines),
        "total_output_lines": sum(output_lines),
        "total_bad_lines": sum(bad_lines),
        "earliest_split_start": starts[0] if starts else "",
        "latest_split_end": ends[-1] if ends else "",
    }


def summarize_merge(merge_metrics):
    if not merge_metrics:
        return {
            "merge_duration_sec": 0.0,
            "merge_total_files": 0,
            "merge_total_input_bytes": 0,
            "merge_final_output_bytes": 0,
            "merge_total_lines": 0,
            "merge_start_time": "",
            "merge_end_time": "",
        }

    return {
        "merge_duration_sec": round(safe_float(merge_metrics.get("duration_sec", 0.0)), 6),
        "merge_total_files": safe_int(merge_metrics.get("total_files", 0)),
        "merge_total_input_bytes": safe_int(merge_metrics.get("total_input_bytes", 0)),
        "merge_final_output_bytes": safe_int(merge_metrics.get("final_output_bytes", 0)),
        "merge_total_lines": safe_int(merge_metrics.get("total_lines", 0)),
        "merge_start_time": merge_metrics.get("start_time", ""),
        "merge_end_time": merge_metrics.get("end_time", ""),
    }


def summarize_monitor(monitor_rows):
    if not monitor_rows:
        return {
            "monitor_samples": 0,
            "avg_cpu_percent": 0.0,
            "peak_cpu_percent": 0.0,
            "avg_mem_percent": 0.0,
            "peak_mem_percent": 0.0,
            "total_disk_read_bytes": 0,
            "total_disk_write_bytes": 0,
            "avg_load_avg_1min": 0.0,
        }

    cpu_vals = [safe_float(r.get("cpu_percent", 0.0)) for r in monitor_rows]
    mem_vals = [safe_float(r.get("mem_percent", 0.0)) for r in monitor_rows]
    read_vals = [safe_int(r.get("disk_read_bytes", 0)) for r in monitor_rows]
    write_vals = [safe_int(r.get("disk_write_bytes", 0)) for r in monitor_rows]
    load_vals = [safe_float(r.get("load_avg_1min", 0.0)) for r in monitor_rows]

    return {
        "monitor_samples": len(monitor_rows),
        "avg_cpu_percent": round(sum(cpu_vals) / len(cpu_vals), 6),
        "peak_cpu_percent": round(max(cpu_vals), 6),
        "avg_mem_percent": round(sum(mem_vals) / len(mem_vals), 6),
        "peak_mem_percent": round(max(mem_vals), 6),
        "total_disk_read_bytes": sum(read_vals),
        "total_disk_write_bytes": sum(write_vals),
        "avg_load_avg_1min": round(sum(load_vals) / len(load_vals), 6),
    }


def compute_estimated_workflow_runtime(split_summary, merge_summary):
    start_candidates = []
    end_candidates = []

    if split_summary.get("earliest_split_start"):
        start_candidates.append(split_summary["earliest_split_start"])
    if merge_summary.get("merge_start_time"):
        start_candidates.append(merge_summary["merge_start_time"])

    if split_summary.get("latest_split_end"):
        end_candidates.append(split_summary["latest_split_end"])
    if merge_summary.get("merge_end_time"):
        end_candidates.append(merge_summary["merge_end_time"])

    if not start_candidates or not end_candidates:
        return 0.0, "", ""

    overall_start = min(start_candidates)
    overall_end = max(end_candidates)

    try:
        t0 = datetime.fromisoformat(overall_start)
        t1 = datetime.fromisoformat(overall_end)
        duration = round((t1 - t0).total_seconds(), 6)
    except Exception:
        duration = 0.0

    return duration, overall_start, overall_end


def write_detailed_split_csv(split_metrics, output_csv, run_label):
    ensure_parent(output_csv)

    fieldnames = [
        "run_label",
        "input_file",
        "output_file",
        "metrics_file",
        "log_file",
        "input_bytes",
        "output_bytes",
        "input_lines",
        "output_lines",
        "bad_lines",
        "start_time",
        "end_time",
        "duration_sec",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for m in split_metrics:
            row = {k: m.get(k, "") for k in fieldnames}
            row["run_label"] = run_label
            writer.writerow(row)


def append_aggregated_csv(output_csv, row):
    ensure_parent(output_csv)

    fieldnames = list(row.keys())
    file_exists = os.path.exists(output_csv)

    with open(output_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    if len(sys.argv) != 8:
        print(
            "Usage: metrics.py <mode> <size> <run_label> <metrics_dir> <monitor_csv> <aggregated_csv> <detailed_split_csv>",
            file=sys.stderr,
        )
        sys.exit(1)

    mode = sys.argv[1]
    size = sys.argv[2]
    run_label = sys.argv[3]
    metrics_dir = sys.argv[4]
    monitor_csv = sys.argv[5]
    aggregated_csv = sys.argv[6]
    detailed_split_csv = sys.argv[7]

    split_metrics, merge_metrics = collect_split_metrics(metrics_dir)
    monitor_rows = read_monitor_csv(monitor_csv)

    split_summary = summarize_splits(split_metrics)
    merge_summary = summarize_merge(merge_metrics)
    monitor_summary = summarize_monitor(monitor_rows)

    workflow_runtime_sec, workflow_start, workflow_end = compute_estimated_workflow_runtime(
        split_summary, merge_summary
    )

    final_row = {
        "mode": mode,
        "size": size,
        "run_label": run_label,

        "num_splits": split_summary["num_splits"],
        "total_split_duration_sec": split_summary["total_split_duration_sec"],
        "avg_split_duration_sec": split_summary["avg_split_duration_sec"],
        "min_split_duration_sec": split_summary["min_split_duration_sec"],
        "max_split_duration_sec": split_summary["max_split_duration_sec"],

        "total_input_bytes": split_summary["total_input_bytes"],
        "total_output_bytes": split_summary["total_output_bytes"],
        "total_input_lines": split_summary["total_input_lines"],
        "total_output_lines": split_summary["total_output_lines"],
        "total_bad_lines": split_summary["total_bad_lines"],

        "merge_duration_sec": merge_summary["merge_duration_sec"],
        "merge_total_files": merge_summary["merge_total_files"],
        "merge_total_input_bytes": merge_summary["merge_total_input_bytes"],
        "merge_final_output_bytes": merge_summary["merge_final_output_bytes"],
        "merge_total_lines": merge_summary["merge_total_lines"],

        "monitor_samples": monitor_summary["monitor_samples"],
        "avg_cpu_percent": monitor_summary["avg_cpu_percent"],
        "peak_cpu_percent": monitor_summary["peak_cpu_percent"],
        "avg_mem_percent": monitor_summary["avg_mem_percent"],
        "peak_mem_percent": monitor_summary["peak_mem_percent"],
        "total_disk_read_bytes": monitor_summary["total_disk_read_bytes"],
        "total_disk_write_bytes": monitor_summary["total_disk_write_bytes"],
        "avg_load_avg_1min": monitor_summary["avg_load_avg_1min"],

        "estimated_workflow_runtime_sec": workflow_runtime_sec,
        "estimated_workflow_start": workflow_start,
        "estimated_workflow_end": workflow_end,
    }

    write_detailed_split_csv(split_metrics, detailed_split_csv, run_label)
    append_aggregated_csv(aggregated_csv, final_row)

    print(f"[COLLECT_METRICS] Detailed split CSV written to: {detailed_split_csv}")
    print(f"[COLLECT_METRICS] Aggregated row appended to: {aggregated_csv}")


if __name__ == "__main__":
    main()
