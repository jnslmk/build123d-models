# Design notes — mounting, standing and corners

Why the mounts are shaped the way they are. Mostly a record of constraints that
are not obvious from the geometry, and of the collar that was wrong first.

The profile's own reasoning lives in `README.md`; the numbers live in
`config.py`. This file covers everything that grips the tube from outside.

---

## 1. The collar was wrong — the section has no undercut, so nothing needs to wrap

The obvious mount for a tube is a collar: a ring that goes all the way round,
split so it can be fitted. That was the first design and it is wrong on this
profile, for a reason that only shows up when you look at where the tube is
widest.

The stadium is at its **full 26 mm from z = 13 to z = 17** — the straight band
between the two R13 arcs. `RIM_Z` = 16.8 sits inside that band. So a trough that
stops exactly at the rim has **no undercut anywhere**: the tube drops straight
into it sideways, and lifts straight back out.

That single change fixes five things at once:

| | |
|---|---|
| A collar shadows 40–60 mm of diffuser | a cradle shadows nothing; only the two 18 mm straps do |
| A collar traps the diffuser, so the strip cannot be serviced | two screws and the strap is off |
| A closed ring cannot pass the 27.2 × 31.2 endcap | a cradle never has to |
| A split collar needs support inside a locating bore | a cradle opens upward and prints clean |
| A closed polygon has to be threaded together | cradles let it be assembled and dismantled in place |

So the universal interface is not a part at all — it is a **cradle profile plus a
strap-boss pattern**, shared in code the way `profile.py` already shares its
sketches. The only wrapping part is a small **strap**, 18 mm wide, two per
station, and it is identical on every foot in the family.

### Locating a 0.5 mm wall means locating on shape, not on force

Four facts drive this, and the first one is the gift:

1. **The stadium self-keys.** It cannot roll in a matching trough. Most of what a
   round-tube clamp's force is *for* — resisting rotation — is free here.
2. **The wall is 0.5 mm.** Clamping force dents it. There is no version of this
   where torque is the answer.
3. **The flanks at z = 13–17 are the floppiest part of the section** — flat
   0.5 mm panels — and they are also exactly where the widest line is. The floor
   web and the two Ø3.3 screw bosses stiffen them, which is the only reason this
   works at all.
4. **The diffuser is a bought snap-in part.** Any pressure on it pops it.

The design that follows: bore is the aluminium stadium clipped at `RIM_Z`, grown
by the material-adjusted fit (§5). Contact in **two 15 mm bands at the ends of a
60 mm cradle**, middle relieved 0.6 mm — which puts the bearing where the moment
reaction wants it and keeps the middle from binding on a 1.5 m extrusion's
straightness.

Torque is designed out rather than specified. The strap's feet land hard on the
cradle's boss lands with the bolt axis through the middle of the land, so the
bolt is in pure compression against a stop and over-torque squashes a 237 mm²
pad instead of the tube. The instruction is **"tighten until it bottoms, plus a
quarter turn"** — no wrench, no judgement.

#### The bolt circle is derived, not chosen

`BOSS_U` was a typed 19.5 mm, which is `ARCH_HALF_W` **exactly** — the bolt axis
lay on the strap's own outer flank. The hole's top mouth came out bisected by
the arch springing, with flat land for only a third of it, and an M4 socket head
fouled the flank by 2.6 mm. The strap could not have been bolted down at all.
The same 2.5 mm-outboard-of-the-cradle bolt circle also put the Ø5.7 insert
holes 0.4 mm into the trough's outer wall.

Both numbers now come out of `mount_config.arch_half_width(FOOT_H)`, which is
the flank's own stadium evaluated at the land: the foot is tall enough (8 mm)
for the flank to have curved in, and the bolt far enough out (22.1 mm) to clear
what is left, with the pad widened to `BOSS_OD` 14.2 mm so it still fuses into
the cradle wall on its inboard side rather than standing free. The insert holes
follow the same circle and now clear the trough wall by 2.2 mm. The cost is a
strap 58 mm wide instead of 51 and 2 mm taller feet; the shadow is unchanged,
because that is `STRAP_W` and nothing here touches it.

`check_bolt_clears_arch()` asserts it twice — once in closed form, once by
putting a head-sized slug where the head goes and looking for shared volume,
because the formula can be right about a shape the builder did not produce.

### The strap's grip lips do not exist, and could not

An earlier version of this section had the strap grip the aluminium flank with
two 1.0 mm compliant lips standing 0.3 mm proud of the nominal tube. They were
built, and the interference check caught them pressing on the **diffuser**.

