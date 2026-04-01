# SciPara IO Benchmark Guide

This document explains the execution outputs, run labeling, and where files are written for the `scipara_io_benchmark` workflow.

## Benchmark Structure

The benchmark has two phases:

1. Preprocessing
2. Execution / workflow runs

Preprocessing prepares reusable dataset artifacts for a size such as `100M`, `300M`, or `1g`.
Execution runs the benchmark for a specific mode such as `shell` or `sciunit`.

## Preprocessing Outputs

These files are shared benchmark assets. They are not currently run-labeled.

### Prepared Input

Location:
- `scipara_io_benchmark/data/prepared/<size>/input.txt`

Produced by:
- `scipara_io_benchmark/scripts/preprocess/prepare_dataset.py`

Contents:
- CSV-style weather rows in this format:
  - `station_id,date,element,value`

Purpose:
- This is the large prepared benchmark input that later gets split into smaller work units.

### Split Files

Location:
- `scipara_io_benchmark/data/splits/<size>/split_XXXX.txt`

Produced by:
- `scipara_io_benchmark/scripts/preprocess/create_splits.py`

Contents:
- A chunk of the prepared input file.
- Each file contains a subset of lines from `input.txt`.

Purpose:
- These are the unit inputs processed in parallel during execution.

### Manifest File

Location:
- `scipara_io_benchmark/data/manifests/splits_<size>.txt`

Produced by:
- `scipara_io_benchmark/scripts/preprocess/create_manifest.py`

Contents:
- One split path per line.

Purpose:
- Used as the complete list of split files for that dataset size.

### Batch Files

Location:
- `scipara_io_benchmark/batches/<size>/batch_XXX.txt`

Produced by:
- `scipara_io_benchmark/scripts/preprocess/create_batches.py`

Contents:
- One split path per line.
- Each batch file groups a subset of splits.

Purpose:
- Snakemake uses these batch files to schedule groups of split-processing tasks.

### Preprocessing Log

Location:
- `scipara_io_benchmark/logs/snakemake/preprocess/preprocessing.log`

Produced by:
- `scipara_io_benchmark/scripts/preprocess/run_preprocessing.py`
- helper logger in `scipara_io_benchmark/scripts/preprocess/logger.py`

Contents:
- Orchestration and progress messages for preprocessing.

## Execution Run Layout

Execution outputs are now isolated by run label.

General layout:

- `scipara_io_benchmark/results/snakemake/<run_label>/...`
- `scipara_io_benchmark/metrics/snakemake/<run_label>/...`
- `scipara_io_benchmark/logs/snakemake/<run_label>/...`

Example run label:
- `run_001_20260328_220114`

This means every workflow run gets its own directory tree and suffixed output files.

## Per-Split Processing Outputs

### Processed Split Output

Location:
- `scipara_io_benchmark/results/snakemake/<run_label>/<mode>/<size>/processed/split_XXXX_<run_label>.out`

Produced by:
- `scipara_io_benchmark/scripts/execution/process_splits.py`

Contents:
- Filtered weather rows.
- Only these elements are kept:
  - `TMAX`
  - `TMIN`
  - `PRCP`

Purpose:
- These are the per-split processed benchmark outputs.

### Per-Split Metrics JSON

Location:
- `scipara_io_benchmark/metrics/snakemake/<run_label>/raw/<mode>/<size>/split_XXXX_<run_label>.json`

Produced by:
- `scipara_io_benchmark/scripts/execution/process_splits.py`

Contents:
- Input path
- Output path
- Metrics path
- Log path
- Input bytes
- Output bytes
- Input lines
- Output lines
- Bad lines
- Kept elements
- Start time
- End time
- Duration

Purpose:
- Used by the metrics aggregation step to summarize the full run.

### Per-Split Rule Log

Location:
- `scipara_io_benchmark/logs/snakemake/<run_label>/rules/<mode>/<size>/split_XXXX_<run_label>.log`

Produced by:
- `scipara_io_benchmark/scripts/execution/process_splits.py`

Contents:
- Per-split progress and summary information such as line counts, bytes, bad lines, and duration.

## Batch-Level Outputs

### Batch Completion Marker

Location:
- `scipara_io_benchmark/results/snakemake/<run_label>/<mode>/<size>/batch_XXX_<run_label>.done`

Produced by:
- Snakemake `run_batch` rule

Contents:
- Empty marker file.

Purpose:
- Signals that a batch completed successfully.

### Batch Log

Location:
- `scipara_io_benchmark/logs/snakemake/<run_label>/batch/<mode>/<size>/batch_XXX_<run_label>.log`

Produced by:
- `scipara_io_benchmark/execution/shell/run_batch.sh`
- `scipara_io_benchmark/execution/sciunit/run_batch_sciunit.sh`

