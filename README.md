# Sciunit_Parallel_Benchmark_Testing

This repository contains the `scipara_io_benchmark` workflow used to benchmark split-based file processing in two modes:

- `shell`
- `sciunit -parallel`

The benchmark prepares a weather dataset, splits it into many files, groups those files into batches, processes the batches in parallel through Snakemake + Slurm (shell and sciunit mode execution), merges the processed outputs, and aggregates metrics.

## Repository Layout

### Top level

- [scipara_io_benchmark](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark)
  Main benchmark project. This is the directory most users will work in.

- [SCIPARA_BENCHMARK_GUIDE.md](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/SCIPARA_BENCHMARK_GUIDE.md)
  Output-focused guide. Explains where run-labeled results, metrics, and logs are written.

- [Lock_Issue_Patch.md](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/Lock_Issue_Patch.md)
  Detailed write-up of the SciUnit locking and project-selection fixes.

- [Shell_vs_SciUnit_Jobs8_Comparison.md](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/results/snakemake/Shell_vs_SciUnit_Jobs8_Comparison.md)
  Focused shell vs SciUnit comparison for the successful `jobs: 8` case.

### Main benchmark folder

Inside [scipara_io_benchmark](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark):

- [configs](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/configs)
  Global benchmark configuration such as execution mode, dataset size, run labels, script paths, and monitoring.

- [workflows](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/workflows)
  Snakemake workflow definition and Slurm executor profile.

- [scripts](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/scripts)
  Python scripts for data preprocessing, per-split processing, merging, monitoring, and metrics aggregation.

- [execution](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/execution)
  Batch wrapper scripts used by Snakemake.

## Common Benchmark Data and Shared Assets

These paths are benchmark assets or benchmark outputs that are useful regardless of which workflow engine is used to run the benchmark.

- Raw upstream dataset source:
  - `https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd_all.tar.gz`
  - size is approximately `30 GB`

- For quick reference in git, the repo intentionally includes a small tracked sample set centered on `1g` batch `013`:
  - `data/raw/ghcnd-version.txt`
  - `data/manifests/splits_1g.txt`
  - `data/splits/1g/split_0061.txt`
  - `data/splits/1g/split_0062.txt`
  - `batches/1g/batch_013.txt`

- The repo also includes a small tracked result sample set for:
  - shell run `run_001_20260329_033941`
  - SciUnit `jobs: 8` run `run_jobs_used8_003_20260330_062715`
  These tracked samples cover representative per-split outputs, raw metrics JSONs, per-split logs, batch logs, monitor CSVs, merge artifacts, and aggregated CSV summaries for `split_0061`, `split_0062`, and `batch_013`.

- Final merged output comparison:
  - shell final output and SciUnit `jobs: 8` final output are identical
  - `cmp` returned `0`
  - both files have SHA-256:
    - `d8c35047f6eab063960537c93782c4bef15a2655828489933a6a4a598d2cf9f2`

- [data](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/data)
  Raw input, prepared input, split files, and manifests.

- [batches](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/batches)
  Batch files. Each `batch_XXX.txt` contains a group of split paths.

- [results](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/results)
  Processed outputs and final merged outputs, organized by backend wrapper and run label.

- [metrics](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/metrics)
  Raw per-split metrics, merge metrics, and aggregated CSV summaries, organized by backend wrapper and run label.

- [logs](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/logs)
  Preprocessing logs, batch logs, rule logs, and monitor CSVs, organized by backend wrapper and run label.

- [repeat_temp](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/repeat_temp)
  Temporary space used during manual replay experiments.

## Important Source Files

### Configuration

- [configs/global.yaml](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/configs/global.yaml)
  Main benchmark settings.

- [workflows/snakemake/profile/config.yaml](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/workflows/snakemake/profile/config.yaml)
  Slurm executor profile with:
  - `jobs`
  - `slurm_partition`
  - `mem_mb`
  - `runtime`
  - `cpus_per_task`

### Workflow

- [workflows/snakemake/Snakefile](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/workflows/snakemake/Snakefile)
  Main workflow entry point.

The Snakemake workflow has these main stages:

1. `run_batch`
2. `merge_outputs`
3. `combine_monitor_logs`
4. `collect_metrics`
5. `all`

### Preprocessing scripts

- [scripts/preprocess/run_preprocessing.py](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/scripts/preprocess/run_preprocessing.py)
  Runs the whole preprocessing sequence.

- `prepare_dataset.py`
  Creates the prepared dataset.

- `create_splits.py`
  Creates `split_XXXX.txt` files.

- `create_manifest.py`
  Writes the split manifest.