The reason is worth keeping. Sample the extrusion across the rim plane:

    u = 9.00  void     u = 11.50  void
    u = 9.75  SOLID    u = 12.45  void
    u = 10.50 void     u = 12.75  SOLID

**There is no land at the rim.** Only two ~0.5 mm wall edges — the channel wall
at u ≈ 9.5–10 and the shell at u ≈ 12.5–13 — with the corner pocket open
between them. Anything above the rim is diffuser, and anything the strap could
reach is either a 0.5 mm edge that would dent or a bought plastic part that
would pop.

So the strap touches nothing. It arches clear by `DIFFUSER_CLEAR` and **captures**
the tube rather than clamping it: the cradle locates by shape, the strap stops
it lifting, and the tube keeps 1.5 mm of vertical play. Where that play matters
— a lamp that travels, or one overhead — a strip of self-adhesive foam under the
crown takes it up. That is a bought consumable, not geometry that could crush a
0.5 mm wall. `check_strap()` now asserts *zero* shared volume with both the
diffuser and the extrusion, and bounds the play.

### A closed polygon is over-constrained, and that is a real number

Three 1500 mm tubes and three 60° corners will not close. **0.5° of angular
error is 13 mm at 1500 mm:**

    1500 × tan 0.5° = 13.1 mm

The relieved middle is what buys the ±1° of compliance that lets the last corner
go together. This is why the cradle is *not* a long tight bore — a full-length
contact would be the stiffest joint and the one that never assembles.

### One axial stop per tube, and no more

Aluminium's α is 23 µm/m·K, so a 1.5 m tube grows

    1.5 × 23e-6 × 30 K = 1.03 mm

over a 30 K swing, and printed parts grow ~3× faster. In a closed polygon that
has to go somewhere. **At most one positive axial stop per tube; the other end
floats on the strap lips.**

Where a structural stop is needed, the best one is a Ø3.2 hole drilled through
the tube's belly at u = 0 into an insert boss in the cradle floor — invisible,
positive, and it touches neither the endcap nor the diffuser. Butting the cradle
against the endcap's 0.6 mm collar shoulder is a *locating* stop only: it puts
load into the two M2 self-tappers, which is exactly what §3 says not to do.

---

## 2. The corner — the glands set the setback, and the cable would set it worse

`angle` means the **included angle between the two tube axes**: 60 is a
triangle, 90 a square, 120 a hexagon. This is in the docstring because building a
hexagon corner by asking for 60 is the obvious mistake.

Both tubes keep their glanded endcaps and the jumper is external, so at a vertex
two glands point at each other. They are cylinders whose axes intersect, not
spheres, so the clearance condition is not "twice the radius":

    a > r_gland / tan(angle/2) = 12 / tan 30°     = 20.8 mm
    s = a + gland protrusion   = 20.8 + 30        = 50.8 mm
    dark run = 2 × (s + CAP_T) = 2 × 62.8         = 126 mm

**126 mm of unlit tube at every vertex**, or about 8 % of an equilateral
triangle's perimeter. The aluminium starts 12 mm behind the cap face, because
`endcap.seated()` puts the flange *outside* the tube — forgetting that term is
worth 24 mm and it is easy to do.

### Why the cable does not set the setback, and how close it came to

The corner contains gland → 100–150 mm pigtail → SP16 → jumper → SP16 →
pigtail → gland. That is 250–350 mm of Ø6.7 ÖLFLEX and two Ø20 × 45 barrels, and
the cable's fixed-install bend radius is 4 × 6.7 = **26.8 mm**.

A single arc filleting a 60° V at that radius touches each leg at

    26.8 / tan 30° = 46.4 mm

which would push `s` to 76 mm and the dark run to **177 mm** — half again worse
than the glands demand. That is avoided by not routing the loop in the plane at
all. The LEDs face out of the form, so the back is hidden: the pigtail loop and
both SP16 barrels live **behind the form plane, inside the corner's own web**.
The web has to be a box section for stiffness anyway (§3), so it is the cable
tray as well, and the setback stays gland-limited at 51 mm.

### Taken and refused

**Taken:**

| | |
|---|---|
| Coplanar corners | one true plane; the form reads as drawn |
| Loop behind the plane | saves 51 mm of dark run per vertex for free |
| Web doubles as cable tray | the stiffener had to exist regardless |

**Refused:**

- **A 36 mm out-of-plane stagger.** Offsetting the two tubes perpendicular to the
  form plane lets the glands pass in separate layers, collapsing the dark run
  from 126 mm to ~24 mm — the lines can even overlap in projection, so visually
  there is no break at all. It is the strongest single idea in this file and it
  is refused on aesthetics: the form becomes two parallel planes 36 mm apart
  rather than one. If the dark corners turn out to look worse than the depth
  would have, this is the first thing to revisit, and the geometry is a
  parameter away.
