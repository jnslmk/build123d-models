# Baseline: what an agent without these skills would likely answer

**This is an analytic prediction, not measured data.** No controlled
experiment was run to produce this file — nobody prompted a skills-disabled
agent on all eleven scenarios and recorded its actual answers. Every entry
below is reasoned from (a) well-known published defaults that circulate
widely enough to be strong priors for any general-purpose model, and (b) the
specific "skill-less failure mode" already named for each scenario in
`scenarios.md`. Treat every number in this file as a prediction to be tested,
not a result to cite. See `README.md` Limitations, point 3.

If someone runs the actual comparison (prompt the scenario with and without
skill access, per `README.md`'s "Running it" section), replace the relevant
row's prediction with the observed transcript and label it clearly as
**measured**, distinct from the analytic predictions that remain.

## Why this prediction is plausible at all

A general-purpose model without these skills is not answering from nothing —
it has broad exposure to the same maker-forum and vendor-page content the
skills themselves cite and correct (Fictiv's snap-fit table, vendor insert
datasheets, generic "45° overhang rule" folklore). The skills exist precisely
*because* that popular-but-wrong content is common enough to be the default
answer. So the baseline prediction for most scenarios is not "the agent says
something random" — it is "the agent reproduces the specific popular
misconception the skill was written to correct," which is a much stronger and
more falsifiable prediction than a vague "it will probably get it wrong."

## Per-scenario predictions

### S1 — 60 mm round PLA snap lid

**Predicted baseline answer:** "Use a snap-fit bead, ~0.4–0.5 mm is a typical
retention height for a lid this size" — sized by feel/convention, with no
strain calculation and no material-specific limit. PLA is treated as
interchangeable with any other filament.

**Why this is wrong or underspecified:** 0.5 mm read as a radial bead height
on a 60 mm ring is `ε = 2×0.5/60 = 1.7 %` hoop strain — over PLA's one-shot
ceiling (1.0 %) and moreso its reopenable limit (0.6 %) used repeatedly. The
baseline answer has no strain budget at all, so it cannot notice this, and it
never surfaces the PLA→PETG material-swap recommendation the correct answer
leads with.

### S2 — M3 heat-set boss in a 3 mm wall

**Predicted baseline answer:** "M3 heat-set insert, 4.0 mm hole (the nominal
size on most vendor spec sheets and the number a quick web search returns
first), boss around 6–8 mm, add the usual lead-in chamfer since every hole
gets one."

**Why this is wrong or underspecified:** 4.0 mm is the *finished-hole*
figure a vendor states as what they want to see, not what to cut in a printer
that prints holes undersize — CNC Kitchen's printed measurements put the
working vertical-hole figure at 4.2 mm. The boss guess of 6–8 mm undershoots
the preferred 9.2 mm (2× insert OD) that the skill recommends "where space
allows." And the lead-in chamfer is actively wrong here: it is a documented,
deliberate exception to the repo's usual "chamfer every mouth" rule, which
the baseline answer applies uniformly because it has no reason to know this
one hole is different.

### S3 — Snap bead on a small PETG cap

**Predicted baseline answer:** "0.5 mm bead, same as any snap-fit lid" —
reusing the same folklore number regardless of the ring being 25 mm instead
of 60–80 mm.

**Why this is wrong or underspecified:** the folklore number is not
diameter-aware at all. At 25 mm, `ε = 2×0.5/25 = 4.0 %` — over twice PETG's
one-shot ceiling (1.7 %). The correct h_bead of ~0.21 mm is 2.4× smaller than
the folklore default; the baseline answer's error compounds both the
diametral/radial mistake and the failure to scale with diameter.

### S4 — Cantilever taper

**Predicted baseline answer:** "A constant-thickness arm is simpler to model
and should be fine" — or, if it does taper, an arbitrary un-cited taper ratio
chosen by eye rather than "to h/2 at the tip."

**Why this is wrong or underspecified:** the baseline answer treats the taper
as a stylistic nicety rather than a quantified +63% deflection gain with a
named formula and three independent corroborating sources. Without the
number, there is no way to know the constant-section arm is either 17% more
material or 46% more strained than it needs to be for the same job.

### S5 — Press-fit dowel clearance from Markforged

**Predicted baseline answer:** "Sure, that's from an official design guide —
use 0.02 mm (the middle of 0.00–0.05 mm)."

**Why this is wrong or underspecified:** the baseline answer treats "it's in
a design guide" as sufficient authority without checking which *process* the
guide is written for. Markforged's numbers assume a closed-loop industrial
machine with active clearance control; on a desktop printer the achievable
tolerance (±0.2 mm) is itself four to ten times looser than the clearance
being specified, so the dowel comes out welded solid. This is explicitly
named in the industry as the single biggest cause of a fit that welds solid,
and a general-purpose agent has no reason to know that without the skill.

### S6 — Acme vs. V thread overhang