- `create_batches.py`
  Groups split files into batch files.

### Execution scripts

- [scripts/execution/process_splits.py](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/scripts/execution/process_splits.py)
  Core per-split processing script.

- [scripts/execution/merge_outputs.py](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/scripts/execution/merge_outputs.py)
  Merges processed split outputs.

- [scripts/execution/metrics.py](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/scripts/execution/metrics.py)
  Aggregates raw metrics and monitor logs into summary CSVs.

- [scripts/execution/monitor.py](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/scripts/execution/monitor.py)
  Records CPU, memory, disk, and load samples during batch execution.

### Batch wrappers

- [execution/common/env_setup.sh](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/execution/common/env_setup.sh)
  Shared HPC environment setup. It purges modules, loads Python, activates the benchmark venv, checks SciUnit, checks GNU Parallel, and prints node info.

- [execution/shell/run_batch.sh](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/execution/shell/run_batch.sh)
  Shell-mode batch runner.

- [execution/sciunit/run_batch_sciunit.sh](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/execution/sciunit/run_batch_sciunit.sh)
  SciUnit-mode batch runner.

## SciUnit Runtime Project File

Each SciUnit batch creates a project named like:

- `project_<run_label>_batch_013`

## Workflow Execution Backends

This repository is intended to support multiple workflow engines over time. The benchmark data and benchmark output layout are shared, but the launcher and workflow-state details can differ by backend.

Planned or possible backend sections:

- Snakemake + Slurm
- Makeflow
- Pegasus
- Nextflow

At present, the implemented and documented backend is Snakemake + Slurm.

### Snakemake-Specific Workflow State

- [.snakemake](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/.snakemake)
  Workflow-local Snakemake state, controller logs, locks, and Slurm wrapper logs.

### Snakemake + Slurm: End-to-End HPC Execution

#### 1. Go to the benchmark folder

```bash
cd /cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark
```

#### 2. Prepare the Python environment for preprocessing

```bash
module purge
module load python/3.13.3 || module load python/3.10
source /cluster/pixstor/data/nkmh5/parasci/bin/activate
python --version
```

#### 3. Run preprocessing

Example for `1 GB`:

```bash
python scripts/preprocess/run_preprocessing.py --size_gb 1
```

This generates:

- `data/prepared/1g/input.txt`
- `data/splits/1g/split_XXXX.txt`
- `data/manifests/splits_1g.txt`
- `batches/1g/batch_XXX.txt`
- `logs/snakemake/preprocess/preprocessing.log`

#### 4. Set workflow configuration

Edit these files before launching the main workflow:

- [configs/global.yaml](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/configs/global.yaml)
- [workflows/snakemake/profile/config.yaml](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/workflows/snakemake/profile/config.yaml)

Key fields in `global.yaml`:

- `mode: shell` or `mode: sciunit`
- `dataset_size`
- `tasks_per_batch`
- optional `run_label`
- optional `run_number`

Key fields in the Slurm profile:

- `jobs`
- `slurm_partition`
- `mem_mb`
- `runtime`
- `cpus_per_task`

#### 5. Launch Snakemake on Slurm

```bash
module load snakemake
snakemake --unlock --snakefile workflows/snakemake/Snakefile --profile workflows/snakemake/profile --configfile configs/global.yaml
snakemake -n --snakefile workflows/snakemake/Snakefile --profile workflows/snakemake/profile --configfile configs/global.yaml
snakemake --snakefile workflows/snakemake/Snakefile --profile workflows/snakemake/profile --configfile configs/global.yaml
```

What these commands do:

- `--unlock`
  Clears stale Snakemake locks from earlier interrupted runs.

- `-n`
  Performs a dry-run to verify the DAG and resolved config.

- final `snakemake`
  Submits the real workflow through the Slurm executor plugin.

### Snakemake + Slurm: What Happens During a Normal Run

For a typical `1g` run:

1. Snakemake submits one `run_batch` job per batch file.
2. Each batch writes its own processed outputs, raw metrics, logs, and monitor CSV.
3. After all batches finish, Snakemake runs:
   - `merge_outputs`
   - `combine_monitor_logs`
   - `collect_metrics`
4. The `all` rule completes when the final aggregated `.done` file exists.

In SciUnit mode, each batch job:

1. runs `env_setup.sh`
2. creates a fresh SciUnit project
3. calls `python -m sciunit2 parallel_exec ...`
4. stores SciUnit provenance in the SciUnit workspace

In shell mode, each batch job:

1. runs `env_setup.sh`
2. launches `process_splits.py` directly for each split in the batch
3. writes the same benchmark outputs, but without SciUnit project/provenance state

