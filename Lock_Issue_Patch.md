# Lock Issue Patch

## Purpose

This note documents the two concurrency issues I observed while running `parallel-sciunit`, why they were intermittent, what I changed to fix them, and what results I obtained after the fixes.

The main point is that there were **two different race conditions**:

1. a **same-project write race** inside one SciUnit project
2. a **wrong-project context race** across multiple SciUnit projects running at the same time

Both had to be fixed.

---

## 1. Short Summary

### What was happening

SciUnit parallel workers were trying to update shared project state at nearly the same time. In some runs this caused:

- `database is locked`
- `execution 'eX' already exists`

In the larger benchmark workflow, a second problem appeared: different Slurm batches were creating different SciUnit projects, but SciUnit still used one shared `~/sciunit/.activated` file to decide the "current" project. That allowed one batch to accidentally redirect another batch's workers into the wrong project.

### Why it was intermittent

This was not a syntax problem. It was a timing problem.

If jobs finished with enough time gap between them, the race did not trigger.
If several workers reached the same shared update step at nearly the same time, the race triggered.

This is why:

- some local runs worked
- some cluster runs worked
- the full SciUnit Snakemake workflow failed reliably before the patch

### What I changed

I made two fixes:

1. **Fine-grained locking inside one project**
   - reserve execution IDs one at a time
   - keep `capture()` parallel
   - commit metadata one at a time

2. **Internal scoped project binding across multiple projects**
   - SciUnit now remembers the active project per launcher context
   - `parallel_exec` binds child workers to one resolved project path
   - workers no longer rely only on one shared global `.activated` pointer during concurrent execution

### What happened after the fixes

- The old equal-time reproducer `sciunit parallel_exec python test.py ::: 1 1 1 1` completed successfully.
- A real single SciUnit benchmark batch completed successfully.
- The hybrid verification of the full SciUnit Snakemake workflow completed successfully with one consistent run:
  - `run_004_20260329_182227`
- After the final internal-only scoped-activation change, a fresh clean rerun showed that the wrong-project race was gone, but one separate CDE package-construction failure still remained in `batch_014`.

---

## 2. Why This Was Hard To Notice

The bug was intermittent because concurrency bugs depend on timing.

If four workers finish at slightly different times, the shared writes may happen one after another, and the run appears healthy.
If they finish together, or if two batches create and use projects almost simultaneously, the hidden race appears.

This explains all of the observations I had:

- the local machine run succeeded
- some direct cluster tests succeeded
- the equal-time test `1 1 1 1` reproduced the issue more clearly
- the full Snakemake SciUnit workflow failed in parallel mode before the patch

This also explains why a failure in one environment does **not** mean the command is wrong. It means the design was unsafe under concurrency.

---

## 3. Issue 1: Same-Project Lock Race

### 3.1 Simple Explanation

Think of one SciUnit project as one shared office desk.

Each worker does three things:

1. ask the desk for a new execution ID like `e1`, `e2`
2. do the actual work and create its package
3. come back to the desk and file the final record

The important point is:

- Step 2 is independent and should happen in parallel.
- Steps 1 and 3 touch shared project state.

Before the patch, several workers could reach those shared steps almost together.
That caused collisions such as:

- two workers trying to reserve the next ID at nearly the same time
- two workers trying to commit metadata at nearly the same time

That is why errors like `database is locked` or `execution 'e4' already exists` appeared.

### 3.2 Example

The simplest example was:

```bash
sciunit parallel_exec python test.py ::: 1 1 1 1
```

All four `test.py` workers sleep for exactly one second. So they finish almost together.

That means they all return to the "desk" at almost the same time.
Before the patch, that made the race much easier to trigger.

### 3.3 Technical Explanation

The technical flow before the patch was:

1. `parallel_exec` launched multiple `sciunit exec ...` child processes.
2. Each child entered `ExecCommand.run()`.
3. Each child reserved an execution row in SQLite.
4. Each child ran `capture()`.
5. Each child committed package and metadata.

The problem was that the code structure used a broad `with emgr.exclusive():`, but `exclusive()` in `ExecutionManager` was not a real inter-process lock.

Relevant code:

- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/command/exec_/__init__.py:30-42`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/records.py:107-110`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/records.py:117-129`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/records.py:138-161`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/version_control.py:26-51`

In particular:

- `records.py:107-110` shows `exclusive()` returning `closing(self)`, not a true process-safe file lock
- `records.py:117-129` reserves the new execution row
- `records.py:138-161` commits the metadata update
- `version_control.py:26-51` runs the `vv commit` package-store commit

So the broad lock scope was conceptually too large, but the real issue was worse: the lock was not actually protecting concurrent processes.

### 3.4 What Failed Before The Patch

Observed failures included:

- `sciunit: exec: b'ERROR: database is locked\n'`
- `sciunit: exec: execution 'e4' already exists`
- `sciunit: exec: execution 'e2' already exists`

These were seen in direct SciUnit tests and later inside the SciUnit Snakemake batch logs.

---

## 4. Fix 1: Fine-Grained Locking Inside One Project

### 4.1 Simple Explanation

I changed the workflow from:

```text
lock everything
  reserve ID
  run capture
  commit results
unlock
```

to:

```text
lock
  reserve ID
unlock

run capture in parallel

lock
  commit results
unlock
```

This design is right because:

- the expensive work still runs in parallel
- only the short shared bookkeeping steps are serialized

### 4.2 Technical Explanation

I introduced a project lock file `.exec.lock` and used it only around the shared project updates.

The changes were:

1. `FileLock` became usable as a context manager.
2. `ExecCommand.run()` now locks only around `emgr.add(args)`.
3. `capture()` remains outside the lock.
4. `CommitMixin.do_commit()` now locks around:
   - `repo.checkin(...)`
   - `emgr.commit(...)`
5. SQLite connection timeout was increased to reduce short transient failures.

Relevant patched code:

- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/filelock.py`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/command/exec_/__init__.py:30-42`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/command/mixin.py:17-24`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/records.py:88-101`

Key lines:

- `exec_/__init__.py:31-33`
  - reserve execution ID under `.exec.lock`
- `exec_/__init__.py:35-41`
  - run capture outside the lock
- `mixin.py:18-24`
  - commit package and metadata under `.exec.lock`
- `records.py:88`
  - `sqlite3.connect(..., timeout=30)`

### 4.3 Result After Fix 1

The old equal-time reproducer succeeded:

```bash
sciunit parallel_exec python test.py ::: 1 1 1 1
```

Observed successful result:

- all four workers completed
- no `database is locked`
- no duplicate execution ID errors
- all four executions were registered in the SciUnit project

This confirmed that the first race condition was fixed.

---

## 5. Issue 2: Wrong-Project Context Race

### 5.1 Simple Explanation

The second issue is different.

Here, the problem was not only "workers collide in one project."
The problem was also "workers from one batch can accidentally start using another batch's project."

Think of it like this:

- Batch 1 creates Folder 1.
- Batch 2 creates Folder 2.
- There is one shared sticky note on the wall saying "current folder = X".

Now suppose:

1. Batch 1 writes the sticky note: `current folder = Folder 1`
2. two workers from Batch 1 start using Folder 1
3. Batch 2 starts a little later and rewrites the sticky note:
   `current folder = Folder 2`
4. the remaining workers from Batch 1 ask, "what is the current folder?"
5. they are told "Folder 2"
6. now those later workers write to the wrong project

That is exactly what happened in the full concurrent workflow.

### 5.2 Why It Did Not Show Up In Small Tests

This second issue usually does **not** appear if only one SciUnit project is active at a time.

That is why:

- a direct single-project test can pass
- a single batch can pass
- the full Snakemake workflow with many concurrent batches can still fail

### 5.3 Technical Explanation

SciUnit determines the active project in `workspace.at()`.

Relevant code:

- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/workspace.py:169-188`

Before the second patch, `at()` always read:

```text
~/sciunit/.activated
```

Then commands like:

- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/command/exec_/__init__.py:30`
- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/command/parallel_exec.py`

called:

```python
sciunit2.workspace.current()
```

which used `at()`.

So project selection depended on one shared global mutable file.

### 5.4 Technical Example

Suppose two concurrent Slurm batches run:

