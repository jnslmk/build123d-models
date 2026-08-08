# photo-reverse-engineering eval harness

Makes the skill's numeric claims executable instead of prose. SKILL.md's "What
the tools were measured to do" table publishes four results; this harness
re-derives all four by actually running `photo_measure.py` and
`silhouette_match.py`, and fails the moment one drifts.

## How this harness differs from `stl-reverse-engineering`'s

That skill's harness pins baselines **copied from an already-published table**,
so it checks a documented claim against reality. This one could not: the skill
and its numbers were written together, so the baselines in `scenarios.json` are
the values this harness measured on its own first run, which were then published
in SKILL.md.

Say plainly what that means. This harness is a **regression detector**, not
independent confirmation of the first measurement. It will catch a future change
that moves a number; it cannot catch a first measurement that was wrong for a
reason common to both the script and the check.

Two of the four scenarios are partly insulated from that, and deliberately so:

- `scale_error_2pct` has an **independent closed form**. A uniformly scaled
  convex outline has IoU exactly 1/k², so k = 1.02 predicts 0.961169 before any
  code runs. The harness measured 0.96124. Agreement to four decimals against
  maths that does not share a line of code with the rasteriser is real
  confirmation, not self-agreement.
- `rectify_roundtrip` has **exact ground truth by construction**: the segment
  was 40 mm before it was warped, so recovering 40.000 mm is checkable without
  trusting anything the harness computed.

`self_match` and `hidden_cavity` have no such external anchor. They assert
properties (a mask matches itself; a sealed void changes no outline) that are
true by geometry, so a deviation is unambiguously a bug — but they confirm the
implementation, not the theory.

## The scenarios

| id | what it runs | why it exists |
|---|---|---|
| `self_match` | `lens_cap` top silhouette against itself | If this is not exactly 1.0, every other IoU here is meaningless. |
| `scale_error_2pct` | the same silhouette rasterised 2% larger | **Required near-miss.** A 2% oversize part must still clear a 95% gate. |
| `hidden_cavity` | a solid block vs the same block with a sealed void | **Required negative.** Silhouettes identical, 25% of the material gone. |
| `rectify_roundtrip` | a synthetic oblique shot of a known board | End-to-end homography, warp and measurement in one. |

The two marked scenarios must keep scoring *well* — a high IoU is the pass
condition, because the published claim is that a visual gate is fooled here. If
a future change made `hidden_cavity` return a low IoU, SKILL.md's "verified in
code or not at all" warning would be over-stated, and this is the check that
would notice. An accuracy-only eval would never look at either case.

`scale_error_2pct` rasterises the same model at `px_per_mm * 1.02` rather than
remodelling it. That is the identical mask a part scaled by 1.02 produces, and
it introduces no remodelling noise, so the scenario measures the *grader's*
behaviour and nothing else.

## Running it

From the repo root:

```bash
uv run --no-group viewer --group photo python \
    .claude/skills/photo-reverse-engineering/eval/run_eval.py
```

`--no-group viewer` is only needed on a machine without GTK development headers
(pygobject builds from source); drop it if `uv sync` already succeeds for you.
Attach a note for the log with `--change-description "..."`.

Exit code is 0 when every scenario matches, 1 otherwise. Every run appends one
line to `results.jsonl`, pass or fail. Runtime is about 5 seconds — this is
cheap enough to run on every change to either script.

## This harness's first real run

2026-08-08, on this machine, in this repo's own dev environment:

```
scenario              measured                                    result
----------------------------------------------------------------------------
self_match            iou=1.0000  width_ratio=1.0000              PASS
scale_error_2pct      iou=0.9612  width_ratio=0.9794              PASS
hidden_cavity         iou=1.0000  volume_ratio=0.7500             PASS
rectify_roundtrip     recovered_mm=40.0000  error_mm=0.0000  rectified_fill=0.9979

4/4 scenarios matched their pinned baseline
```

Exit code 0. As set out above, this run is where the baselines came from, so
4/4 here is not independent evidence — with one exception worth stating
precisely: `scale_error_2pct`'s 0.96124 was compared to 1/1.02² = 0.961169,
derived on paper, and agreed to four decimal places. That comparison the run
*does* pass independently.

Full-precision values from the same run, for anyone re-deriving them:
`self_match` 1.0 / 1.0, `scale_error_2pct` 0.96124 / 0.9793578, `hidden_cavity`
1.0 / 0.75, `rectify_roundtrip` 40.0 mm / 0.0 mm / 0.99786.

## Tolerances, and why each is what it is

- **IoU on `self_match` / `hidden_cavity`: `[0.9999, 1.0]`.** These are exact by
  geometry, so the window only absorbs a hypothetical rounding difference. Any
  real drift is a bug.
- **IoU on `scale_error_2pct`: `±0.005`.** Wide enough to absorb a change in
  tessellation tolerance (which shifts the outline by a fraction of a pixel),
  far tighter than the ~0.04 gap between this value and 1.0 that the whole claim
  rests on.
- **`width_ratio` on `scale_error_2pct`: `±0.005`.** The ratio comes from
  integer pixel bounding boxes, so it quantises: 427 px against 436 px gives
  0.97936 rather than 1/1.02 = 0.98039. That quantisation is a property of the
  measurement, not noise, and the window covers it.
- **`error_mm` on `rectify_roundtrip`: `[0, 0.05]`.** Measured 0.000. The window
  allows a float-precision difference and nothing else.
- **`rectified_fill`: `[0.99, 1.0]`.** Measured 0.9979. The shortfall is the
  one-pixel border where bilinear sampling reaches outside the warped
  quadrilateral, which is correct behaviour, not error.

**Do not edit a baseline to make a run pass.** If a run disagrees, either the
tooling regressed or SKILL.md's table needs a deliberate, reviewed update — and
the table is the thing that changes first, with `scenarios.json` following it.

## `results.jsonl` is an append-only audit log

One compact JSON object per run: `iteration`, `kind`, `timestamp` (ISO 8601,
UTC), `score`, `passed`, `total`, `failed_assertions`, `skill_version_hash`
(first 12 hex chars of `SKILL.md`'s SHA-256) and `change_description`.

Lines are written **only** by `append_result()` inside `run_eval.py`, at the end
of the run that produced them. There is no path that writes a line for a run
that did not happen, and none should ever be hand-authored. A
`change_description` must describe something that had already happened when the
line was written. If a line looks like it misrepresents what actually ran,
delete it rather than editing its wording.

The harness never rewrites or truncates the log. Trim it by hand in a reviewed
change if it ever grows unwieldy.
