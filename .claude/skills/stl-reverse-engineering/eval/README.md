# stl-reverse-engineering eval harness

Makes the skill's accuracy claims executable instead of prose. SKILL.md's
round-trip table asserts three numbers per model (`swept/actual`, IoU, and a
pass/fail verdict) as evidence the skill works. This harness re-derives those
same three numbers by actually running the pipeline (`export` ->
`mesh_analyze.py` -> reconstruct -> `mesh_compare.py`) and fails loudly the
moment a real number drifts from the pinned baseline.

Adapted from the `eval/` concept in
[andreahaku/openscad_claude_skill](https://github.com/andreahaku/openscad_claude_skill)
(MIT): named scenarios, each with assertions, plus an append-only results log
with a documented baseline. That repo's assertions are LLM-judged prose checks
on a conversation transcript. This skill ships deterministic scripts with
known numeric ground truth instead of prose to judge, so the concept is
adapted, not copied: every assertion here is a real executable check against
real script output. **No LLM judging is involved anywhere in this harness.**

## What it checks, and why

Three scenarios, one per model in SKILL.md's round-trip table:

| id | model | required `mesh_compare` exit |
|---|---|---|
| `cube` | `cube` | 0 (pass) |
| `door_latch` | `door_latch` | 0 (pass) |
| `led_profiles.stand` | `led_profiles.stand` | 1 (REQUIRED NEGATIVE) |

For each, the harness asserts three independent things:

1. **`swept_over_actual` reproduces.** This ratio (swept profile volume over
   actual mesh volume) is a pure function of the mesh and `mesh_analyze.py`'s
   slicing math -- deterministic given the same STL. A drift here means the
   *pipeline itself* changed (a different simplify tolerance, a slicing bug),
   not that the mesh moved.
2. **IoU reproduces within tolerance.** IoU comes from a Monte Carlo /
   boolean volume comparison in `mesh_compare.py`, which is why it gets a
   tolerance instead of an exact match (see below).
3. **`mesh_compare.py`'s exit code matches what's required.** For
   `led_profiles.stand` the required exit code is **1**, not 0 -- the
   published claim is that the tool correctly *refuses* that reconstruction
   (IoU 38.91%, "wrong shape -- do not iterate"). Asserting exit 1 there is
   the pass condition. If a future change to `mesh_compare.py` ever made it
   return 0 (pass) for that reconstruction, that would be a **silent
   regression in the tool's honesty**, and this is the check that would catch
   it -- an accuracy-only eval would never look at the negative case at all.

## How to run it

One command from the repo root:

```bash
uv run --group mesh python .claude/skills/stl-reverse-engineering/eval/run_eval.py
```

Optionally attach a note for the log:

```bash
uv run --group mesh python .claude/skills/stl-reverse-engineering/eval/run_eval.py \
    --change-description "tightened mesh_analyze.py's simplify default"
```

It exports each model fresh (`uv run export <model>`), runs
`mesh_analyze.py` and `mesh_compare.py` for real (subprocesses, `--group
mesh`), dynamically imports each `reconstructed.py`'s `create()`, exports the
reconstruction to a temp-dir STL, and prints a table plus a pass rate:

```
scenario                 swept/actual        IoU   exit  result
cube                           1.0000    100.00%      0  PASS
door_latch                     0.9967     99.60%      0  PASS
led_profiles.stand             2.1374     38.91%      1  PASS

3/3 scenarios matched their pinned baseline
```

Exit code is `0` when every scenario matches its baseline, `1` if any
assertion fails. Every run appends one line to `results.jsonl`, whether it
passed or not.

## The pinned baselines, and where they came from

```
cube                 swept/actual 1.000  -> IoU 100.00%  (1.00)  mesh_compare exit 0
door_latch           swept/actual 0.997  -> IoU  99.60%  (0.996) mesh_compare exit 0
led_profiles.stand   swept/actual 2.137  -> IoU  38.91%  (0.3891) mesh_compare exit 1
```

These are the exact numbers published in `SKILL.md`'s "Round-trip validation"
table as of the date this harness was written (2026-08-05). They are pinned
in `scenarios.json` as `baseline_swept_over_actual` and `baseline_iou`. They
are **not** re-derived from a fresh run and then written back -- they are
copied from the already-published table, so the harness is checking the
skill's *documented claim* against reality, not checking a number against
itself.

**Do not edit these numbers to make a run pass.** If a future run disagrees
with them outside tolerance, that is the harness doing its job -- it means
either the skill regressed or the SKILL.md table needs updating (and that
update should be a deliberate, reviewed change to SKILL.md, not a quiet edit
to `scenarios.json`).

## Tolerance

`scenarios.json` declares two tolerances, both absolute, both on the raw
`0..1` fraction (not the percentage):

- `swept_tolerance: 0.005` -- `swept_over_actual` is deterministic geometry
  math (polygon area x extrusion length / mesh volume) with no sampling
  noise, so this only needs to absorb floating-point and library-version
  differences in the slicing computation itself. Tight on purpose: a real
  change to the slicing or simplify logic should trip this.
- `iou_tolerance: 0.01` (1 percentage point of IoU) -- `mesh_compare.py`
  computes IoU via an exact `manifold3d` boolean when the meshes are clean
  (both STL exports here are watertight, so that's the code path exercised),
  which is itself deterministic, but the *mesh tessellation* underneath it
  can shift by a hair across `build123d`/OCCT/`manifold3d` versions or
  machines (different triangulation of the same curved surface, e.g.
  `door_latch`'s fillets). 1 percentage point is forgiving enough to absorb
  that legitimate cross-machine noise while still being far tighter than the
  ~9-percentage-point gap between `door_latch`'s 99.60% and, say, the 85%
  "draft" verdict boundary -- a real regression that dropped a hole or
  mis-sized a profile would blow through 1 point immediately, as the
  `led_profiles.stand` scenario's 38.91% (60+ points off the 95% pass bar)
  demonstrates.

## This harness's own first real run

Ran on this machine on 2026-08-05, `uv run --group mesh python
.claude/skills/stl-reverse-engineering/eval/run_eval.py`:

```
scenario                 swept/actual        IoU   exit  result
cube                           1.0000    100.00%      0  PASS
door_latch                     0.9967     99.60%      0  PASS
led_profiles.stand             2.1374     38.91%      1  PASS

3/3 scenarios matched their pinned baseline
```

**Result: all three baselines reproduced within tolerance. No discrepancy.**

For the record, the measured values versus the pinned baselines:

| scenario | measured swept/actual | baseline | measured IoU | baseline IoU | exit (req'd) |
|---|---|---|---|---|---|
| `cube` | 1.0000 | 1.000 | 100.00% | 100.00% | 0 (0) |
| `door_latch` | 0.9967 | 0.997 | 99.60% | 99.60% | 0 (0) |
| `led_profiles.stand` | 2.1374 | 2.137 | 38.91% | 38.91% | 1 (1) |

`door_latch`'s `swept_over_actual` (0.9967 measured vs. 0.997 published) is a
rounding-precision difference only -- the published table carries 3 decimal
places, the harness prints 4 -- well inside the 0.005 tolerance, not a real
discrepancy. Every other figure matched to the published precision exactly.
This run's environment: same `manifold3d`/`trimesh`/`build123d` versions
pinned in this repo's `uv.lock` that produced the original SKILL.md
measurements, run in this repo's own dev environment (not a foreign machine),
so an exact match is the expected outcome here, not a coincidence -- the
tolerance exists for a *different* machine or a future library bump, and this
run does not exercise that case.

## `results.jsonl` is an append-only audit log

Matches the reference repo's own convention: one compact JSON object per run,
appended, never rewritten. Fields: `iteration` (sequential), `kind` (`"seed"`
or `"run"`, see below), `timestamp` (ISO 8601, UTC), `score` (pass rate as a
percentage), `passed`, `total`, `failed_assertions` (empty list when clean),
`skill_version_hash` (first 12 hex chars of `SKILL.md`'s SHA-256, so a line
records which version of the skill it ran against), and
`change_description` (a one-line note, `--change-description` on the CLI or a
default placeholder).

**Every line means one of exactly two things, told apart by `kind`, and each
is appended by a different party:**

- **`"kind": "run"`** -- a real, completed execution of `run_eval.py`. These
  lines are appended **only** by `append_result()` inside `run_eval.py`
  itself, immediately after that same invocation's pipeline finished. There
  is no code path that writes a `"run"` line for anything other than the
  execution currently producing it -- whoever ran the command (a developer,
  CI, an agent verifying the harness) is who "appended" that line, by virtue
  of having run it.
- **`"kind": "seed"`** -- exactly one entry, `iteration: 0`. Hand-authored,
  once, when this harness was first written, to record that these three
  baselines were pinned from SKILL.md's already-published round-trip table
  (dated the day this harness was written), not measured by the harness
  itself. It is not a harness run and must never be confused with one.

**The rule that keeps this file trustworthy:** a `change_description` must
only ever describe an event that has already happened by the time the line
is written. Concretely, that means: never hand-author or edit a `"run"` line,
and never describe a line as coming from "a reviewer" (or anyone else) who
had not, in fact, already executed `run_eval.py` themselves at the time that
line was added. An earlier version of this file had exactly that defect --
a line whose `change_description` attributed the run to a review that had
not happened yet when the line was written -- and it was removed rather than
corrected in place, because the fix for a fabricated audit entry is deleting
it, not editing its wording. If a line looks it may misrepresent what
actually happened, delete it; do not paper over it with a new line.

The log is intentionally append-only and is not auto-pruned by the harness --
that is the point of an audit trail (the reference repo's `results.jsonl`
works the same way). If it grows large enough to be unwieldy, trim it by hand
in a reviewed change; the harness itself will never silently rewrite or
truncate it.