### Snakemake + Slurm: What Success Looks Like

#### Snakemake controller log

Main controller log location:

- `scipara_io_benchmark/.snakemake/log/<timestamp>.snakemake.log`

A healthy run typically shows:

- `Job X has been submitted with SLURM jobid ...`
- `Finished job X.`
- `Touching output file ... batch_XXX_<run_label>.done`
- `Finished job 38.`
- `Finished job 2.`
- `Finished job 1.`
- `39 of 39 steps (100%) done`
- `Complete log: .snakemake/log/...`

Real successful completion pattern:

```text
Finished job 1.
38 of 39 steps (97%) done
...
Finished job 0.
39 of 39 steps (100%) done
Complete log: .snakemake/log/2026-03-30T062715.073102.snakemake.log
```

#### Batch log

Batch log location:

- `logs/snakemake/<run_label>/batch/<mode>/<size>/batch_XXX_<run_label>.log`

Typical healthy SciUnit batch log:

```text
[START] Batch: batch_013 (Sciunit)
[INFO] Mode: sciunit | Size: 1g
[INFO] Run label: run_jobs_used8_003_20260330_062715
[INFO] Batch file: .../batches/1g/batch_013.txt
[INFO] Process script: scripts/execution/process_splits.py
[INFO] Sciunit project: project_run_jobs_used8_003_20260330_062715_batch_013
[INFO] Launching Sciunit parallel tasks...
[INFO] Creating fresh Sciunit project...
Opened empty sciunit at /home/nkmh5/sciunit/project_run_jobs_used8_003_20260330_062715_batch_013
[END] Batch: batch_013 completed (Sciunit)
```

#### Files you should see after success

For a completed run label `<run_label>`:

- `results/snakemake/<run_label>/<mode>/<size>/processed/*.out`
- `results/snakemake/<run_label>/<mode>/<size>/final_output_<run_label>.txt`
- `metrics/snakemake/<run_label>/raw/<mode>/<size>/*.json`
- `metrics/snakemake/<run_label>/aggregated/results_<run_label>.csv`
- `metrics/snakemake/<run_label>/aggregated/<mode>_<size>_<run_label>_splits.csv`
- `logs/snakemake/<run_label>/batch/...`
- `logs/snakemake/<run_label>/rules/...`
- `logs/snakemake/<run_label>/monitor/...`

In SciUnit mode, you should also see fresh projects under:

- `/cluster/pixstor/data/nkmh5/sciunit`

### Snakemake + Slurm: What Failure Looks Like

#### In the Snakemake controller log

When a job fails, the controller log usually:

- stops before `100%`
- reports that a rule failed
- points you to a wrapper log under:
  - `scipara_io_benchmark/.snakemake/slurm_logs/...`

Typical failure behavior:

1. some batch jobs are submitted
2. some jobs finish successfully
3. one job fails
4. Snakemake exits nonzero and stops normal forward progress

#### Where to inspect first

Check in this order:

1. `scipara_io_benchmark/.snakemake/log/<timestamp>.snakemake.log`
2. `scipara_io_benchmark/.snakemake/slurm_logs/...`
3. `logs/snakemake/<run_label>/batch/<mode>/<size>/batch_XXX_<run_label>.log`
4. `logs/snakemake/<run_label>/rules/<mode>/<size>/split_XXXX_<run_label>.log`

#### Common failure patterns observed in this repo

These are examples from real benchmark debugging:

- `missing cde.options file`
- `cde.log: No such file or directory`
- `execution 'eX' already exists`
- `unable to open database file`
- `disk I/O error`
- `Disk quota exceeded`

Practical interpretation:

- `missing cde.options file` and missing `cde.log`
  often indicate incomplete SciUnit/CDE package construction during capture

- `execution 'eX' already exists`
  indicates a SciUnit execution metadata/package conflict inside a project

- `unable to open database file` and `disk I/O error`
  point to filesystem or SQLite pressure in the SciUnit workspace

## Recommended First-Time Workflow

If you are new to the repo, use this order:

1. Read this README.
2. Check [SCIPARA_BENCHMARK_GUIDE.md](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/SCIPARA_BENCHMARK_GUIDE.md) for output paths.
3. Edit [configs/global.yaml](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/configs/global.yaml) and [config.yaml](/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark/workflows/snakemake/profile/config.yaml).
4. Run preprocessing.
5. Run `snakemake --unlock`.
6. Run `snakemake -n`.
7. Launch the real Snakemake workflow.
8. Inspect `.snakemake/log/...` first if something goes wrong.