Contents:
- Batch start/end
- Run label
- Batch file path
- Processing script used
- Monitor start/stop information
- Split launch information

## Monitoring Outputs

### Per-Batch Monitor CSV

Location:
- `scipara_io_benchmark/logs/snakemake/<run_label>/monitor/<mode>_<size>_batch_XXX_<run_label>.csv`

Produced by:
- `scipara_io_benchmark/scripts/execution/monitor.py`

Contents:
- Header columns:
  - `timestamp`
  - `cpu_percent`
  - `mem_percent`
  - `disk_read_bytes`
  - `disk_write_bytes`
  - `load_avg_1min`

Purpose:
- Records system resource samples during batch execution.

### Combined Monitor CSV

Location:
- `scipara_io_benchmark/logs/snakemake/<run_label>/monitor/<mode>_<size>_<run_label>_combined.csv`

Produced by:
- Snakemake `combine_monitor_logs` rule

Contents:
- Concatenated per-batch monitor CSVs.
- If monitoring is disabled or no monitor files exist, a header-only CSV is created.

## Merge Outputs

### Final Merged Output

Location:
- `scipara_io_benchmark/results/snakemake/<run_label>/<mode>/<size>/final_output_<run_label>.txt`

Produced by:
- `scipara_io_benchmark/scripts/execution/merge_outputs.py`

Contents:
- Concatenation of all processed split output files for that run.

### Merge Log

Location:
- `scipara_io_benchmark/logs/snakemake/<run_label>/rules/<mode>/<size>/merge_<run_label>.log`

Produced by:
- `scipara_io_benchmark/scripts/execution/merge_outputs.py`

Contents:
- Files merged
- Bytes merged
- Total lines
- Duration
- Merge start/end timestamps

### Merge Metrics JSON

Location:
- `scipara_io_benchmark/metrics/snakemake/<run_label>/raw/<mode>/<size>/merge_<run_label>.json`

Produced by:
- `scipara_io_benchmark/scripts/execution/merge_outputs.py`

Contents:
- Input glob pattern
- Output file
- Log file
- Total files merged
- Total input bytes
- Final output bytes
- Total lines
- Start time
- End time
- Duration

## Aggregated Metrics Outputs

### Detailed Split CSV

Location:
- `scipara_io_benchmark/metrics/snakemake/<run_label>/aggregated/<mode>_<size>_<run_label>_splits.csv`

Produced by:
- `scipara_io_benchmark/scripts/execution/metrics.py`

Contents:
- One row per processed split
- Includes:
  - `run_label`
  - input file
  - output file
  - metrics file
  - log file
  - input bytes
  - output bytes
  - input lines
  - output lines
  - bad lines
  - start time
  - end time
  - duration

### Aggregated Results CSV

Location:
- `scipara_io_benchmark/metrics/snakemake/<run_label>/aggregated/results_<run_label>.csv`

Produced by:
- `scipara_io_benchmark/scripts/execution/metrics.py`

Contents:
- One aggregated row for the full run.
- Includes:
  - `mode`
  - `size`
  - `run_label`
  - split summary fields
  - merge summary fields
  - monitor summary fields
  - estimated workflow start/end/runtime

### Final Done Marker

Location:
- `scipara_io_benchmark/metrics/snakemake/<run_label>/aggregated/<mode>_<size>_<run_label>.done`

Produced by:
- Snakemake `collect_metrics` rule

Contents:
- Empty marker file.

Purpose:
- Signals that the full benchmark run has completed.

## SciUnit-Specific Output

In `sciunit` mode, the batch runner also creates a SciUnit project directory:

Location:
- `~/sciunit/project_<run_label>_<batch_id>`

Produced by:
- `scipara_io_benchmark/execution/sciunit/run_batch_sciunit.sh`

Purpose:
- Holds SciUnit execution state for that batch.

## Run Label Behavior

Run labels are controlled by:
- `scipara_io_benchmark/configs/global.yaml`
- `scipara_io_benchmark/workflows/snakemake/Snakefile`

### Available Settings

In `global.yaml`:

- `run_label`
  - optional exact full label
  - example: `run_001_20260328_120000`
- `run_number`
  - optional exact numeric portion
  - example: `1`
- `run_number_start`
  - minimum auto-generated run number
  - default: `1`

### Generation Rules

Priority order:

1. If `run_label` is set, that exact label is used.
2. Else if `run_number` is set, the label becomes `run_<NNN>_<timestamp>`.
3. Else the workflow scans existing run directories and picks the next number, with `run_number_start` as the floor.

### Practical Examples

Reset numbering after cleanup:

```yaml
run_label: ""
run_number: ""
run_number_start: 1
```

Force the next run to use number 1:

```yaml
run_label: ""
run_number: 1
run_number_start: 1
```

Force an exact custom label:

```yaml
run_label: run_001_manual_test
run_number: ""
run_number_start: 1
```