- **Blanking the corner-facing glands** and passing the bus through the corner
  body. It would delete the whole setback problem, but it means routing Ø6.7
  cable through a 120° bend in a part that is 21 mm deep, and it breaks the
  decision that corners are mechanical only.
- **90° elbow glands at corner ends.** They cut the protrusion to ~18 mm and the
  dark run to ~105 mm, which is real. Refused for now only because it means
  stocking two gland types; worth reconsidering if corners get common.

---

## 3. Stiffness — the static case is a non-issue, handling is not

The first estimate here was wrong in an instructive way. A 1.5 m tube
cantilevered from a corner is

    0.45 kg × 9.81 × 0.75 m = 3.31 N·m

and a 5 mm × 40 mm plate section gives 20 MPa — which looked marginal. But that
is the plate's **weak** axis, and in a wall-hung planar form gravity bends the
plate about its **strong** axis, giving 2.5 MPa. The static case was never the
problem.

The design case is somebody pushing the tube's far tip out of the plane. Take
10 N at 1.5 m = **15 N·m**:

| section | Z (mm³) | σ at 15 N·m | |
|---|---|---|---|
| 5 mm plate, weak axis | 167 | 90.0 MPa | fails outright |
| solid 8 × 40, weak axis | 427 | 35.2 MPa | no margin |
| **closed box 45 × 21, t = 4** | **2662** | **5.6 MPa** | comfortable |

So the answer is not a thicker plate. It is a **closed box web the same depth as
the cradle**, R8 fillet at the root of the V, with the tray pocket opening away
from the bed so nothing bridges and a screwed-on cover closing the section.

Allowables, because they are not the textbook numbers: FDM ASA is ~40 MPa short
term, but it **creeps**, so a permanently loaded part gets **≤ 10 MPa sustained**.
The 5.6 MPa above is against a transient abuse load and the 1.2 MPa static case
is what actually sits there for years.

**The section is not the weak link.** Ranked, the real ones are:

1. **The tube-to-cradle grip** (§1).
2. **Bolt preload relaxation.** Printed parts lose 20–50 % of preload in weeks.
   Wave washer under every clamp screw, and the joint must not release when it
   relaxes — which a cradle does not, because it is a positive capture.
3. **The endcap.** The two M2 self-tappers are the *only* tie between endcap and
   tube. House rule for this whole family: **no mount takes its primary load
   through the endcap.**
4. **The root fillet.** R ≥ 8 mm inside the V, and no cover screws in the root.

If any bolted plate-to-cradle interface is ever added, two bolts in a line is not
enough — the moment about the bolt line is carried only by face friction, which
is the thing that relaxes. Four bolts on a square, or two plus a keyed pad.

---

## 4. The stand — three legs, and the number nobody quotes

