# Measuring from photos

Detail behind SKILL.md's workflow: where the error actually comes from, what a
photo can and cannot resolve, and how to read specific features.

## The error budget

Five sources, largest first for a typical phone photo of a palm-sized part.
Only the last two are worth optimising, and most people optimise the wrong one.

| Source | Typical size | Fix |
|---|---|---|
| **No scale reference** | unbounded | Put one in frame. Nothing else matters until this is done. |
| **Scale reference not coplanar** | 2–10% | The reference must lie in the same plane as the feature. A rule *beside* a tall part is measuring the table, not the part. |
| **Perspective** | 1–8% across the frame | Shoot square-on from far back; rectify what is left. |
| **Corner-click error in the homography** | 0.2–1% | Zoom in to place them. This error scales every measurement. |
| **Endpoint-click error** | ±2 px, so ±0.3 mm at 12 px/mm | Zoom in. This error is per measurement and averages out over repeats. |

`rectify_roundtrip` in the eval recovers a known 40 mm segment through a
synthetic oblique shot with **0.000 mm** of error, so the transform contributes
nothing. Every millimetre you are wrong by came from the four corners, the
reference, or the shot.

### Barrel distortion

Phone wide-angle lenses bow straight lines by 1–3% near the frame edge, and a
four-point homography cannot model it — it assumes straight lines stay straight.
Two mitigations, in order of preference: keep the part in the middle third of
the frame, and shoot with the main (not ultra-wide) camera. A straight edge that
visibly bows in the photo is the tell; re-shoot rather than correcting it.

## What a photo can and cannot resolve

**Can, reliably**: outline and profile, feature *placement* on a visible face,
counts (holes, ribs, teeth, slots), proportions and ratios, symmetry, which face
is which, roughly where a parting line or a lid seam runs.

**Can, with a coplanar scale reference and a square-on shot**: absolute
dimensions of features on that one face, to a few tenths of a millimetre.

**Cannot, at all**: wall thickness, depth of a blind hole or pocket, internal
ribs and bosses, draft angle, thread pitch and class, material, and anything
behind the front surface. The eval's `hidden_cavity` scenario is this stated as
a number: 25% of a part's material can vanish without changing a single
silhouette.

Depth along the camera axis is the sneaky one. It is not measurable from a
square-on shot at all, and from an oblique shot only if you can identify the
same feature in two views with a known angle between them. In practice: measure
depth with a depth gauge, or take it from a datasheet, or mark it `ASSUMED` and
print a test.

## Reading specific features

**A circular hole** photographs as an ellipse unless the shot is exactly
square-on. Its **major** axis is the true diameter — the minor axis is the
foreshortening. Measure the major axis, and treat a large major/minor ratio as a
warning that the whole face is oblique and everything else on it is wrong too.

**A fillet or a chamfer** cannot be told apart at low resolution and both read
as a soft edge. Look at the highlight: a fillet gives a continuous gradient, a
chamfer gives a distinct band with two hard boundaries. When it is genuinely
ambiguous, choose per `AGENTS.md` — chamfer horizontal edges, fillet vertical
ones — and note the choice as an assumption.

**A repeating pattern** should be measured across the whole run and divided, not
one pitch at a time. Ten holes measured end to end and divided by nine gives a
pitch nine times more precise than any single gap.

**Hardware in frame** is a free scale reference and a free datasheet. An M3
socket head cap screw, a 608 bearing, a USB-C receptacle, a 18650 cell, a
standard DIN rail: identify it, take its dimensions from the standard, and use
it to calibrate the photo instead of measuring it.

**Text and markings** are often the highest-value thing in the frame — a part
number turns the whole job into a datasheet lookup. Read them before measuring
anything.

## Writing the ledger into a model

One constant per ledger entry, with provenance in the comment. The shape to aim
for in a package's `config.py`:

```python
# measured: photo_measure, front view, +/-0.31 mm
BODY_WIDTH = 48.2
# datasheet: 608ZZ bearing, ISO 15:2017
BEARING_OD = 22.0
# ASSUMED: not visible in any photo; depth gauge or print test needed
POCKET_DEPTH = 6.0
```

Two properties this buys, both of which matter more than they look:

- `grep -rn ASSUMED models/<name>/` lists everything standing between the model
  and a confident print. That list should be empty, or knowingly non-empty,
  before a final print — never accidentally non-empty.
- A measured constant carries its own error bar, so the next reader can see at a
  glance that `BODY_WIDTH` is not a caliper reading and must not be used to
  derive a clearance.

Clearances themselves never appear in this list. They come from
`models/lib/fits.py` via `fdm-fits-and-clearances`, because a photo shows you
the *original designer's* clearance for *their* printer and material, which is
not evidence about yours.

## When to stop measuring and print

A fit test beats another hour of measuring. The moment the ledger has the
mating dimensions bracketed to within a couple of tenths, print the smallest
piece of geometry that tests the fit — a 5 mm tall ring of the bore, a stub of
the rail, the pocket alone — and measure the printed result instead. That closes
the loop on the printer, the material and the measurement all at once, which no
amount of image processing does.
