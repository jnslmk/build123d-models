---
name: fdm-fits-and-clearances
description: Chooses and records clearances for 3D-printable build123d models instead of re-guessing a number per part. Maps a mating requirement to a named fit class (press, snug, sliding, free) from models.lib.fits, adjusts it for material (PETG baseline, plus PLA, ABS, ASA, TPU), and compensates bores that FDM prints undersize. Use when picking a clearance, tolerance, gap or allowance between mating parts; sizing a bore, hole, shaft, socket, pocket or lid; deciding a press fit, interference fit, snug fit, sliding fit, running fit, free fit or snap fit; turning a nominal hardware dimension (bolt, magnet, bearing, heat-set insert, dowel) into a CAD dimension; or reasoning about shrinkage, warping, elephant's foot, minimum wall thickness, minimum feature size, overhang or bridging limits on the printers this repo targets.
---

# FDM fits and clearances

The master numeric reference for this repo. Every clearance decision starts here, and
every clearance constant that ships must be traceable back to a row in
`references/fits.md`.

## The problem this exists to stop

Clearance constants in this repo were each derived independently, with no recorded
rationale:

| Constant | File | Value |
|---|---|---|
| `CLEARANCE` | `models/round_snap_box.py` | `0.3` |
| `LID_PLUG_CLEAR` | `models/led_psu_enclosure/config.py` | `0.3` |
| `VENT_CLEAR` | `models/led_psu_enclosure/config.py` | `0.35` |
| `HEX_CLEARANCE` | `models/drill_storage_hex.py` | `0.15` |
| `STEP_CLEARANCE` | `models/satellite_led.py` | `0.5` |

Five numbers, five different intents, none of them stated. A later reader cannot tell
whether `0.3` was measured, guessed, or copied from a page about an industrial machine —
so nobody can safely change it. Naming the fit class fixes that: the next argument is
about *the fit*, not about an anonymous float.

## Rule 1 — pick a fit class, do not invent a number

Import the class. Do not type a literal.

```python
from models.lib import fits

LID_PLUG_CLEAR = fits.SLIDING  # sliding fit, PETG baseline
```

| Class | Value (mm, diametral) | Use it when |
|---|---|---|
| `fits.PRESS` | `-0.10` | Assembled with force, not meant to come apart. Dowels, pins, permanent bosses. |
| `fits.SNUG` | `+0.10` | Goes together by hand, no perceptible play. Locating features, alignment tabs. |
| `fits.SLIDING` | `+0.22` | Moves freely along its axis while staying located. Lids, slides, shafts, plug skirts. |
| `fits.FREE` | `+0.40` | Drops in with clearance to spare. Tool holders, drop-in captives, loose dowels. |

All four are **diametral** — the total gap between the two parts, not the gap per side.
A bore that must clear a 6.00 mm shaft with a sliding fit is `6.00 + fits.SLIDING`, not
`6.00 + 2 * fits.SLIDING`. Getting this wrong doubles or halves every fit in the model,
and it is the most common mistake when porting a number in from a web page that did not
say which convention it used.

The full ladder, with the three published sources it reconciles and the disagreements
between them, is in `references/fits.md`.

## Rule 2 — the baseline material is PETG

`models/lib/fits.py` is calibrated against PETG. Any model that prints in something else
adjusts through `for_material`:

```python
from models.lib import fits

BORE_CLEAR = fits.for_material(fits.FREE, "pla")  # free fit, PLA
```

`for_material` raises `ValueError` on an unknown material rather than silently returning
the PETG number, because a wrong clearance is invisible until the parts are printed.

Known materials and their offsets from the PETG baseline: PLA `-0.10`, PETG `0.00`,
ABS `-0.15`, ASA `-0.15`, TPU `+0.10`. The reasoning for each, and the per-material
sliding/rotating/snap-fit table those offsets came from, is in `references/fits.md`.

## Rule 3 — every clearance constant carries a comment

**House rule.** A clearance constant in a model file is not allowed to stand alone. It
carries a comment naming its **fit class** and its **material baseline**:

```python
LID_PLUG_CLEAR = fits.SLIDING              # sliding fit, PETG baseline
HEX_CLEARANCE = fits.SNUG                  # snug fit, PETG baseline
BORE_CLEAR = fits.for_material(fits.FREE, "pla")  # free fit, PLA
```

If a model genuinely needs a value that is not a fit class — a functional gap rather than
a fit, such as the 1.5 mm drop-in relief in `models/led_psu_enclosure/config.py` — the
comment says so and says why:

```python
SHELF_DROP_CLEAR = 1.5  # not a fit: hand clearance to drop the shelf past the rim
```

The test is simple. If the comment does not let the next reader decide whether to change
the number, the comment is not finished.

## Rule 4 — never cut a bore at nominal

FDM prints small vertical holes **undersize**. A 5 mm hole modelled at exactly 5.00 mm
came out **0.24 mm small** in a PLA test on a 0.4 mm nozzle; external diameters go the
other way, printing about **+0.10 mm oversize**
([Creative3DP](https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/)).
The nozzle drags the inner perimeter inward on a concave curve and piles material up on
the inside of the arc.

So a bore cut at nominal is already a press fit before you have chosen a fit at all.
Always add the fit class on top of nominal:

```python
BORE_D = SHANK_D + fits.FREE  # free fit, PETG baseline — drop-in tool bore
```

Two consequences worth internalising:

- **Compensation is not symmetric.** Holes shrink, shafts grow. If both halves of a joint
  are printed, the error budget is roughly `0.24 + 0.10 = 0.34 mm` before you have spent
  any clearance — which is exactly why the house `FREE` is `0.40` and not the `0.10–0.20`
  an industrial vendor quotes.
- **Bridged holes are worse.** A hole whose axis lies in the XY plane has an unsupported
  crown that sags into a D-shape. Add another `+0.1–0.2 mm`, or orient the hole so its
  axis is along Z.

## Rule 5 — do not port industrial numbers

Markforged quotes `0.00–0.05 mm` for a press fit and `0.10–0.20 mm` for a fit that
"slides and rotates easily"
([Composites Design Guide](https://support.markforged.com/hc/en-us/articles/360001308239-Composites-Design-Guide)).
Those figures are real, and they are for a closed-loop industrial machine printing Onyx.
On a desktop FDM printer the error budget — nozzle wander, over-extrusion, first-layer
squish, thermal shrink — is *several times larger than the clearance itself*, so a
Markforged press fit becomes an unassemblable weld and a Markforged running fit becomes a
press fit.

**This is the single biggest cause of a fit that welds solid.** If a number came from an
industrial vendor's guide, it is a lower bound on what is physically possible, not a
value to type into a model.

## Rule 6 — calibration outranks every number here

Every figure in this skill assumes a **0.4 mm nozzle, 0.15–0.2 mm layers, and calibrated
flow**. An uncalibrated extrusion multiplier swamps all of it: over-extrusion eats
`0.1–0.2 mm` off the inside of every hole, which is the whole of a snug fit and half of a
sliding one. If press fits feel impossible on a machine, the flow rate is the first
suspect, not the CAD
([Creative3DP](https://tools.creative3dp.com/tools/hole-tolerance-calculator/)).

Printer-specific baselines are in `references/printers.md`.

## Rule 7 — a typed constant that equals a derived envelope dimension is the bug, not a coincidence

If a clearance-adjacent constant matches another dimension in the same file to the
decimal, that is not confirmation the number is right — it means nobody wrote the
relationship down, so nobody could see it collide. Two real instances, both from
`models/led_profiles`:

- `mount_config.BOSS_U` was typed as `19.5`, which is `mount_config.ARCH_HALF_W`
  (also `19.5`) exactly. The strap's bolt axis sat *on* its own arch flank: the
  hole's mouth came out bisected by the arch springing and an M4 head fouled the
  flank by 2.6 mm, so the strap could not be bolted down
  (`models/led_profiles/mount_config.py:99-111`). `BOSS_U` is now
  `arch_half_width(FOOT_H) + BOLT_HEAD_D / 2 + BOLT_HEAD_CLEAR` — derived from the
  envelope it has to clear the flank by, not typed against it.
- `feet.PAD_U_OUT` was `26.0`, which is `HOLE_U + EYE_CBORE_D / 2` (also `26.0`)
  exactly. The eye foot's M6 nyloc pocket had a zero-thickness outboard wall, on
  the one part in the family rated for 20 kg of shock, and the same tangency
  stopped OCC chamfering that pad's rim at all (`models/led_profiles/feet.py:66-80`).
  `PAD_U_OUT` is now `HOLE_U + max(EYE_CBORE_D, WALL_CBORE_D) / 2 + PAD_WALL`, with
  `PAD_WALL` a named minimum wall rather than an accident of arithmetic.

Same class both times: a constant that should have been written as an expression
got typed as its evaluated result instead, so the relationship it depends on
became invisible and free to drift the moment either end moved.

**When a clearance-adjacent constant goes into a model, ask what it has to clear,
and check whether that quantity is already a constant in the same file.** If the
two match, write the dependent one as the derivation — even a one-line one — so
the next person who moves the other end of that relationship gets a changed
number instead of a silent collision.

## Procedure

1. **State the requirement in words first.** "The lid must drop on and come off by hand
   without rattling" — that is a sliding fit. "The dowel must never come out" — press.
2. **Pick the class** from the table above.
3. **Adjust for material** with `for_material` if the model is not PETG.
4. **Adjust for scale and orientation** if either applies — see the scaling rules in
   `references/fits.md`. Large parts and bridged holes need more; sub-20 mm² features
   tolerate less.
5. **Write the constant with its comment** (Rule 3).
6. **Verify in code, not in the viewer.** A clearance is invisible in a projection.
   Point-sample the solid to confirm the gap exists — see the `build123d-geometry-ops`
   skill.
7. **If the fit matters and the geometry is unusual, print a test coupon** rather than
   trusting the table. Three variants at ±0.1 mm around the chosen value costs one short
   print and settles the question permanently.

## When to leave the ladder

The fit classes cover *cylindrical and prismatic mating features*. They are the wrong
tool for:

- **Snap beads and cantilever arms** — engagement is `bead − clearance`, and the
  clearance is the sliding fit of the joint it lives in. See
  `models/led_psu_enclosure/config.py`, where `SNAP_BEAD = 0.6` over a
  `LID_PLUG_CLEAR = 0.3` leaves 0.3 mm of engagement.
- **Ribbed bores**, where the tool rides on three line contacts instead of a full-circle
  wall. Cut the valley loose and let the ribs set the grip — see `AGENTS.md`.
- **Functional gaps** (finger clearance, cable routing, airflow), which are not fits at
  all and should not borrow a fit constant.

## References

- `references/fits.md` — the fit ladder with its source disagreements, per-material
  clearances, dimensional reality (tolerance, shrinkage, hole compensation), minimum
  printable features, and scaling rules.
- `references/printers.md` — the machines this repo targets and the baseline assumed
  throughout.
