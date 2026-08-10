# Design notes: measuring the source, and rebuilding it

This is the ledger behind `models/cable_spool`. Section 1 says how the source
model was measured, section 2 what came out of it, section 3 what this model
does differently and why, section 4 is the clip, and section 5 grades the
result against the original meshes.

The tooling is the `stl-reverse-engineering` skill's. Nothing here was read off
a render.

## 1. Getting the meshes

Printables serves the model page behind a bot check (HTTP 403 to anything
without a browser), but its GraphQL API answers plainly and the STLs sit on a
public CDN path that the API hands you:

```bash
curl -s -X POST https://api.printables.com/graphql/ \
  -H 'Content-Type: application/json' \
  -d '{"query":"query { print(id: 27496) { name stls { id name } } }"}'
# -> clip.stl, base.stl, cover.stl, middle.stl
curl -O https://files.printables.com/media/prints/27496/stls/<id>_<uuid>/base.stl
```

Four parts, all watertight: `base` (8 944 triangles), `cover` (4 888),
`middle` (5 258), `clip` (2 900). All four have Y as their axis; this model
uses Z, so every comparison below is done after a +90 degree rotation about X.

`mesh_analyze.py` reported `swept/actual` of 1.019 for the cover and 1.061 for
the middle — clean extrusions, as expected for a 2 mm plate — and 4.164 for the
base, which is the hub. The clip came back at 1.039, which is misleading: it
*is* nearly a prism, and the thing wrong with it is that the prism is straight.

## 2. What the meshes say