- Batch 005 creates:
  - `/home/nkmh5/sciunit/project_run_X_batch_005`
- Batch 014 creates:
  - `/home/nkmh5/sciunit/project_run_X_batch_014`

Each batch did:

```bash
python -m sciunit2 create -f "$SCIUNIT_PROJECT_NAME"
python -m sciunit2 parallel_exec ...
```

`create` updated the shared file:

```text
/home/nkmh5/sciunit/.activated
```

The race was:

1. Batch 005 set `.activated` to `project_run_X_batch_005`
2. some Batch 005 workers started
3. Batch 014 set `.activated` to `project_run_X_batch_014`
4. a later worker from Batch 005 called `workspace.current()`
5. it now saw Batch 014's project
6. it reserved/committed execution records in the wrong project

This explains why i observed:

- `batch_005` logs showing SciUnit project names from `batch_014`
- execution IDs larger than expected inside a 5-task batch
- duplicate execution ID errors that did not fit the batch size

In other words, this was **project cross-contamination**.

### 5.5 Real Failure Evidence

Before the second fix, the failed SciUnit workflow run:

- `run_002_20260329_040338`

showed failures in Snakemake wrapper logs such as:

- `.snakemake/slurm_logs/rule_run_batch/005/12942024.log`
- `.snakemake/slurm_logs/rule_run_batch/014/12942025.log`

The failure pattern was:

- `database is locked`
- `execution 'eX' already exists`
- mixed project names appearing in the wrong batch logs

This was the clue that the problem was no longer only "same project locking." The active project pointer itself was being switched by concurrent batches.

---

## 6. Fix 2: Internal Scoped Project Binding

### 6.1 Simple Explanation

The fix is simple in concept:

- stop relying only on one shared sticky note for "current project"
- let SciUnit remember which project belongs to the current launcher context
- once `parallel_exec` starts, tell every child worker its exact project path directly

That means:

- Batch 005 workers are explicitly told to use:
  - `/home/nkmh5/sciunit/project_run_..._batch_005`
- Batch 014 workers are explicitly told to use:
  - `/home/nkmh5/sciunit/project_run_..._batch_014`

So even if another batch starts later, the existing workers do not switch.

### 6.2 Technical Explanation

The second fix now has two internal parts, plus one optional advanced override that remains supported.

#### Part A: SciUnit now records scoped activation internally

I changed:

- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/workspace.py`

so that SciUnit does not rely only on:

```text
~/sciunit/.activated
```

It now also keeps a scoped activation record in:

```text
~/sciunit/.activated.d/<scope_key>
```

The scope key is derived from:

- parent process ID
- parent process start time
- current working directory

This lets SciUnit distinguish different launcher contexts without depending on Slurm-specific IDs.

Project resolution precedence is now:

1. explicit project override, if intentionally provided
2. scoped activation for the current launcher context
3. shared `.activated` fallback

#### Part B: `parallel_exec` now binds children to one resolved project

I changed:

- `/cluster/pixstor/data/nkmh5/parallel-sciunit/sciunit2/command/parallel_exec.py:30-42`

so that the parent `parallel_exec` process:

1. resolves the project once
2. copies the environment
3. sets:

```python
env['SCIUNIT_PROJECT_PATH'] = repo.location
```

4. launches GNU Parallel with that environment

So all child `sciunit exec` workers inherit the same exact project path.

#### Part C: explicit override remains available, but normal workflows do not need it

`SCIUNIT_PROJECT_PATH` support is still present as an advanced override.

That is useful for debugging or unusual launchers, but after the scoped-activation change it is no longer required for the normal benchmark flow.

### 6.3 Why This Is The Right Design

This is a more universal concurrency fix because project identity is no longer inferred only from one shared mutable global file during parallel execution.

Instead:

- SciUnit remembers project identity per launcher context
- `parallel_exec` then carries the resolved project identity explicitly to child workers

That is the safe pattern.

---

## 7. What Commands Changed For The User

No top-level user command had to change.

The workflow remained:

```bash
sciunit parallel_exec ...
```

and the benchmark remained:

```bash
snakemake --snakefile workflows/snakemake/Snakefile --profile workflows/snakemake/profile --configfile configs/global.yaml
```

The fixes are internal:

- finer-grained locking
- explicit project-path binding

This was an important design goal because i wanted to improve correctness without changing the user-facing interface.

---

## 8. Results Before And After

### 8.1 Before Any Fix

Observed failures:

- `database is locked`
- `execution 'eX' already exists`
- batch logs and project names becoming mixed across concurrent Slurm batches

Examples:

- equal-time reproducer `test.py ::: 1 1 1 1` could fail
- full SciUnit Snakemake run `run_002_20260329_040338` failed in the first wave of batches

### 8.2 After Fix 1 Only

Result:

- the old equal-time same-project reproducer succeeded
- a single real SciUnit benchmark batch succeeded

This showed that the **same-project write race** was fixed.

However, the full multi-batch SciUnit workflow still showed cross-project contamination before Fix 2 was applied.

### 8.3 After Fix 1 + Fix 2 (Hybrid Verification)

Before the final internal-only cleanup, I verified the combined logic with the project path pinned explicitly from the benchmark runner. In that verification mode, the full SciUnit Snakemake workflow completed successfully.

Successful workflow run:

- `run_004_20260329_182227`

Observed successful outputs:

- batch `.done` files: `35`
- processed `.out` files: `175`
- raw metrics `.json` files: `176`
  - `175` per-split files
  - `1` merge metrics file
- per-split rule logs: `176`
  - `175` per-split logs
  - `1` merge log path family
- batch logs: `35`
- monitor CSV files: `36`
  - `35` per-batch monitor CSVs
  - `1` combined monitor CSV

Final workflow artifacts confirmed:

- final merged output exists:
  - `results/run_004_20260329_182227/sciunit/1g/final_output_run_004_20260329_182227.txt`
- final aggregated metrics marker exists:
  - `metrics/run_004_20260329_182227/aggregated/sciunit_1g_run_004_20260329_182227.done`

This was the strongest practical confirmation that both original concurrency issues were fixed:

- same-project write races
- wrong-project cross-contamination

### 8.4 After The Final Internal-Only Scoped-Activation Change

I then removed the benchmark-side project export and reran from a clean state so the behavior depended only on the internal SciUnit changes.

Fresh rerun:

- `run_002_20260330_014054`

Observed behavior:

- the old wrong-project contamination did **not** reappear
- the first wave submitted `8` batches
- `8` batches completed successfully

- SciUnit created the correct project:
  - `/home/nkmh5/sciunit/project_run_002_20260330_014054_batch_014`
- the project database registered all five intended revisions:
  - `split_0066`
  - `split_0068`
  - `split_0067`
  - `split_0069`
  - `split_0070`
- five workers completed successfully:
  - `e1 -> split_0066`
  - `e2 -> split_0068`
  - `e3 -> split_0067`
  - `e5 -> split_0070`
  - `e4 -> split_0069`
---

## 9. Why Some Runs Worked Even Before The Patch

This deserves emphasis because it can otherwise look contradictory.

### Local machine

A local run could succeed because:

- fewer things were running at once
- filesystem timing was different
- workers may have completed more staggered in time
- Do not have multiple independent SciUnit projects competing at once

### Direct cluster command that still worked

A cluster command could also succeed if:

- workers did not reach the critical section at the same instant
- only one project was effectively active
- there was enough timing gap between commits

### Batch workflow

The full benchmark workflow was much more likely to fail before the patch because:

- many batches started concurrently
- each batch internally launched multiple `sciunit exec` workers
- multiple projects were being created at almost the same time
- very small timing gaps were enough to trigger both races

So the bug was real even if not every run failed.

---

## 10. Final Takeaway

The main lesson is that SciUnit concurrency needed two different protections:

1. **protect shared writes inside one project**
2. **protect project identity across multiple projects**

The first fix alone was necessary but not sufficient.
The second fix removed the wrong-project contamination problem.

After the fixes now present in the code:

- the simple equal-time reproducer passed
- the single benchmark batch passed
- the hybrid full-workflow verification passed
- the final fresh internal-only rerun showed that project-binding is now correct.

So the concurrency design is in a much better state.
