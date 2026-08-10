# Design notes: measuring the source, and rebuilding it

This is the ledger behind `models/cable_spool`. Section 1 says how the source
model was measured, section 2 what came out of it, section 3 what this model
does differently and why, section 4 is the clip, and section 5 grades the
result against the original meshes.

The tooling is the `stl-reverse-engineering` skill's. Nothing here was read off
a render.

**Section 2 has been rewritten once already, and it is worth saying why.** The
first pass read the cover's bore as a plain 24.05 circle, concluded that the
0.9 mm notch it saw above the rib tops could not swallow a 2.0 mm cover, and
recorded the source's bayonet as a mechanism that "cannot close". Every part of
that was wrong, and the error was one of sampling rather than of arithmetic:
the bore was measured at one height, at four angles that all happened to miss
the features. Sampled through the thickness it is stepped, the band above the
rib top is 2.005 mm rather than 0.9, and the mechanism closes exactly as
drawn. The lesson is cheap to state and was expensive to learn — **when a
reconstruction concludes that a shipping design does not work, the
reconstruction is what to re-measure.**

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

Every z below is measured from the base's bed face, on the meshes rotated
Z-up. The source files are stored with Y as the axis and the base plate at
y = −2 … 0, so `z = y + 2` throughout.

| Feature | Measured | Here |
| --- | --- | --- |
| Base plate | z 0.00 … 2.00 | z 0 … 2 |
| Middle disc seat (collar top) | 9.195 | `MIDDLE_Z = 9.2` |
| Cover seat (rib tops) | 18.395 | `COVER_Z = 18.4` |
| Top of hub, and of the cover | 20.400 | `STACK_H = 20.4` |
| Channel heights | 7.195 and 7.200 | `CHANNEL_H = 7.2` (both) |

**The two channels are the same channel twice.** An earlier pass of these notes
had them at 7.0 and 7.4 and put the stack at 20.0. Both were wrong, and they
were wrong together: the collar top was read as y = 7.0 rather than 7.195 and
the stack was then cut to 20.0 rather than the 20.4 the hub actually stands.
The independent check is the source's own clip, whose cavity measures 20.4 —
which is exactly the stack it is meant to span, and which no longer needs
explaining away.

### The hub

| Feature | Measured | Here |
| --- | --- | --- |
| Tube | r 22 … 24 | same |
| Lower collar | r 24 … 24.99, up to z = 9.195 | `HUB_COLLAR_R = 25.6`, to `MIDDLE_Z` |
| Guide ribs | 4 × 34.96 deg, r to 24.99, to z = 18.395 | `HUB_RIB_COUNT/ARC/PHASE` |
| Rib top trailing chamfer | 3.5 deg of arc over the top 0.8 mm | `RIB_LEAD_W/H` |
| Bayonet groove | r back to 24.0, z 18.4 … 19.1 | `BAYONET_LIP_H = 0.7` |
| Bayonet cone | 24.0 → 25.0, z 19.1 … 19.7 | `BAYONET_RAMP_H = 0.6` |
| Bayonet flare | r 25.0, z 19.7 … 20.4 | `BAYONET_FLARE_H = 0.7` |
| Wall liner behind each rib | r 20.6 … 22 over the same sectors, full height | `HUB_LINER_R = 21`, to `STACK_H` |
| Cable slot | ~29 deg at mid-wall, full height | `CABLE_SLOT_ARC = 33` |
| Second slot | same, opposite, above z = 9.195 only | keyway |
| Spindle post | r 3.25, bore r 1.49, **blind** from the top | r 2.2 / 1.25, bore goes through |

### The two upper discs, and the bayonet between them

The middle disc's bore is constant through its 2 mm: 24.04 nominal with four
25.045 relief pockets ~37 degrees wide on the rib centres, plus two keys
reaching in to r = 22.0 at opposite sides, which line up with the hub's two
slots. It drops past the ribs and lands on the collar. Nothing subtle.

**The cover's bore is not constant through its thickness, and that is the whole
mechanism.** Sampled at 0.02 mm steps through the plate, at 0.5 degree steps
around it, it reads as three sectors repeating every 90 degrees:

| Sector | Width | z 0 … 0.71 | 0.71 … 1.29 | 1.29 … 2.00 |
| --- | --- | --- | --- | --- |
| locking | ~35 deg | 24.045 | cone 24.05 → 25.05 | 25.045 |
| tab | ~18 deg | 24.045 | 24.045 | 24.045 |
| pocket | ~37 deg | 25.045 | 25.045 | 25.045 |

Set that against the hub's own band above a rib top — groove to 19.115, cone to
19.695, flare to 20.400, i.e. 0.715 / 0.58 / 0.705 from a rib top at 18.395 —
and the two are complementary to within 0.02 mm over all three steps. They are
not two things that happen to exist; they are a shaft and its socket.

So the mechanism is a **bayonet**, and it goes together like this:

1. Turn the cover so its four pockets sit over the four ribs. A pocket is
   25.045 over the full thickness and a rib is 24.99, so the cover passes.
2. Lower it until it rests on the rib tops at 18.395.
3. Twist it about 36 degrees, until each tab butts against the trailing face of
   a flare. A tab is 24.045 over the full thickness and a flare is 24.985, so a
   tab cannot pass one at any height — that is the rotation stop, and it lands
   the locking sectors square on the ribs.

Locked, the cover's 0.71 mm lip lies in the hub's 0.715 mm groove, under a
flare that stands 0.94 mm proud of it, over 4 × 35 = 140 degrees of arc. It
cannot lift, and the rib tops under it mean it cannot sink. The clips then have
nothing to do but hold the *rim* together.

