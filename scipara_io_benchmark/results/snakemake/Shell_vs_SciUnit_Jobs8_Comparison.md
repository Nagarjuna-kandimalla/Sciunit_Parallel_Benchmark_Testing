# Shell vs SciUnit (`jobs: 8`) Comparison

## Scope

This note compares:

- shell baseline: `run_001_20260329_033941`
- SciUnit run with `jobs: 8`: `run_jobs_used8_003_20260330_062715`

The benchmark repository is:

- `/cluster/pixstor/data/nkmh5/Sciunit_Parallel_Benchmark_Testing/scipara_io_benchmark`


## Important Workflow Clarification

In this workflow, SciUnit is **not** used for the merge step.

From the Snakemake workflow:

- `run_batch` is the only stage that switches between shell and SciUnit
- in SciUnit mode, `run_batch_sciunit.sh` runs `sciunit2 parallel_exec` around `process_splits.py`
- `merge_outputs` still runs the merge script directly with plain Python
- `collect_metrics` also runs directly with plain Python

So this comparison should be interpreted as:

- shell processing of split files
vs
- SciUnit-wrapped processing of split files

The merge stage is shared infrastructure, not a SciUnit-specific phase.


## Output Correctness

Both runs completed the full workload successfully.

Shared outcome:

- `175` splits processed
- same total input bytes: `1,073,741,839`
- same total output bytes: `963,136,156`
- same total input lines: `34,959,739`
- same total output lines: `31,468,248`
- no bad lines observed

Interpretation:

- the shell and SciUnit `jobs: 8` runs are functionally equivalent for this dataset
- the difference is performance and resource behavior, not correctness


## Main Metrics

### Shell baseline

Run:

- `run_001_20260329_033941`

Summary:

- total split duration: `23.222153 s`
- average split duration: `0.132698 s`
- min split duration: `0.100595 s`
- max split duration: `0.201511 s`
- merge duration: `5.021927 s`
- average CPU: `82.717143%`
- peak CPU: `90.6%`
- average memory: `6.085714%`
- peak memory: `7.0%`
- total sampled disk read bytes: `126,976`
- total sampled disk write bytes: `106,496`

Fastest and slowest split:

- fastest: `split_0175.txt` at `0.100595 s`
- slowest: `split_0067.txt` at `0.201511 s`


### SciUnit `jobs: 8`

Run:

- `run_jobs_used8_003_20260330_062715`

Summary:

- total split duration: `32.85654 s`
- average split duration: `0.187752 s`
- min split duration: `0.120023 s`
- max split duration: `0.389586 s`
- merge duration: `4.55879 s`
- average CPU: `40.744872%`
- peak CPU: `51.6%`
- average memory: `19.276923%`
- peak memory: `19.6%`
- total sampled disk read bytes: `9,867,264`
- total sampled disk write bytes: `13,034,776,576`

Fastest and slowest split:

- fastest: `split_0175.txt` at `0.120023 s`
- slowest: `split_0119.txt` at `0.389586 s`


## Direct Comparison

| Metric | Shell | SciUnit (`jobs: 8`) | Interpretation |
| --- | --- | --- | --- |
| Splits completed | 175 | 175 | Both completed the full dataset |
| Total split duration (s) | 23.222153 | 32.85654 | SciUnit spent more total time in split processing |
| Avg split duration (s) | 0.132698 | 0.187752 | SciUnit average split time was about 41% higher |
| Min split duration (s) | 0.100595 | 0.120023 | SciUnit best-case split is still slower |
| Max split duration (s) | 0.201511 | 0.389586 | SciUnit worst-case split is much slower |
| Merge duration (s) | 5.021927 | 4.55879 | Merge is similar, and not a SciUnit-specific phase |
| Avg CPU (%) | 82.717143 | 40.744872 | SciUnit shows much lower sampled CPU usage in this successful run |
| Avg memory (%) | 6.085714 | 19.276923 | SciUnit uses much more memory |
| Total sampled disk read bytes | 126,976 | 9,867,264 | SciUnit shows much more read activity |
| Total sampled disk write bytes | 106,496 | 13,034,776,576 | SciUnit shows dramatically more write activity |


## Analysis

### 1. Split-processing overhead remains clearly visible

The most important comparison is the split stage, because that is the stage SciUnit actually wraps.

On that phase:

- SciUnit is slower on average
- SciUnit has a slower best case
- SciUnit has a much slower tail

This indicates that the SciUnit capture/packaging path adds measurable overhead even when the run succeeds cleanly.


### 2. Merge should not be used as evidence for SciUnit overhead

The merge stage is not run through SciUnit in this workflow.

So the fact that:

- shell merge = `5.021927 s`
- SciUnit-run merge = `4.55879 s`

should not be used as evidence for or against SciUnit overhead.


### 3. Resource usage is much heavier under SciUnit

The strongest difference is in memory and I/O:

- memory is roughly `3x` the shell baseline
- sampled disk writes are enormously larger under SciUnit
- sampled disk reads are also much larger under SciUnit

This is consistent with SciUnit’s extra capture/package/project-management activity.


### 4. CPU interpretation 

This successful `jobs: 8` SciUnit run shows lower sampled CPU than the shell baseline.

That does not change the main result that SciUnit still shows higher split-processing time and heavier memory and I/O usage.


## Practical Conclusion

For this workload:

- shell remains the lighter and faster execution path
- but SciUnit still imposes clear per-split overhead
- SciUnit also drives much heavier memory and disk activity than shell
- Sciunit is still more expensive than shell in both runtime overhead and storage-related activity

## Source Files

- `metrics/snakemake/run_001_20260329_033941/aggregated/results_run_001_20260329_033941.csv`
- `metrics/snakemake/run_001_20260329_033941/aggregated/shell_1g_run_001_20260329_033941_splits.csv`
- `metrics/snakemake/run_jobs_used8_003_20260330_062715/aggregated/results_run_jobs_used8_003_20260330_062715.csv`
- `metrics/snakemake/run_jobs_used8_003_20260330_062715/aggregated/sciunit_1g_run_jobs_used8_003_20260330_062715_splits.csv`