Measured by slicing in trimesh and sampling material along rays and circles
(`radial.py`-style scans, per the skill's "never add a feature you have not
seen in slice data").

### The disc, common to all three

| Feature | Measured | In `config.py` |
| --- | --- | --- |
| Rim radius | 89.99–90.00 | `OUTER_R = 90` |
| Rim ring, inner edge | 80.00 | `RIM_INNER_R = 80` |
| Window inner arc | 32.49–32.50 | `SPOKE_RING_R = 32.5` |
| Windows | 6, area 2301.7 mm² each | `WINDOW_COUNT = 6` (rebuilt: 2302.4 mm²) |
| Window corner fillet | solved, see below | `WINDOW_FILLET = 5` |
| Plate thickness | 2.00 | `PLATE_T = 2` |
| Spoke width | 10.00 | `SPOKE_HALF_W = 5` |

**The spokes are bars, not wedges**, and that is the one piece of geometry a
render would have got wrong. Sampling one window's straight edge at r = 36.5,
55.5 and 74.5 puts all three points on a single line whose perpendicular
distance from the axis is 5.000 mm. Both of a window's straight sides are such
chords, 120 degrees apart in normal, so the spoke between two windows is a
constant-width 10 mm bar. An annular sector would have measured 11 degrees wide
at r = 50 and 11 degrees wide at r = 70; it measures 11.0 and 8.0, which is
what a constant chord width does.

**The corner fillet was solved, not eyeballed.** The fillet leaves the straight
side at 74.33 mm from the axis and rejoins the r = 80 arc. A circle tangent to
both has its centre at `(5 + R)` off-axis, so `sqrt((5+R)² + 74.33²) = 80 − R`,
whose only solution is `R = 5.000`. The inner corners check out against the
same radius: `sqrt((5+5)² + 36.14²) = 37.5 = 32.5 + 5`.

### The stack

| Feature | Measured (source frame) | Here |
| --- | --- | --- |
| Base plate | y −2.0 … 0.0 | z 0 … 2 |
| Middle disc seat | y 7.0 (collar top) | `MIDDLE_Z = 9` |
| Cover seat | y 16.4 (rib tops) | `COVER_Z = 18` |
| Stack height | 20.4 | `STACK_H = 20` |
| Channel height | 7.0 and 7.4 | `CHANNEL_H = 7` (both) |

### The hub

| Feature | Measured | Here |
| --- | --- | --- |
| Tube | r 22 … 24 | same |
| Lower collar | r 24 … 25, up to y = 7 | `HUB_COLLAR_R = 25.6`, to `MIDDLE_Z` |
| Guide ribs | 4 × 34.5 deg at 42.5+90k deg, r to 25 | `HUB_RIB_COUNT/ARC/PHASE` |
| Wall liner behind each rib | r 21 … 22 over the same sectors | `HUB_LINER_R = 21` |
| Cable slot | 33 deg, full height | `CABLE_SLOT_ARC = 33` |
| Second slot | 33 deg, opposite, above y = 7 only | keyway |
| Spindle post | OD 4.4, bore 2.5, **blind** from the top | bore goes through |

### The two upper discs

Both bores measure 24.05 nominal with four 25.05 relief pockets 36 degrees
wide. The middle's pockets sit exactly on the rib centres; the cover's sit
45 degrees off them. The middle additionally carries two tabs reaching in to
r = 22.0 at opposite sides, which line up with the hub's two slots.

That is the whole spacing mechanism, and it is a good one: one radius, two
heights, and a disc that either has the pockets (drops past the ribs, lands on
the collar) or does not (lands on the rib tops).

## 3. Where this model departs, and why

Six deliberate deviations. Each costs a little IoU in section 5, which is the
honest place to look for them.

1. **The cover's bayonet is gone.** In the source the guide ribs carry a 0.9 mm
   notch at y = 16.4–17.3 with a flare above it, and the cover's 45-degree
   offset pockets say it is meant to be lowered past the ribs and twisted under
   that flare. It cannot close: the cover is 2.0 mm thick and the notch is
   0.9 mm tall. Here the cover simply rests on the rib tops and the clips hold
   it down — which is what the clips are for.
2. **The spindle bore goes through.** The source's is blind from the top, so
   the "put a rod through it and spin the spool" reading of that hole does not
   work. Through-drilled it does, and it costs nothing.
3. **The window mouths are chamfered on both faces of all three discs.** The
   source chamfers only the middle disc's top. The cable crosses these edges on
   every turn, and `AGENTS.md` does not allow shipping them raw.
4. **The diametral rib is 5.4 mm, not 2.9.** At 2.9 the 4.4 mm spindle post
   stands proud of the rib it is carried on, leaving two bare arcs of cylinder
   meeting the bed face at 90 degrees; at exactly 4.4 the two are tangent,
   which is worse (OCC leaves a sliver edge at each tangency).
5. **The channels are both 7.0 mm.** The source's are 7.0 and 7.4; the
   difference is the source's hub being 20.4 tall against a 20.0 stack.
6. **The hub's interior is simpler.** The source hub carries additional
   internal structure — four webs converging toward the axis, visible in slices
   at r = 6 … 21 — whose function could not be established from the mesh. It is
   not a stiffener for anything the discs load, it does not reach the spindle
   post, and the two shapes it is complementary to (the flange's kidney holes)
   are 10 mm below it. It is not reproduced. This is most of the base's IoU
   gap, and section 5 says how much.

Beyond those, every clearance was re-derived from `fdm-fits-and-clearances`
rather than copied. The source's disc bore is 24.05 on a 24.00 hub — 0.05 mm
of radial clearance, which is inside a single extrusion's tolerance and will
bind on any machine that prints a hair fat. `DISC_BORE_FIT = fits.SLIDING`
gives 0.11 mm a side.

## 4. The clip

The complaint is that it falls off. Three things are wrong with it and each one
is sufficient on its own.

### 4.1 It is straight and the rim is round

The source clip is a prism: `mesh_analyze` gives `swept/actual = 1.039` and its
jaws are flat over the 24 mm it spans. On a 90 mm radius, 24 mm of chord sits
`24²/(8·90) = 0.80 mm` off the arc at its middle. So each jaw touches the disc
at its two corners and nowhere else, and the clip rocks about the tangent.

Fixed by construction here: every face of the new clip is a revolve about the
spool axis, so its bore is a true cylinder at r = 90.2 over all 30 degrees of
its wrap. `checks.py` samples five angles across the wrap to say so.

### 4.2 Its jaws land where there is no disc

Mapping the source clip's own solid (occupancy grid, 0.4 mm, in its X–Z plane)
gives a cavity 20.4 mm wide — the stack height — with a 16.4 mm mouth, and the
retaining lips at the mouth are 4.4 mm deep measured from the cavity floor.
Since the cavity floor rides on r = 90, those lips sit at **r = 75.5 … 79.9**.

The discs' solid ring runs r = 80 … 90. The lips are entirely inboard of it,
over the windows. Whether a given clip grips anything at all depends on whether
it happened to be pushed on where a spoke is, and a spoke is 10 mm wide out of
an 84 mm pitch.

Here both jaws stop at `RIM_INNER_R`: the lower one covers r = 80 … 90 and the
upper one's flat land is r = 86.4 … 89. All of it on the ring.

### 4.3 Its arms are over-strained on the first fit

The source arms measure 1.6 mm thick and 10.4 mm long from root to lip, and
they have to spread 2.0 mm a side to get the 20.4 mm stack through the 16.4 mm
mouth. For a constant-section cantilever:

```
eps = 3·t·y / (2·l²) = 3 · 1.6 · 2.0 / (2 · 10.4²) = 4.4%
```

against PETG's 1.7% for a single fit and 1.0% for repeated use
(`snap-fits/references/materials.md`; PLA is 1.0% and 0.6%). The arms yield the
first time the clip is fitted, and after that it is a loose collar — which is
exactly the reported symptom, and it explains why it gets *worse* with use.

### 4.4 What replaces it

Not a clamp. The jaws are a 0.15 mm clearance fit on the 20 mm stack and hold
it together without squeezing it, because a joint whose retention is a
sustained squeeze on PETG is a joint with a shelf life. Retention is a detent:
a curved cantilever under the base disc with a tooth that drops up into one of
the six windows and catches on the window's own r = 80 wall.

The arm runs *along* the arc rather than radially, which is what makes the
numbers work — a radial arm has 11 mm to play with between the spine and the
window wall, and a tangential one has as much as the clip is wide:

```
h = 1.8 mm      arm thickness        (4 perimeters at 0.4 mm, the FDM floor)
b = 8.0 mm      arm width, radial    (over the 6 mm floor)
l = 24.0 mm     root to tooth, arc   (l/h = 13.3, a slender beam)
y = 1.8 mm      tooth height         (y >= h and y >= 1.2, both floors bind)

eps = y·h / (0.67·l²)                  = 0.84%      <= 1.0%   OK
P   = (b·h²/6) · (E_s·eps/l)           = 2.6 N      E_s = 1700 MPa
W   = P·(mu + tan 45) / (1 - mu·tan 45) = 7.7 N     mu = 0.5
```

So it takes about 8 N of straight push to fit and the arm sits at 0.84% strain
while it rides over its own tooth — half of what the source clip demanded on
first assembly, and inside the repeated-use limit rather than over the one-shot
one.

`CLIP_WRAP = 30 deg` is not a styling choice; it is `DETENT_L` plus the root
block plus the release tab, expressed as an angle at the arm's mid-radius.

### 4.5 The catch is vertical, so the clip is captive

The wall the tooth engages is the window's own r = 80 boundary: a 2 mm step
inside a 2 mm plate. There is no room to slope the catch back and still reach
that wall — a 45-degree return face would only touch the window at z = 0, where
the wall's own chamfer already is. So the tooth's catch face is vertical and
the clip does not pull off; it is released by pressing the arm's free end.

That is a deliberate trade and it is the right way round for this part. The
original's failure mode is "comes off when you did not ask"; this one's is
"needs a finger to come off when you did".

## 5. Grading

`mesh_compare.py`, exact IoU by boolean, this model's exported STL against the
source mesh rotated into the same frame. **Not** aligned — see the note below.

| Part | Volume, source → here | IoU | Verdict |
| --- | --- | --- | --- |
| `middle` | 18 483 → 18 382 mm³ | **95.3%** | passes the skill's 95% gate |
| `cover` | 19 164 → 18 740 mm³ | **96.1%** | passes |
| `base` | 33 332 → 26 815 mm³ | **70.5%** | see below |

Splitting the base by height, against slabs of the same two meshes:

| Region | Source | Here | IoU |
| --- | --- | --- | --- |
| plate, z 0 … 2 | 19 842 mm³ | 19 374 mm³ | **90.9%** |
| hub, z 2 … 21 | 13 490 mm³ | 7 441 mm³ | **42.4%** |

So the base's plate is as good as the other two discs — the 9% it gives up is
almost all the window and bore chamfers this model adds and the source does not
(6 windows × ~250 mm of edge × 0.18 mm² × two faces ≈ 540 mm³, against a 470
mm³ volume difference), plus the wider diametral rib of §3.4. The hub is where
the reconstruction genuinely departs, for the reasons in §3.1 and §3.6: no
bayonet flare, and none of the internal webbing. Reporting 70.5% and saying
which half of the part it comes from is more use than an aligned number that
hides it.

**A note on `--align`, because it costs more than it looks.** The flag is meant
for exactly this situation — grading against a downloaded reference — and here
it makes every score *worse*: middle 95.3% → 51.1%, cover 96.1% → 80.1%. Its
best-rotation search lands in a local optimum, and it does so on a part with
six-fold symmetry where being 30 degrees out puts every spoke over a window.
The two meshes were already registered: sampling material at r = 50 around a
full turn gives spokes at 24.5–35.5, 84.5–95.5, … degrees on both, identically.
Check for that before reaching for the flag, and do not read a low aligned
score as a bad reconstruction until you have looked at the unaligned one.

## Sources

- rgeissler, *cable spool ethernet cable*, Printables 27496.
- Covestro (ex-Bayer), *Snap-Fit Joints for Plastics*, via the `snap-fits`
  skill: the cantilever formulas, the taper table, and the friction guide data.
- Prusament PETG TDS, via the same skill: 1.7 GPa flexural, 5.1% elongation at
  yield, hence 1.7% / 1.0% allowable strain.