**A word on angles between two files.** Each STL is saved in whatever rotation
its exporter happened to use, so a measured offset between a feature on the
*base* and a feature on the *cover* is not evidence of anything on its own —
and an earlier pass of these notes used exactly such an offset (a "45 degrees"
between the cover's pockets and the base's ribs) as its argument for a twist.
Nothing above rests on that. The relative orientation here is derived from what
has to be mechanically true: the cover's locking sector is the only part of its
bore shaped like the hub's rib-top band, so that is the part that sits on a rib,
and everything else follows from the three sector widths adding to 90 degrees.
The two files do in fact turn out to be within a degree of co-oriented, with the
cover stored *locked* — but that is a happy accident, not the evidence.

Two smaller measurements corroborate the reading. The ribs are a constant 34.96
degrees from the collar up to z = 17.6 and then narrow, **on one side only**, to
about 31.5 by the rib top: that is a lead-in ramp for the cover's underside, and
it is on the trailing side, which is the side the cover sweeps in from. And the
band above the rib top measures 2.005 mm against a cover of 2.00 — the cover
finishes flush with the top of the hub, which is not something that happens by
accident.

## 3. Where this model departs, and why

The mechanism is not one of them any more. **The bayonet in section 2 is
reproduced, and it is the model's only retention for the cover — there is no
switch, no fallback and no "rests on the rib tops" version.** What is left are
five deviations, and each costs a little IoU in section 5, which is the honest
place to look for them.

1. **The spindle post is smaller than the source's, and its bore goes through.**
   The source post measures r = 3.25 with a r = 1.49 bore, blind from the top;
   this one is `SPINDLE_R = 2.2` with a 2.5 mm bore drilled through. The
   through-bore is the point — "put a rod through it and spin the spool" does
   not work on a blind hole — and the diameter has not been revisited since it
   was first read. It should be: 3.25 is what the mesh says.
2. **The window mouths are chamfered on both faces of all three discs.** The
   source chamfers only the middle disc's top. The cable crosses these edges on
   every turn, and `AGENTS.md` does not allow shipping them raw.
3. **The diametral rib is 5.4 mm, not 2.9.** At 2.9 the 4.4 mm spindle post
   stands proud of the rib it is carried on, leaving two bare arcs of cylinder
   meeting the bed face at 90 degrees; at exactly 4.4 the two are tangent,
   which is worse (OCC leaves a sliver edge at each tangency).
4. **The hub's interior is simpler.** The source hub is not a hollow 2 mm tube.
   Sliced at any height above the plate it carries a pair of walls straddling
   the axis about 2.1 mm apart, widening into two solid lobes where they reach
   the bore at the slot ends — roughly 6 000 mm³ of structure whose function
   could not be established from the mesh. It is not a stiffener for anything
   the discs load, it does not reach the spindle post, and the shapes it is
   complementary to (the flange's kidney holes) are in the plate below it. It
   is not reproduced, and it is most of the base's IoU gap; section 5 says how
   much.
5. **The bayonet's clearances are this repo's, not the source's.** The
   geometry — 0.7 / 0.6 / 0.7 of band, 35 degree ribs, one radius at 25.0 —
   is measured and kept. The gaps in it are re-derived: the lip is
   `fits.SLIDING` on the tube (24.11 against the source's 24.045), the pockets
   are `fits.FREE` over a rib (25.2 against 25.045), the counterbore is
   `fits.SLIDING` over the flare (25.11), and a pocket is `HUB_RIB_ARC + 6`
   wide against the source's `+ 3`. The source's 0.045 mm and 1 degree are
   inside a single extrusion's tolerance and will bind on any machine that
   prints a hair fat; that is the whole reason `AGENTS.md` says not to copy a
   source's clearances.

The pockets being wider than the source's is what makes the tab 14 degrees
rather than 18 and the twist 38 rather than 36 — the three have to add to a
quarter turn, so widening one narrows another. Nothing else about the motion
changes.

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

| Part | Volume, source → here | IoU | Before the bayonet | Verdict |
| --- | --- | --- | --- | --- |
| `middle` | 18 483 → 18 380 mm³ | **95.3%** | 95.3% | passes the skill's 95% gate |
| `cover` | 19 164 → 18 565 mm³ | **96.6%** | 96.1% | passes |
| `base` | 33 332 → 27 182 mm³ | **71.1%** | 70.5% | see below |

Splitting the base by height, against slabs of the same two meshes:

| Region | Source | Here | IoU | Before |
| --- | --- | --- | --- | --- |
| plate, z 0 … 2 | 19 842 mm³ | 19 375 mm³ | **90.9%** | 90.9% |
| hub, z 2 … 21 | 13 490 mm³ | 7 807 mm³ | **44.4%** | 42.8% |

So the base's plate is as good as the other two discs — the 9% it gives up is
almost all the window and bore chamfers this model adds and the source does not
(6 windows × ~250 mm of edge × 0.18 mm² × two faces ≈ 540 mm³, against a 470
mm³ volume difference), plus the wider diametral rib of §3.3. The hub is where
the reconstruction still genuinely departs, and after the bayonet it is for one
reason only: §3.4's internal structure, about 6 000 mm³ of it. Reporting 71.1%
and saying which half of the part it comes from is more use than an aligned
number that hides it.

**What the bayonet was worth.** The hub slab gains 1.6 points and the base
0.6 — small, because the groove, the cone and the flare together are only about
40 mm³ of geometry. The cover is the honest measure of it: 96.1% → 96.6%, and
its *excess* volume (material this model has and the source does not) falls
from 162 mm³ to 26. That number is the bore, and it is now the source's bore
rather than a plain circle.

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