**Predicted baseline answer:** "Acme/trapezoidal threads print better than
V-threads because the flanks are flatter and there's less overhang" —
repeating the claim in the prompt back as agreement, since this is a
commonly repeated piece of 3D-printing folklore.

**Why this is wrong or underspecified:** this is precisely backwards. A
flatter flank (smaller β from horizontal) produces a *larger* overhang
(`90° − β`), not a smaller one — Acme's 14.5° flank is a 75.5° overhang,
worse than ISO metric V (60°) or a custom 45° V (45°, ideal). The baseline
answer is not a guess so much as a documented, widely-circulated inversion of
the actual geometry, which is exactly why this scenario is useful: it tests
whether the skill corrects a specific wrong belief rather than just adding
detail to a vague one.

### S7 — M4 printed female thread against a real bolt

**Predicted baseline answer:** "M4 is a totally normal, common thread size —
model the female thread with standard V-thread clearance (~0.4 mm total
diametral) and it should be fine."

**Why this is wrong or underspecified:** the baseline treats "M4 is common"
as evidence it is printable as a female thread against real metal, without
knowing the specific, harder floor for that particular pairing (M6 minimum,
versus M8 for printed-on-printed or no floor at all if a heat-set insert is
used instead). The joint would strip on the first real-torque use.

### S8 — Flush-fitting round lid closure

**Predicted baseline answer:** "Use a friction/press-fit lip — it's the
simplest closure that will hold a lid on."

**Why this is wrong or underspecified:** a friction lip is a real, working
closure, but by construction it stands proud where the lip steps out from
the body — it cannot be flush. The baseline answer optimizes for "will it
hold" and misses the actual stated requirement ("no lip standing proud, no
visible step"), because it has no catalogue distinguishing retention
closures from the one flush-specific pattern (the stepped rabbet).

### S9 — Selecting a hole's mouth edge by position

**Predicted baseline answer:** "The position match is probably imprecise
because of floating-point/kernel rounding — widen the comparison tolerance to
a few millimetres and it should match."

**Why this is wrong or underspecified:** this papers over the actual API
trap (`Edge.center()` on a full circle returns a point on the curve, not the
centre) with a tolerance band wide enough to hide the systematic ~1-radius
offset. It will appear to work on a sparsely laid-out part and silently
mis-select the moment two holes are close enough together that the widened
tolerance catches the wrong one.

### S10 — Ribbed bore for a hex driver shank

**Predicted baseline answer:** "Cut the bore at 6.35 mm to match the shank,
maybe add a small clearance like 0.1–0.2 mm for an easy fit."

**Why this is wrong or underspecified:** FDM's ~0.1–0.3 mm small-vertical-hole
undersize is on the same order as the "small clearance" the baseline answer
adds, so the net result is anywhere from a snug fit to a press fit depending
on that print's particular shrinkage — an outcome the baseline answer cannot
predict because it has no undersize-compensation rule at all, let alone the
compliant-rib alternative that would make the grip tolerant of that
variance in the first place.

### S11 — Engraved decimal label at font_size=4

**Predicted baseline answer:** "It looks correct in the viewer, so it should
print fine" — no separate check of stroke width or the decimal point
specifically.

**Why this is wrong or underspecified:** the viewer renders the vector glyph
exactly as drawn; it has no simulation of what a 0.4 mm nozzle can resolve.
A ~0.41 mm-wide period at regular weight is right at the edge of what one
nozzle pass can hold open, and it is a known, specific failure (not a vague
"small text might be hard to read") that the baseline answer has no reason to
single out without the skill's measured glyph table.

## Summary table

| Scenario | Baseline default reproduced | Correct-answer delta |
| --- | --- | --- |
| S1 | 0.5 mm bead by convention, no strain check | 0.18 mm PLA / recommend PETG |
| S2 | 4.0 mm nominal hole, chamfer everywhere | 4.2 mm hole, no chamfer |
| S3 | 0.5 mm bead regardless of diameter | ~0.21 mm at 25 mm PETG |
| S4 | Constant-section arm, no named cost | Taper to h/2, name the +63% |
| S5 | Trust the design-guide number as-is | Reject as industrial-only, use `fits.PRESS` |
| S6 | "Acme is flatter, prints better" | Backwards on overhang; use 45° V/DIN 405 |
| S7 | "M4 is common, should be fine" | Below the M6 metal-bolt floor; use an insert |
| S8 | Friction lip "simplest that works" | Stepped rabbet is the only flush option |
| S9 | Widen the position-match tolerance | Use `arc_center`, not `.center()` |
| S10 | Bore at nominal ± a small clearance | Undersize-aware clearance or ribbed bore |
| S11 | "Looks fine in the viewer" | Flag the period specifically; use BOLD |

No column in this table is a measured pass/fail rate. It is a compact
restatement of the per-scenario predictions above, meant to make the pattern
visible: in nearly every case, the predicted baseline is not "no answer" but
"a specific, named, wrong-or-incomplete answer that happens to be common
enough to be a plausible default" — which is what makes these scenarios a
meaningful test rather than a tautology.
