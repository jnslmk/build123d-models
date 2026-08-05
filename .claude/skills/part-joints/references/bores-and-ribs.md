# Bores and ribs

A bore that receives a *tool* — a drill shank, a hex bit, a screwdriver — is a joint
like any other, and it obeys the same three rules from `SKILL.md`. It gets its own
reference because FDM does something to small vertical holes that no clearance table
will tell you, and because this repo has a printed-and-measured implementation of the
compliant-rib answer.

## Contents

- [Never cut a bore at nominal](#never-cut-a-bore-at-nominal)
- [Ribbed bores](#ribbed-bores)
- [The repo's implementation and its constants](#the-repos-implementation-and-its-constants)
- [Hex sockets](#hex-sockets)
- [Spacing between bores](#spacing-between-bores)
- [Calibrating a grip](#calibrating-a-grip)
- [Sources](#sources)

## Never cut a bore at nominal

**FDM prints small vertical holes roughly 0.1–0.3 mm undersize**, with a worked
example of ~0.24 mm on a 5 mm hole in PLA on a 0.4 mm nozzle — both figures from
[Creative3DP][c3]. [Protolabs Network][pl] independently confirms the general
effect ("FDM often prints undersized vertical-axis holes") without giving its own
number. A bore modelled at exactly the tool's nominal diameter therefore comes
off the bed as a press fit.

So:

- **Add diametral clearance.** About **0.4–0.5 mm** for an easy drop-in tool fit.
  [AON3D][an] gives a range, not a single figure: **1–2× extrusion width** — 1×
  (~0.4 mm at a 0.4 mm nozzle) for a tighter sliding fit, 2× (~0.8 mm) for a
  free-running one. This section's 0.4–0.5 mm sits at the tight end of that
  range, appropriate for a tool that should drop in without rattling.
- **Wood and brad-point bits want the looser end**, because their spurs cut a wider
  circle than the shank behind them, so the widest part of the bit is not the part
  you measured.
- **Expose the clearance as a named constant, not a magic number.** In this repo
  it is `create_base(..., clearance=...)`, and the docstring at
  `models/drill_storage/box.py:1014-1018` states the undersize reason
  inline — copy that habit.
- **Slicers already compensate a little**, inconsistently and differently per
  slicer. That is a reason to print a coupon, not a reason to skip the clearance.

## Ribbed bores

A plain clearance bore is a compromise: wide enough to drop in means wide enough to
rattle. The fix is compliance.

**Cut the bore a little wider than the tool — a relieved *valley* — then add three
rounded internal ribs so the tool rides on three line contacts instead of a
full-circle wall.** The tool drops in cleanly and is held by a light, even grip
regardless of layer scarring, bore shrinkage or which day it was printed.

Why it beats a tight bore:

- Three contacts locate a cylinder exactly; a full circle over-constrains it, so
  every bit of bore error becomes either play or jam.
- Each rib can **deflect**. A rib that deflects converts a position-controlled fit
  into a force-controlled one, so one interference number covers a whole range of
  bore sizes. Same principle as a crush rib
  ([Hackaday][hd]) but sized to stay elastic, because a tool goes in and out
  hundreds of times where a bearing goes in once.
- The valley behind each rib is what gives it somewhere to deflect *to*. A rib with
  no relief behind it is a bump welded to the wall — it can only be crushed.

Shape rules:

- **Make the rib mostly proud of the valley**, meeting the wall on a narrow neck.
  A shallow lens across a wide footprint has no travel.
- **Keep the rib the same size in every bore**, not scaled to the bore. An
  identically-shaped rib has identical radial stiffness, so an identical deflection
  gives an identical retention force from a 2 mm bore to a 10 mm one. Scale the rib
  and you are back to needing a different number per size.
- **Stop the ribs a few mm below the mouth** so the opening stays a clean circle
  for the lead-in chamfer, and so the chamfer is cut on plain geometry (an OCC
  chamfer on a ribbed mouth is a reliable way to corrupt the builder — see the
  `build123d-geometry-ops` skill).
- **Taper each rib out to nothing near its top** rather than ending it square. The
  taper is the tool's lead-in onto the ribs.
- **Grip on the plain shank, not the flutes.** Put the rib band low, just above the
  bore floor, where every tool bottoms out on a true cylinder. Higher up sit the
  flutes — two narrow spiral margins over a void — where ribs grip intermittently
  and, worse, the hardened spurs broach the ribs away on the way past and the bore
  loses its interference permanently.

## The repo's implementation and its constants

`models/drill_storage/box.py`, `cut_holes` (`:828`) and
`create_base(ribbed=True)` (`:992`). Verified constants as of this writing:

| Constant | Value | Line | Meaning |
| --- | --- | --- | --- |
| `RIB_COUNT` | `3` | `:185` | ribs per bore |
| `RIB_GRIP` | `0.22` | `:217` | diametral interference at the rib faces, all bores |
| `HEX_GRIP` | `0.25` | `:218` | same for hex sockets — flats, not a curved wall |
| `RIB_WIDTH` | `0.9` | `:292` | rounded-bead diameter (≥ 2 perimeters at the neck) |
| `RIB_RELIEF_FRAC_OF_WIDTH` | `0.75` | `:298` | protrusion past the valley, as a fraction of bead width |
| `RIB_TAPER` | `4.0` | `:299` | height over which each rib ramps out to nothing |
| `RIB_ZONE_H` | `14.0` | `:310` | rib band height above the bore floor |
| `HEX_SLIP` | `0.05` | `:324` | across-flats clearance on the hex guide socket |
| `RIB_TOP_GAP` | `BORE_MOUTH_CHAMFER + 0.4` = 1.2 | `:326` | how far below the mouth the ribs stop |
| `BORE_MOUTH_CHAMFER` | `0.8` | `:111` | 45° lead-in depth at every mouth |

Derived helpers, all at `:345-374`:

- `rib_tip_r(d, grip) = (d - grip) / 2` — the grip radius, just inside the tool.
- `_rib_width(d, grip) = min(RIB_WIDTH, 1.4 * rib_tip_r(d, grip))` — fixed bead,
  capped on the tiniest bores so three beads cannot choke the hole.
- `rib_relief(d, grip) = RIB_RELIEF_FRAC_OF_WIDTH * _rib_width(d, grip)` — tied to
  the bead width, not to `d`, because it is the *ratio* of the two that decides
  whether the rib is a spring or a bump. Must stay below 1.0 or the bead never
  reaches the valley wall and prints as a floating pin (`:290-291`).
- `ribbed_valley_r(d)` (`:362`) — the cut radius, i.e. the bore's real footprint
  for layout and packing. Use this, not the tool diameter, when spacing holes.

Small-bore compensation, `RIB_GRIP_SMALL` (`:275-282`) with linear interpolation in
`grip_for` (`:325`):

| Bore Ø | Grip |
| --- | --- |
| 2.0 mm | 0.46 |
| 2.5 mm | 0.45 |
| 3.0 mm | 0.48 |
| 3.5 mm | 0.42 |
| 4.0 mm | 0.28 |
| 5.0 mm | 0.22 (meets `RIB_GRIP`) |

This is a **manufacturing** correction, not a return to a size-scaled grip law. A
0.45 mm-radius convex bead traced out of a concave notch on a small bore is the
tightest curvature in the part, and a 0.4 mm nozzle rounds it off, so the ribs print
further out than modelled. The effect dies away above ~4 mm. The design comment at
`:216-274` is the full argument and it is worth reading before touching any number
in that table — including the note that the table is deliberately non-monotonic.

## Hex sockets

A hex socket has **no ribs to take up slack unless you give it some**, so a plain
hex fit lives entirely in its across-flats clearance and is correspondingly fussy.
`models/drill_storage/hex.py:51` (`HEX_SHANK_AF`) and `:60` (`HEX_CLEARANCE`)
does exactly that: `HEX_CLEARANCE = 0.15` on a nominal `HEX_SHANK_AF = 6.35`
(1/4") shank — enough to drop in and lift out one-handed, not enough to rattle.

The ribbed variant splits the two jobs. The socket is cut **over** size
(`HEX_SLIP = 0.05`, `:320`) so it only guides the shank and stops it rotating, and
the grip comes from three compliant beads in a band at the bottom bearing on
alternating flats at `HEX_GRIP` (`:919-964`). Within that band the socket opens out
to a round relief pocket wide enough to swallow the hex corners, so the beads have
travel behind them — invisible from outside, where the mouth stays a clean hex.

The earlier design got its grip by cutting *under* the nominal across-flats, and it
went from drop-in to jammed over 0.15 mm with nothing to tune (`:308-311`). That is
rule 3 failing in the wild: flat-on-flat against a solid wall has no compliance.

## Spacing between bores

Ribbed and clearance-widened bores have a bigger footprint than the tool they hold,
so a layout that fitted at nominal will not fit once relieved.

- **Keep at least 0.8–1.2 mm of wall between neighbouring bores** — 2–3 perimeters
  at a 0.4 mm nozzle ([Hydra Research][hr] puts the minimum wall at 0.9 mm).
- **Re-space a tight layout rather than letting bores merge.** A gap under about
  0.3 mm does not slice as a wall at all: the slicer merges the two bores into one
  slot and the grip disappears from both.
- Budget for the **lead-in chamfers as well as the bores**. Two neighbouring mouths
  each want their chamfer to form. The repo's budget:
  `HOLE_WALL = 2 * BORE_MOUTH_CHAMFER + 0.1` = 1.7 mm between holes (`:128`), and
  `WALL_CLEARANCE = BORE_MOUTH_CHAMFER + BASE_TOP_CHAMFER + 0.4` = 2.2 mm from any
  hole to the outer wall (`:129`), so a hole's lead-in and the top-rim chamfer both
  still form.
- **Pack by the cut footprint, not the nominal diameter** — `ribbed_valley_r(d)`,
  fed to `pack_rows` (`:608`) via `layout_bores` (`:723`). Both packers print a
  WARNING to stderr when they cannot reach the requested spacing; do not ignore it,
  because `pack_rows` only warns about *horizontal* overpacking and will silently
  overlap rows.

## Calibrating a grip

The grip constants above were not derived. They were printed, judged, and revised —
twice for the round bores and once again for the small ones, with the whole trail
kept in the source comments (`:183-274`). Two lessons transfer to any new
interference feature:

1. **Print a sweep coupon.** `drill_fit_tester.sweep` and `drill_fit_tester.small`
   exist for exactly this; the latter offsets the whole grip law by a fixed amount
   per bar so the correction curve can be measured rather than assumed.
2. **When one number cannot be made to work across sizes, the geometry is wrong,
   not the number.** Two full generations were spent tuning a constant that could
   never have worked, because the ribs had no travel. Check compliance before
   tuning interference.

Verify the result in code, not in a projection: point-sample the solid to confirm
the ribs formed and the grip circle is where you think it is (see the
`build123d-geometry-ops` skill). Ray-sampling the CAD is how the repo established
that a bar's grip circle really was 1.784 mm while the printed part behaved as if
it were 0.22 mm wider — which is what identified the effect as a toolpath artifact
rather than a modelling error.

## Sources

[c3]: https://tools.creative3dp.com/blog/press-fit-tolerances-3d-printing/
[pl]: https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
[an]: https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/
[hr]: https://www.hydraresearch3d.com/design-rules
[hd]: https://hackaday.com/2020/10/15/adding-crush-ribs-to-3d-printed-parts-for-a-better-press-fit/

- [Creative3DP — Press-fit tolerances for 3D printing][c3]
- [Protolabs Network — How to design parts for FDM 3D printing][pl]
- [AON3D — Engineering fits: how to design for 3D printed assemblies][an]
- [Hydra Research — Design rules and best practices for FFF][hr]
- [Hackaday — Adding crush ribs to 3D printed parts for a better press fit][hd]
