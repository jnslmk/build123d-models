# Printable threads

Threads printed directly into the part - screw-on lids, caps, coarse
adjusters, jar-style closures, and printed male threads that mate with real
metal nuts.

## Contents

- [Overhang: the profile choice](#overhang-the-profile-choice)
- [Where the clearance goes](#where-the-clearance-goes)
- [Clearance defaults](#clearance-defaults)
- [Minimum sizes](#minimum-sizes)
- [Modelling rules](#modelling-rules)
- [ISO tolerance classes are a dead end](#iso-tolerance-classes-are-a-dead-end)
- [Sources](#sources)

## Overhang: the profile choice

With the thread axis vertical (the only orientation worth printing), let the
flank angle **beta** be measured from the plane perpendicular to the axis -
i.e. from horizontal. Then the underside of each flank presents an overhang of
**90 deg - beta**.

Two rows below are named by **beta directly** (Custom 45 deg V, DIN 405) and
two are named by their standard's **included** angle, with beta derived as
half of it (ISO metric V, Acme/trapezoidal) - do not infer beta from the row
name the same way for every row; the "Overhang" column is the one number that
is always `90 - beta`, computed after beta is known.

| Profile                    | beta   | Overhang | Verdict               |
| --------------------------- | ------ | -------- | ---------------------- |
| Custom 45 deg V (named by beta) | 45     | 45       | Ideal, meets the rule  |
| ISO metric V (60 deg included) | 30     | 60       | Best of the standards  |
| Round / knuckle DIN 405 (named by beta) | <= 30  | <= 60    | Best for screw lids    |
| Acme (29 deg included)      | 14.5   | 75.5     | Pure bridging          |
| Metric trapezoidal (30 deg included) | 15     | 75       | Pure bridging          |
| Square                      | 0      | 90       | Worst                  |

ISO metric threads have a 60 deg **included** angle, so each flank sits 30 deg
from the perpendicular: `90 - 30 = 60`. Acme is 29 deg included (14.5 deg
flanks): `90 - 14.5 = 75.5`. Metric trapezoidal is 30 deg included (15 deg
flanks): `90 - 15 = 75`. The two are close enough that "about 75" is the right
mental model, but they are not the same profile and the exact figures differ.
DIN 405 round thread has a 30 deg flank angle with fully rounded crests and
roots.

Sources: [ISO metric screw thread][iso-metric], [Acme thread form][acme],
[DIN 405 round thread][din405]

### The common advice is backwards

"Acme prints better than V-threads because the flanks are flatter" is
geometrically wrong on overhang. Flatter flanks mean a **smaller** beta, which
means a **larger** overhang angle. A 14.5 deg Acme flank is a 75.5 deg
overhang - almost a bridge - while a 30 deg ISO flank is a 60 deg overhang and
a 45 deg custom V exactly meets the 45 deg rule.

Acme's real merits are elsewhere, and they are genuine:

- a **blunt crest**, which survives the first layer of each thread turn
  instead of printing as a knife edge,
- a **thick root**, which is where a printed thread actually fails,
- and generous axial clearance built into the standard, which forgives
  layer-scarring.

So: pick Acme for a load-carrying leadscrew where root thickness dominates.
Pick a 45 deg custom V or a DIN 405 round profile for a screw-on lid, where
surface finish and easy starting dominate. Do not pick Acme *because of*
overhang.

## Where the clearance goes

This matters by roughly 3x, and getting it wrong produces the confusing
failure mode of a thread that both rattles radially and binds axially.

- **V-threads (ISO metric, custom 45 deg): apply clearance radially.** Shrink
  the **major diameter** of the male thread (or grow the female). On a
  V-profile the flanks are steep, so a radial shift moves the flanks apart
  along their normal - which is what you want.
- **Trapezoidal, Acme, square: apply clearance axially.** Thin the **tooth**
  (reduce the thread thickness along the axis). On a shallow-flank profile a
  radial shift barely separates the flanks at all, while it does open a radial
  gap - so radial clearance on an Acme thread gives you slop without
  relieving the bind.

If a printed thread is stiff to turn but wobbles when it stops, the clearance
was applied on the wrong axis for the profile.

## Clearance defaults

Total diametral clearance unless noted:

| Case                                   | Clearance |
| -------------------------------------- | --------- |
| Printed male + printed female, V       | 0.40 mm   |
| First attempt, or PETG                 | 0.50 mm   |
| Well-calibrated printer, M10 and below | 0.30 mm   |
| Printed female + real metal bolt       | +0.30 mm on female major dia. |
| Any thread with a **horizontal** axis  | 2x the above |

The horizontal-axis doubling is not a safety factor - a horizontal thread
prints its upper flanks as overhangs of the *sum* of the flank angle and the
local helix angle, and sags accordingly. Prefer to reorient; if the axis must
be horizontal, double the clearance and expect to clean the thread up.

## Minimum sizes

- **Printed female + metal bolt: M6 x 1.0 and up.** Below that the female
  crest is thinner than a couple of extrusions and shears off.
- **Printed on printed: M8 x 1.25 minimum, prefer M10 x 1.5.**
- **Below M5 under load: do not print the thread. Use a heat-set insert.**
  See [heat-set-inserts.md](heat-set-inserts.md).
- **Do not use standard coarse pitch on small printed threads.** Standard
  pitch scales with diameter and gets absurdly fine at the small end: M6 x 1.0
  puts a 0.5 mm-tall tooth into a 0.4 mm nozzle's world.
- If **both** parts are yours, override the standard: **M6 x 2.0** instead of
  M6 x 1.0. A coarser pitch at the same diameter gives a taller, thicker tooth
  with the same overhang angle, and it assembles faster.

## Modelling rules

- **Thread axis always vertical.** Everything above assumes it.
- **Fade the thread in over 90-360 degrees.** Never start a thread at a
  knife-edge - it curls off the bed or off the previous layer and then the
  nozzle drags it.
- **Never start the thread at z = 0.** Leave at least **one full pitch of
  plain collar** below it, chamfered 0.5-1.0 mm. This is the repo's standard
  bottom-ring chamfer doing double duty as a thread lead-in. It is also what
  keeps the mouth's lead-in cone from cutting into the thread's first turn —
  cut the two into each other and OCC's fuse silently returns the thread alone
  instead of the part (`build123d-geometry-ops`, `references/gotchas.md` §7).
- **Crest and root flats >= one extrusion width (0.4 mm).** A crest narrower
  than the nozzle cannot be printed; the slicer either drops it or fattens it
  unpredictably.
- **Root fillet >= 0.2 x pitch.** The root is the stress riser and the failure
  site.
- **3-4 perimeters minimum**, so the whole thread is perimeter and never
  infill. A thread printed partly in infill is a thread that shears.
- **Engagement length >= 1.0 x D, prefer 1.5 to 2.0 x D.** Printed threads
  share load across turns much worse than metal ones, so buy extra turns.
- **Layer height <= pitch / 6.** Fewer than about six layers per pitch and the
  helix visibly staircases into a set of rings.
- Add a lead-in chamfer at the thread mouth (boolean `Cone`, per the repo's
  house style) so the mating part starts square.

## ISO tolerance classes are a dead end

It is tempting to reach for a standard fit class - "just use 6g/6H" - and let
the standard supply the clearance. It does not work at printing scale.

For external threads, tolerance position **g** has fundamental deviation
**es = -(15 + 11P) micrometres**, with P the pitch in millimetres.
Source: [ISO 965-1, Table 1][iso965]

Work it for M10 x 1.5: `15 + 11 x 1.5 = 31.5`, so **es is about -32 um**, i.e.
0.032 mm. The printed thread wants roughly 0.30-0.40 mm - **about 10x more**.

The second trap is reaching for a bigger grade number to fix that. It does not
help: the **grade number (4, 6, 8, ...) widens the tolerance band**, it does
not shift the thread away from basic size. The offset from basic size is set
by the **letter** (the fundamental deviation), and the letters available stop
far short of what FDM needs.

So do not label a printed thread "6g" or "7g6g" - it is not one, and calling
it one misleads anyone who later tries to gauge it. Instead:

1. Model the **basic profile** (ISO 68-1 geometry, zero allowance).
2. Apply an explicit millimetre offset from the clearance table above.
3. **Document it as a non-standard printing offset**, in a named constant,
   e.g. `THREAD_CLEARANCE = 0.40  # total diametral, printed-on-printed V`.

## Sources

- [ISO metric screw thread (60 deg included angle)][iso-metric]
- [Acme thread form (29 deg included angle)][acme]
- [DIN 405 round / knuckle thread (30 deg flank angle)][din405]
- [ISO 965-1, ISO general purpose metric screw threads, tolerances][iso965]

[iso-metric]: https://en.wikipedia.org/wiki/ISO_metric_screw_thread
[acme]: https://en.wikipedia.org/wiki/Trapezoidal_thread_form
[din405]: https://www.gewindebohrer.de/en/service/thread-standards/round-thread-din-405
[iso965]: https://cdn.standards.iteh.ai/samples/57778/765c17fc0f7946ff850db22b43920f09/ISO-965-1-2013.pdf
