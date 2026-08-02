# Eval scenarios

Eleven design questions, each with a checkable correct answer derived from the
content of the nine skills under `.claude/skills/`. See `README.md` for how to
run these and what a pass means, and `baseline.md` for what an agent without
the skills would likely answer instead.

Format note: this is hand-authored Markdown rather than JSON/YAML. There is no
executable grader (per the task's own allowance), the grading is currently a
human or an LLM judge reading prose assertions against a transcript, and the
citations need to stay next to prose they reference for a reviewer to check
them quickly. A flat list of Markdown sections is the lowest-friction format
for that reader. If this suite grows an executable grader later, promoting
each scenario's `assertions` list to a YAML/JSON sidecar (keeping the prompt
and citations in Markdown) is the natural next step — see `README.md`
Limitations.

Every scenario below states: the prompt, the expected answer with its
tolerance, the specific assertions a grader checks, which skill should fire,
the exact file and section the answer traces to, and the failure mode a
skill-less agent would most plausibly produce.

## Contents

1. [60 mm round PLA snap lid](#s1-60-mm-round-pla-snap-lid)
2. [M3 heat-set boss in a 3 mm wall](#s2-m3-heat-set-boss-in-a-3-mm-wall)
3. [Snap bead on a small PETG cap — the diametral trap at scale](#s3-snap-bead-on-a-small-petg-cap--the-diametral-trap-at-scale)
4. [Cantilever taper — worth the modelling complexity?](#s4-cantilever-taper--worth-the-modelling-complexity)
5. [Press-fit dowel clearance ported from an industrial guide](#s5-press-fit-dowel-clearance-ported-from-an-industrial-guide)
6. [Screw-on lid thread profile — Acme vs. V](#s6-screw-on-lid-thread-profile--acme-vs-v)
7. [M4 printed female thread against a real bolt](#s7-m4-printed-female-thread-against-a-real-bolt)
8. [Flush-fitting round lid closure](#s8-flush-fitting-round-lid-closure)
9. [Selecting a hole's mouth edge by position](#s9-selecting-a-holes-mouth-edge-by-position)
10. [Ribbed bore for a hex driver shank](#s10-ribbed-bore-for-a-hex-driver-shank)
11. [Engraved decimal label at font_size=4](#s11-engraved-decimal-label-at-font_size4)

---

## S1: 60 mm round PLA snap lid

**Prompt:** "Design a 60 mm round box with a reopenable snap lid in PLA."

**Expected answer (tolerance in parentheses):**

- Permissible strain for PLA, **repeated/reopenable** engagement is **0.6 %**
  (not the 1.0 % one-shot ceiling, and nowhere near the 4–8 % folklore figure).
- Bead height uses the **diametral** formula `h_bead = ε·d/2`, giving
  `0.006 × 60 / 2 = 0.18 mm` radial (± 0.02 mm).
- The answer flags 0.18 mm as impractically small to mould/print reliably and
  as a joint that will fatigue fast even if it prints, and recommends either
  **switching material to PETG** (repeated ε = 1.0 % → 0.30 mm, a bead that is
  actually buildable) or **switching closure type** (e.g. rabbet + screws, or
  a friction lip with PETG/ASA instead of PLA).
- It does **not** land on a flat 0.5 mm bead as a safe PLA answer.

**Assertions a grader checks:**

- [ ] States PLA reopenable/repeated strain as 0.6 % (accept 0.55–0.65 %).
- [ ] Applies `h = ε·d/2`, not `h = ε·d` (i.e. treats the formula's `y` as
      diametral).
- [ ] Computed bead height is 0.16–0.20 mm for PLA, or explicitly rejects PLA
      for this joint before computing a bead at all.
- [ ] Recommends a specific fix: material swap to PETG (with the 0.30 mm
      figure) or a different closure — not just "make the bead small."
- [ ] Does not present 0.5 mm as an acceptable PLA bead for a 60 mm reopenable
      lid.

**Skill that should fire:** `snap-fits` (bead sizing), with `box-closures`
plausibly co-firing since the prompt is phrased as "a box with a lid."

**Traces to:**

- `.claude/skills/snap-fits/references/materials.md` — "Derived table for real
  filaments" (PLA repeated 0.6 %) and "Two published errors to contradict."
- `.claude/skills/snap-fits/references/annular.md` — "The headline trap: `y`
  is diametral, not radial" and the "Bead height by lid diameter" table.
- `.claude/skills/snap-fits/SKILL.md` — worked example section states the same
  arithmetic for `round_snap_box.py` at a different diameter.

**Skill-less failure mode:** reaches for "0.5 mm is the standard snap bead
height" (the folklore default repeated across maker forums and even implied
by some published tables if `y` is misread as radial), without checking the
material's strain limit or the diametral/radial distinction at all. On a
60 mm ring that is `ε = 2·0.5/60 = 1.7 %` — over PLA's one-shot ceiling (1.0 %)
and nearly 3× its reopenable limit (0.6 %); the joint would crack open on
repeated use, if it survives the first cycle.

---

## S2: M3 heat-set boss in a 3 mm wall

**Prompt:** "Add an M3 heat-set boss to a 3 mm wall."

**Expected answer (tolerance in parentheses):**

- Hole diameter **4.2 mm** (the repo default for a vertical insert hole — not
  the 4.0 mm nominal vendor figure).
- Boss OD **≥ 6.5 mm floor**, preferably **~9.2 mm** (2× the 4.6 mm insert OD)
  where space allows.
- Depth for a **blind** hole = insert length **+ 1 mm** (a relief well for
  displaced plastic), at least insert length + 2 thread pitches.
- **No lead-in chamfer** at the hole mouth — a deliberate exception to the
  repo's general "chamfer every hole mouth" rule.
- Wall around the boss ≥ 1× the fastener diameter (3 mm).

**Assertions a grader checks:**

- [ ] Hole diameter stated as 4.2 mm, not 4.0 mm.
- [ ] Boss OD given as ≥ 6.5 mm, with 9.2 mm (or "~2×") named as the preferred
      target, not just the floor.
- [ ] Blind-hole depth rule given as insert length + 1 mm.
- [ ] Explicitly says **no** lead-in chamfer on this hole, and gives the
      reason (insert's own chamfer self-guides; a printed chamfer removes
      material the insert needs to melt into).
- [ ] Does not contradict itself by adding a chamfer "per the usual hole rule."

**Skill that should fire:** `fasteners-and-inserts`.

**Traces to:**

- `.claude/skills/fasteners-and-inserts/SKILL.md` — "Quick numbers" table and
  "Repo-specific rules" (no lead-in chamfer).
- `.claude/skills/fasteners-and-inserts/references/heat-set-inserts.md` —
  "Conflict 1: the M3 hole is not 4.0 mm," "Conflict 2: boss diameter, 2-3x or
  1.4x," and "Hole geometry rules" (depth, no chamfer).

**Skill-less failure mode:** copies the vendor table's nominal M3 hole
(4.0 mm) verbatim, sizes the boss at the vendor's bare minimum (6.5 mm, or
even the SPIROL 1.4× figure) rather than the safer 2×, and — following the
repo's own general "lead-in at every hole mouth" habit, which is correct
everywhere except here — adds a chamfer that removes exactly the material the
insert needs to displace into.

---

## S3: Snap bead on a small PETG cap — the diametral trap at scale

**Prompt:** "I'm adding a retaining snap bead to a 25 mm diameter PETG cap,
snapped once during assembly and never reopened. How tall should the radial
bead be?"

**Expected answer (tolerance in parentheses):**

- PETG **one-shot** strain ceiling is **1.7 %**.
- `h_bead = ε·d/2 = 0.017 × 25 / 2 ≈ 0.21 mm` radial (± 0.02 mm).
- The answer explicitly names the diametral/radial trap: a bead built to the
  common "just make it 0.5 mm" folklore, read as a *radial* height, would be a
  **diametral** interference of `y = 2 × 0.5 = 1.0 mm` over a 25 mm ring, i.e.
  `ε = 1.0 / 25 = 4.0 %` — well over twice PETG's 1.7 % ceiling, and the cap
  would crack rather than snap.

**Assertions a grader checks:**

- [ ] Uses PETG one-shot ε = 1.7 % (not the repeated 1.0 %, since the prompt
      states "snapped once, never reopened").
- [ ] Computes `h_bead ≈ 0.21 mm` (accept 0.19–0.23 mm) using `h = ε·d/2`.
- [ ] States, unprompted, that a naive 0.5 mm bead at this diameter would be
      unsafe, and shows the arithmetic (or the equivalent conclusion) for why.
- [ ] Identifies that the failure mode of the naive answer is specifically the
      diametral-vs-radial confusion, not just "0.5 mm is too big."

**Skill that should fire:** `snap-fits`.

**Traces to:**

- `.claude/skills/snap-fits/references/annular.md` — "The headline trap: `y`
  is diametral, not radial," which states this exact failure mode ("fails
  outright below about 30 mm, where the same mistake doubles the strain past
  the material's limit outright") and the bead-height table.
- `.claude/skills/snap-fits/references/materials.md` — PETG one-shot ε = 1.7 %.

**Skill-less failure mode:** applies "0.5 mm bead" as a fixed default that
"works fine on the lids I've seen," which is true on 40–80 mm PETG lids (per
`annular.md`) but silently carries a 2× diametral/radial error that only
becomes fatal once the ring shrinks below ~30 mm — exactly this case.

---

## S4: Cantilever taper — worth the modelling complexity?

**Prompt:** "I'm modelling a cantilever snap arm (a latch/hook) in PETG.
Should I bother lofting the thickness down to half at the tip, or keep the
cross-section constant along its length to keep the code simple?"

**Expected answer (tolerance in parentheses):**

- Always taper the thickness to `h/2` at the tip. It buys **+63 %** more
  permissible deflection for the same root strain, confirmed independently by
  three design guides (Covestro 0.67 → 1.09, BASF 0.92 → 1.50, Ticona ratio
  1.636 — all within 0.01 of "1.63").
- The deflection formula for the tapered case is `y = 1.09·ε·l²/h` versus
  `y = 0.67·ε·l²/h` for a constant section.
- Skipping the taper costs **17 % more material** for the same deflection, or
  **46 % higher root strain** for the same envelope — either way the constant
  section is the worse design, not just the simpler one. A linear loft from
  root to tip is one more sketch feature, not a new capability.

**Assertions a grader checks:**

- [ ] Recommends the thickness taper to `h/2` at the tip as the default,
      not a constant section "for simplicity."
- [ ] States the factor as ≈1.63× (accept 1.6–1.65).
- [ ] Cites at least one concrete cost of skipping it: +17 % material for
      equal deflection, or +46 % strain for equal envelope.
- [ ] Uses `y = 1.09·ε·l²/h` for the tapered case if it writes a formula at
      all (not the 0.67 constant-section coefficient).

**Skill that should fire:** `snap-fits`.

**Traces to:**

- `.claude/skills/snap-fits/references/cantilever.md` — "The three
  cross-sections" table and "The taper factor is 1.63, not a rounding fluke."

**Skill-less failure mode:** picks the constant-thickness section because it
is one line of code instead of a loft, and does not know a name or number
exists for what that choice costs — the arm ends up needing to be longer or
thicker than necessary to hit the same undercut, or is sized to the same
envelope and quietly runs 46 % hotter on root strain than the tapered
alternative would.

---

## S5: Press-fit dowel clearance ported from an industrial guide

**Prompt:** "I found Markforged's Composites Design Guide, which gives
0.00–0.05 mm diametral clearance for a press fit. We're printing a locating
dowel on a desktop PETG printer (K2 Plus / Centauri Carbon). Should I use that
number?"

**Expected answer (tolerance in parentheses):**

- No. Markforged's figures are for a **closed-loop industrial machine
  printing Onyx**, and do not transfer to desktop FDM.
- On desktop FDM the error budget — holes print ~0.24 mm undersize, shafts
  ~0.10 mm oversize, and practical achievable tolerance is only ±0.2 mm — is
  **larger than the 0.00–0.05 mm clearance itself**, so a Markforged "press
  fit" becomes an unassemblable weld on a desktop machine.
- Use the desktop-safe default instead: `fits.PRESS = -0.10 mm` diametral
  (`models.lib.fits`), i.e. more interference room than the industrial figure,
  not less.

**Assertions a grader checks:**

- [ ] Explicitly declines to use the Markforged 0.00–0.05 mm figure as-is.
- [ ] States the reason: industrial closed-loop machine (Onyx) vs. desktop
      FDM's much larger error budget.
- [ ] Recommends `fits.PRESS = -0.10 mm` (or an equivalent number in the
      -0.05 to -0.15 mm neighbourhood — must be a *looser* clearance value
      than Markforged's, not tighter) as the number to actually model.
- [ ] Mentions at least one concrete desktop error figure (hole undersize
      ~0.24 mm, shaft oversize ~0.10 mm, or ±0.2 mm practical tolerance).

**Skill that should fire:** `fdm-fits-and-clearances`.

**Traces to:**

- `.claude/skills/fdm-fits-and-clearances/SKILL.md` — "Rule 5 — do not port
  industrial numbers."
- `.claude/skills/fdm-fits-and-clearances/references/fits.md` — "The
  industrial-numbers trap" and "Hole and shaft compensation."

**Skill-less failure mode:** treats the Markforged PDF as an authoritative
design guide (it is, for its own machine) and models the dowel at 0.02 mm
clearance. The first printed assembly does not go together at all, and
without knowing the industrial-numbers trap by name, the likely next step is
random re-tuning of the CAD rather than recognising the clearance was ported
from the wrong process class.

---

## S6: Screw-on lid thread profile — Acme vs. V

**Prompt:** "We're adding a screw-on lid to a small enclosure — printed
thread on both halves, axis vertical. A colleague suggests an Acme
(trapezoidal) profile 'because the flatter flanks print better than a
V-thread.' Do you agree?"

**Expected answer (tolerance in parentheses):**

- No — this is backwards on overhang. Overhang = `90° − β` where `β` is the
  flank angle from horizontal. A **flatter** flank means a **smaller** `β`,
  which means a **larger**, not smaller, overhang.
- Acme (14.5° flank) is a **~75.5°** overhang — "pure bridging." ISO metric V
  (30° flank) is **60°**. A custom **45° V** is **45°** — exactly the 45°
  design rule, and the best of the listed options for a lid.
- For a screw-on lid, where surface finish and easy starting dominate, pick a
  **45° custom V or a DIN 405 round/knuckle profile**, not Acme.
- Acme's genuine merits — a blunt crest, a thick root, generous built-in axial
  clearance — matter for a load-carrying leadscrew, not a lid, and are not
  reasons related to overhang at all.

**Assertions a grader checks:**

- [ ] States the "Acme prints better because flatter" claim is backwards /
      geometrically wrong on overhang.
- [ ] Gives correct overhang figures: Acme ≈ 75–75.5°, ISO V 60°, custom 45° V
      = 45° (accept ±2° rounding).
- [ ] Recommends 45° custom V or DIN 405 round thread for this lid, not Acme.
- [ ] If it credits Acme with real advantages, attributes them to crest/root
      geometry and clearance — not to overhang — and frames them as relevant
      to leadscrews, not lids.

**Skill that should fire:** `fasteners-and-inserts` (the profile numbers
live there); `box-closures` is the likely first skill to fire on "screw-on
lid" and hands off to `fasteners-and-inserts` for the thread profile per its
own decision table.

**Traces to:**

- `.claude/skills/fasteners-and-inserts/references/threads.md` — "Overhang:
  the profile choice" table and "The common advice is backwards."
- `.claude/skills/box-closures/SKILL.md` — row 4 ("Screw-on thread") and its
  "Thread profile ... → `fasteners-and-inserts`" pointer.

**Skill-less failure mode:** agrees with the colleague and specifies an Acme
thread, reproducing the widely-circulated but geometrically backwards claim.
The lid thread ends up with a ~75° overhang — close to a pure bridge — where
a 45–60° overhang was available for the same lid.

---

## S7: M4 printed female thread against a real bolt

**Prompt:** "A bracket needs an M4 female thread printed directly into the
plastic, to take a real steel M4 bolt in a load-bearing joint. Good plan?"

**Expected answer (tolerance in parentheses):**

- No. Printed female thread + real metal bolt needs **M6×1.0 and up**. Below
  that, the female crest is thinner than a couple of extrusions and shears
  off under load.
- M4 is also below the "below M5 under load → heat-set insert" line.
- Recommend a **heat-set insert** instead for this joint.

**Assertions a grader checks:**

- [ ] States the minimum size for printed-female + metal-bolt as M6, and that
      M4 is below it.
- [ ] Gives the failure mode: crest thickness ~ a couple of extrusions,
      shears under load.
- [ ] Recommends a heat-set insert as the fix, not "print it anyway with a
      bigger clearance" or "cut it deeper."
- [ ] Does not approve the M4 printed female thread as specified.

**Skill that should fire:** `fasteners-and-inserts`.

**Traces to:**

- `.claude/skills/fasteners-and-inserts/references/threads.md` — "Minimum
  sizes" ("Printed female + metal bolt: M6 x 1.0 and up... Below M5 under
  load: do not print the thread. Use a heat-set insert.").
- `.claude/skills/fasteners-and-inserts/SKILL.md` — "Choosing the joint,"
  decision-order point 5.

**Skill-less failure mode:** treats M4 as an ordinary, common thread size and
models the female thread directly (perhaps with generic 0.4 mm total
diametral clearance from a screw-on-lid mental model), without checking that
this specific pairing — printed female against a *real metal* bolt — has a
harder floor (M6) than printed-on-printed (M8) or an insert-backed hole would.

---

## S8: Flush-fitting round lid closure

**Prompt:** "I need a round lid that sits perfectly flush with the box's
exterior — no lip standing proud, no visible step at the joint line. What
closure should I use, and what's the wall budget?"

**Expected answer (tolerance in parentheses):**

- **Stepped rabbet** (the flush closure) — the only row in the closure table
  that achieves a flush exterior.
- Recess the top of the box wall inward to a thin lip; the lid drops *over*
  that lip so the lid's outer face is coplanar with the body.
- Wall budget is asymmetric: `body_wall = lip_wall + clearance + lid_wall`
  (thick body, thin lid), with `lip_wall ≥ 0.8 mm` and clearance
  0.15–0.25 mm.
- The lid mouth seats **flat-on-flat** on the shoulder the recess creates —
  that shoulder is not chamfered.
- If retention is also needed, a snap bead lives *inside* the joint so it
  never breaks the flush exterior.

**Assertions a grader checks:**

- [ ] Names the closure as a stepped rabbet (or "flush rabbet"), not a
      friction lip, bayonet, magnet-only, or screw-down closure.
- [ ] States the wall-budget formula `body_wall = lip_wall + clearance +
      lid_wall`.
- [ ] Gives `lip_wall ≥ 0.8 mm` and clearance 0.15–0.25 mm.
- [ ] States the shoulder/lid mouth mates flat-on-flat (not chamfered), and
      that a retention bead (if any) is buried inside the joint.

**Skill that should fire:** `box-closures`.

**Traces to:**

- `.claude/skills/box-closures/SKILL.md` — decision table row 2 ("Stepped
  rabbet (flush)") and "## 2. Stepped rabbet (flush) — the house pattern."

**Skill-less failure mode:** picks the friction/press-fit lip (row 1) as "the
simplest thing that works" — it is a working closure, but by construction the
lip stands proud of the body wall where it steps out, so the result is not
flush; the "no visible step" requirement in the prompt is missed entirely.

---

## S9: Selecting a hole's mouth edge by position

**Prompt:** "I'm writing a check that should select one specific circular
hole's mouth edge on a plate, by comparing `edge.center()` against a known
`(x, y)` hole-centre coordinate. It's matching the wrong edge, or nothing at
all. What's wrong?"

**Expected answer (tolerance in parentheses):**

- `Edge.center()` on a **full circle** returns a point **on the curve**, not
  the centre of the circle — so comparing it against a known hole-centre
  coordinate can never match (the mismatch is roughly one hole radius).
- Use **`edge.arc_center`** for circular edges instead, which is the actual
  circle centre.
- Non-circular edges raise `ValueError` on `.arc_center`, so guard the access
  with try/except.
- `.center()` remains the *correct* call for straight/line edges (e.g. hex
  socket flats), where it is the midpoint — the fix is not "never use
  `.center()`," it is "use the right accessor for the edge type."

**Assertions a grader checks:**

- [ ] Correctly diagnoses the root cause as `Edge.center()` on a circle
      returning a point on the curve, not the centre.
- [ ] Recommends `edge.arc_center` for circular edges as the fix.
- [ ] Notes the `ValueError`-on-non-circular-edge guard.
- [ ] Does not overgeneralise to "never use `.center()`" — states it is still
      correct for straight/line edges.

**Skill that should fire:** `build123d-geometry-ops`.

**Traces to:**

- `.claude/skills/build123d-geometry-ops/references/gotchas.md` — "2.
  `Edge.center()` on a full circle is a point on the curve, not the centre."

**Skill-less failure mode:** treats the mismatch as noisy/approximate
geometry and "fixes" it by widening the position-matching tolerance to a
few mm, which happens to work by accident on a sparse hole layout and breaks
again the moment two holes are that close together — the actual API trap is
never identified or fixed.

---

## S10: Ribbed bore for a hex driver shank

**Prompt:** "I'm designing a tool holder with round bores that should grip a
6.35 mm hex driver shank firmly enough for one-handed insertion and removal.
Is cutting the bore at exactly 6.35 mm the right diameter?"

**Expected answer (tolerance in parentheses):**

- No. **Never cut a bore at nominal.** FDM prints small vertical holes
  roughly **0.1–0.3 mm undersize**, so a bore modelled at exactly the tool's
  diameter comes off the printer as a press fit.
- For a simple drop-in fit, add **~0.4–0.5 mm diametral clearance**.
- For a robust, variation-tolerant grip (the better answer for a
  one-handed tool holder), cut the bore into a wider relieved **valley** and
  add **3 rounded internal ribs** so the tool rides on three line contacts
  instead of a full-circle wall; stop the ribs a few millimetres below the
  mouth so the opening stays a clean circle for the lead-in chamfer.

**Assertions a grader checks:**

- [ ] Rejects cutting the bore at exactly 6.35 mm nominal.
- [ ] States the FDM small-vertical-hole undersize magnitude as ~0.1–0.3 mm.
- [ ] Recommends either ~0.4–0.5 mm diametral clearance (plain bore) or the
      ribbed-bore approach with 3 ribs (preferred for a repeatedly-used
      grip).
- [ ] If ribbed bore is chosen: states the ribs stop below the mouth, leaving
      a clean circular opening for the lead-in chamfer.

**Skill that should fire:** `part-joints`.

**Traces to:**

- `.claude/skills/part-joints/references/bores-and-ribs.md` — "Never cut a
  bore at nominal" and "Ribbed bores."

**Skill-less failure mode:** models the bore at exactly 6.35 mm "to match the
shank," which prints as a press fit rather than a one-handed drop-in fit, or
compensates with an ordinary clearance bore (a full-circle wall) that is wide
enough not to jam but then rattles — because a plain clearance bore has no
mechanism to take up bore-to-bore print variance the way a compliant rib
does.

---

## S11: Engraved decimal label at font_size=4

**Prompt:** "I'm engraving a size label '2.5' at `font_size=4`, regular
weight, into a drill-bit holder. It looks fine in the viewer. Any concern
before I print it?"

**Expected answer (tolerance in parentheses):**

- Yes. At regular weight the period is only about **0.41 mm** wide — about
  one nozzle width — and often **vanishes on print**, turning "2.5" into
  "25." The viewer renders the vector glyph faithfully and gives no signal
  that a stroke this thin will not survive slicing.
- The fix is `font_style=FontStyle.BOLD`, which grows the period to about
  **0.70 mm** while roughly doubling stroke width generally, at no cost to
  size, spacing or alignment.
- Secondarily, `font_size=4` renders digits at only ~0.75× that height
  (~2.97 mm) — at the repo's 3 mm absolute floor, not comfortably inside it;
  worth flagging if legibility (not just the decimal point) matters.

**Assertions a grader checks:**

- [ ] Specifically flags the decimal point / period as the concrete risk, not
      a generic "text might be small" caution.
- [ ] Gives the period width figures: ~0.41 mm regular vs. ~0.70 mm bold (or
      "about one nozzle" vs. "comfortably above one nozzle").
- [ ] Recommends `FontStyle.BOLD` as the fix.
- [ ] Notes the digit height at `font_size=4` is ~2.97 mm, i.e. at/near the
      3 mm floor, not the nominal 4 mm.

**Skill that should fire:** `printed-text`.

**Traces to:**

- `.claude/skills/printed-text/SKILL.md` — "The two traps" and the measured
  glyph table ("Measured on this repo's default system sans at font_size=4").

**Skill-less failure mode:** takes "looks fine in the viewer" as sufficient
verification and ships the label as specified. The viewer is a faithful
vector render and gives no warning; the decimal point silently fails to
survive slicing on a 0.4 mm nozzle, and the defect is discovered only after
a print run of labelled parts comes out reading "25" instead of "2.5."