Modelled on the [Astera AX1‑STD](https://astera-led.com/products/tubestand/):
three legs that swing out and nest together for packing, holding the tube
vertically close to the floor. No ballast at all.

A printed hub carries three **bought flat bars** (20 × 3 × 250 mm, Ø6.5 hole one
end) on M6 pivots through clevis ears at 120°, friction held by nyloc and
washers. The tube sits in a vertical cradle; its lower endcap lands in a well
with a side cable exit.

**The gland is 6 mm off the tube axis** — `GLAND_Z` = 9.0 against a tube axis at
15.0 — so the well is offset, not concentric. A Ø24 envelope at 6 mm offset
reaches to z = −3 relative to the tube outline, i.e. it pokes *outside* the
26 × 30 footprint at the bottom. A concentric well does not clear it, and this
is the single easiest thing to get wrong in the part.

### The stability number, stated plainly

    m      = 0.45 (tube) + 0.15 (hub) + 3 × 0.118 (legs)   = 0.95 kg
    r_eff  = 275 × cos 60°                                  = 137 mm
    F_tip  = m·g·r / h = 0.95 × 9.81 × 0.137 / 1.5          = 0.85 N

**About 85 g of horizontal push at the top topples it.** That is not a defect —
it is what this class of stand is, and the Astera original is no better. It is
studio kit used in controlled space and normally sandbagged.

Two things worth knowing before anyone quotes a tip *angle* instead: a tripod
tips about the line joining two adjacent legs, which is at `r × cos 60°` — **half**
the leg reach, so a Ø550 tripod behaves like a Ø275 disc. A four-leg variant tips
about `r × cos 45°` and is ~40 % better for the same reach and one more bar.

Leg length stays a parameter. `checks.py` computes `F_tip` from the actual part
volumes rather than from a comment, so a future change cannot quietly make it
tippier without failing.

---

## 5. Outdoor, lightly — drain rather than seal

The target is "survives light rain". Explicitly **not** an IP rating: no gaskets,
no O-rings, no sealed joints. Three consequences, and the first one propagates
further than it looks.

### ASA, and what it does to every fit in the family

**The whole family prints in ASA**, a stated deviation from the PETG default in
`AGENTS.md`. Two reasons stack: ASA is UV-stable where PETG chalks and
embrittles outdoors, and its HDT is ~95 °C against PETG's ~70 °C — which this
system needed anyway, since 30–45 W in a 1.5 m aluminium heatsink runs the tube
at 40–60 °C and PETG creeps badly near its HDT under sustained load.

That changes the clearances, and it changes them enough to matter.
`fits.for_material` takes **0.15 mm off** the PETG baseline, so:

    fits.SNUG    in ASA = 0.10 − 0.15 = −0.05 mm   ← an interference fit
    fits.SLIDING in ASA = 0.22 − 0.15 =  0.07 mm   ← where SNUG lands in PETG

So the cradle specifies `for_material(SLIDING, "asa")`, **not** `SNUG`. Reaching
for the fit class that *reads* right here gives a press fit on a 0.5 mm wall
aluminium tube.

### The print poses create three water traps

Every part in this family is posed to print without support, and in all three
cases that means a pocket opening upward. Two of the three get drains, and
`checks.py` asserts a drain path from their lowest point:

1. **The stand hub's gland well** — a cup directly under a vertical tube. Drain
   straight through the flange.
2. **The cradle trough** — holds water whenever the LEDs face up. Slots in the
   floor.

3. **The corner — the stated exception.** Its channel and both its troughs are
   **undrained**. They were drilled at four stations (the knuckle, one short of
   each cradle, and two out along each trough) and those drains have since been
   removed, so the channel now holds water to the depth of its own mouth and
   each trough to the lowest lip of its floor. `checks.py` reports both depths
   and asserts the plinth is solid at every station that used to be drilled —
   the exception is tested rather than merely written down, so re-drilling one
   fails a check and forces this section to be restated. **A corner therefore
   wants a sheltered mounting**, and a form that stands out in the rain wants
   its drains back: the geometry is in this file's git history.

### The rest

**A2 stainless throughout** — the M2 self-tappers into the ports, the strap
screws, the leg pivots. Legs in stainless or galvanised flat bar; plain mild
steel will bleed rust down a white diffuser within a season.

And a note that is a recommendation rather than geometry: **the extrusion itself
is not sealed either.** The diffuser snap and the endcap butt joint both admit
water. For a horizontal outdoor tube the sensible move is a small drain hole in
the tube's belly at its lowest point — but that is a modification to a bought
part, so it stays advice.

---

## 6. The part family

| module | part | notes |
|---|---|---|
| `mount_config.py` | — | shared cradle, strap and gland constants, all derived from `config.py` |
| `cradle.py` | `create_cradle()` | the shared trough, and the sections every foot cuts with |
| `strap.py` | `create_strap()` | the one universal part, two per station |
| `corner.py` | `create_corner(angle=60)` | two cradles on a plinth, V-bar with an open channel |
| `stand.py` | `create_stand_hub()` | vertical cradle, offset gland well, side exit, three leg pivots |
| `feet.py` | `create_eye_foot()`, `create_wall_foot()` | eye is a **through-bolt**, not an insert |

Two departures from the sketch above, both found while building:

- **`cradle.py` is its own module.** The cradle's sections are cut by four
  different feet; sharing them the way `profile.py` shares the extrusion's is
  cheaper than a constants file plus four copies.
- **The corner's cable tray has no lid, and the cradles sit on a `PLINTH_H`
  plinth.** The gland axis is 6 mm *below* the tube axis, so a Ø24 gland hangs
  3 mm below the tube's underside and cuts straight through a 4 mm cradle floor.
  Raising the cradles clears it. The channel then runs open from the vertex out
  to each cradle, holding both caps, both glands and the jumper loop — and the
  caps stand proud of it for most of its length, so a lid could only ever have
  covered the knuckle. It was dropped rather than half-built; the arm section is
  stiff enough without it (§3).

Feet carry their cradles **integrally**. There is no bolted collar-to-foot joint
in any moment path — that was the other half of the collar mistake in §1, and
deleting it removes a relaxing bolted interface from every load path in the
family. A `plain_collar()` with a 4-bolt pad stays as an escape hatch for ad-hoc
feet, but nothing structural goes through it.

A suspension eye is a bought M6 eye bolt through a Ø6.5 hole in a 10 mm boss,
penny washer and nyloc on the far side — **not** a heat-set insert. Inserts pull
out under shock, and a through-bolt cannot. Design it to 20 kg even though the
real load is 1.35 kg.

Print poses, all authored already sitting on z = 0 per the house rule: the corner
on its web back with both cradles opening up; the strap on its feet with the arch
up; the stand hub standing on its flange with the channel vertical, gusseted at
the root because that is where bending crosses layer boundaries. Every one is
support-free — support scarring in a locating bore is exactly what ruins the fit
in §1.

**Correction:** the strap's outer silhouette is an ogive shaped to stay ≥ 45°
throughout, but that claim does not extend to the bore's own crown, which is a
different curve. The crown is genuinely flat at its centre (0° from horizontal,
not merely close to it) and drops below the 45° rule over a chord of
`sqrt(2) * BORE_HALF_W` ≈ 20.5 mm — measured off the built solid, not asserted
from the sketch. It is still support-free, but for a different reason than "every
face clears 45°": that chord is thrown across the strap's own `STRAP_W`
(18 mm) as a short, converging bridge rather than a flat one, and it stays
printable only as long as the run does not outgrow the chord it closes.
`strap.py`'s module docstring carries the full derivation and the numbers;
`checks.check_bore_crown_bridge` is what keeps this paragraph honest if either
side of that relationship ever moves.

---

## 7. What the checks will enforce

The single most valuable assertion in the set:

    _shared_volume(part, create_diffuser(...)) == 0

**No mount ever touches the diffuser.** It is invisible in a projection and it is
the failure that would only show up when a strip needed replacing.

Then: `len(part.solids()) == 1` on every part, to catch the OCC silent-collapse
already documented in `endcap.py`; bore bands solid and the relieved middle
hollow, point-sampled; bed footprint inside 256 × 256 across the whole angle
sweep, so the parts print on either machine; the angle between the two cradle
axes measured *from the geometry* rather than asserted from the input; mock gland
envelopes proven non-intersecting at the computed setback, with the dark run
reported as a check line so it is visible in `uv run check`; a drain path from
every enclosed pocket that has one, and solid plinth plus reported water depth
at the corner's four undrained stations; and the stand's `F_tip` computed from
real part volumes.

---

## 8. Three numbers that are still assumed

**`GLAND_ENV_D` — proposed, `mount_config.py`, assumed 24 mm.** The diameter of
the circle containing the fitted gland seen down the tube axis — across the
*corners* of its hex, or its dome nut, whichever is bigger. It sets the corner
setback directly through `a > (GLAND_ENV_D/2) / tan(angle/2)`. A nylon M12 is
~17.3 mm across corners, which is ~15 mm off the dark run at every vertex.
*Measure:* calipers across the widest part of the fitted gland.

**`GLAND_PROUD` — proposed, `mount_config.py`, assumed 30 mm.** How far the gland
stands out past the endcap's outer face along the tube axis: cap face to the tip
of the dome nut, ignoring the cable. Not the gland's overall length — 12 mm of it
is buried in the cap's printed thread. It adds one-for-one to the setback, so it
is the other ~15 mm per vertex. *Measure:* depth gauge from the cap face.

**`FLOOR_T` — exists, `config.py:58`, assumed 1.0 mm.** Not a gland number at
all: the thickness of the horizontal aluminium web between the bottom of the
strip slot and the ceiling of the wiring cavity. It matters because

    CAVITY_TOP_Z = STRIP_FLOOR_Z − FLOOR_T = 13.1

is what four things register against — the cavity ceiling in `profile.py`, the
endcap's register lip in `endcap.py`, the check that the gland bore stays below
the ceiling, and the depth the PCB gets.

The concrete failure: if the real web is 2 mm, the ceiling is at 12.1 while the
endcap's lip is authored to reach 12.7. **The lip stands 0.6 mm proud of the
aluminium and the cap never seats** — it bears on the web instead of pulling
flush, and the two M2 screws pull against it. The cradle inherits the same
reference.

*Measure:* depth gauge into the cavity from the tube's open end, clear internal
height at the centre line. Expected 12.6 mm. Then

    FLOOR_T = 14.1 − 0.5 − (reading)

---

## 9. Open question

Can the corner-facing pigtails be re-terminated to ~60 mm? At 150 mm, the loop
plus two SP16 barrels is most of what the corner tray has to swallow, and the
tray is most of what sets the corner's size. Shortening them would make the whole
part substantially smaller for no optical cost.
