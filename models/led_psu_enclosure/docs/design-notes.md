# Design notes

Why the box is shaped the way it is. Mostly a record of constraints that are not
obvious from the geometry, and of things that were wrong first.

---

## 1. The thermal problem, and why the vent is modular

The RSP-320-24 is 89 % efficient at 321 W, so it sheds **~40 W**. It is also
fan-cooled from its top cover and derates from 50 °C ambient down to 50 % load at
70 °C. Those two facts fight the word "waterproof".

Rough sums for a sealed box of this size: external surface ≈ 0.19 m², and natural
convection plus radiation off plastic is ~6–8 W/m²·K.

| Load | Heat | ΔT over ambient | Internal at 25 °C ambient |
|---|---|---|---|
| 50 % | ~20 W | ~15 K | ~40 °C — comfortable |
| 75 % | ~30 W | ~22 K | ~47 °C — fine |
| 100 % | ~40 W | ~30 K + internal gradient | ~60–65 °C — into the derating band |

So sealed is genuinely fine up to about half load and gets marginal above it. For
LED lighting, average load is usually well under half. Rather than pick one
answer now, both end walls carry the **same** port and the decision stays a
swappable cartridge: `vent_blank` (sealed), `vent_louvre` (~IP54 chevron
labyrinth), `vent_fan` (40 mm forced).

Ports are placed **low at the terminal end, high over the PSU's top-cover fan**,
so a fitted pair gives cross-flow. One port alone would do very little. The shelf
is slotted so the plenum under it stays connected to the high port.

This also drives the material choice: at 55–65 °C internal, **PLA creeps and is
not an option**. ASA (or ABS if shaded) is the right answer; PETG is a distant
third.

## 2. The PSU nearly fills the box, and everything follows from that

The PSU is 215 × 115 inside a 228 × 128 interior — **6.5 mm to every wall**. An
SP1712 needs 19.7 mm behind the panel plus wire bend room, so *no wall at PSU
height can host a connector*. This is the constraint that shapes the layout:

- The shelf underside sits at **z = 63, i.e. 23 mm above the PSU**, not the naive
  10 mm — the top-cover fan needs a plenum to breathe into.
- The connectors go in the **front wall at z = 85**, in the space above the PSU.
- Everything mounted on the shelf is held **36 mm back from the front wall**
  (`SHELF_FRONT_KEEPOUT`) so the connector bodies have somewhere to be. That
  number is set by the deepest intruder — the RJ45 coupler at 32 mm — not by the
  SP1712s at 19.7 mm.
- The vent frames are capped at 5 mm thick because thicker would foul the PSU.
- The PSU plate is only 0.5 mm bigger than the PSU, for the same reason.

## 3. The lid snaps in — the flange is gone

The box originally closed like a commercial IP enclosure: an outboard flange
(`FLANGE_OUT = 12.5`), 14 M4 screws into blind inserts, and the screws placed
**outboard** of the gasket so a leaking screw hole drained back out instead of
into the joint. Correct, but it made the box 25 mm bigger in both directions
and bristling with protrusions.

The lid now **faces inwards**: a flush plate whose sides are coplanar with the
walls, with a plug skirt that drops into the mouth and a triangular bead around
the skirt that snaps into a groove in the rim band's inner face. The rim band
(`RIM_WALL = 7`) is what carries both the gasket groove on its top face and the
snap groove on its inner face — that is why the inward thickening survived the
flange's removal.

The trade-off is real and accepted: 14 screws could crush a 3 mm cord to its
23 % design compression over a ~700 mm perimeter; one perimeter bead cannot.
With the plug labyrinth in front of it the joint is a dust/splash seal, not an
IP65 crush. Engagement is deliberately light (0.3 mm): a 221 × 121 ring is far
stiffer than the `round_snap_box` hoop, so more would need a pry tool to open.

## 4. Nothing bores through the shell

Every fixing is either blind or outside the sealed volume:

- **The lid needs no fasteners at all** — it snaps into the mouth.
- **The PSU is not bolted through the floor** — that would be four leak paths in
  the bottom of a waterproof box. It bolts to `psu_plate`, which snaps onto four
  hollow split studs in the floor. No screw can reach that joint in either
  direction: the PSU's own bolts only go in from below the plate (a bench job),
  and a mounted PSU covers every stud position, so nothing can be driven from
  above either. The snap is the only fastening that assembles — 45° ramps both
  ways, so it clicks on a press and releases on a straight pull. The studs are
  hollow only down to a solid base block, so the floor stays sealed.
- **Vent cartridge screws** are blind self-tapping pilots.

The only holes through the wall are the ones a sealed component deliberately
fills.

## 5. Things that fought back

**The rim opening is not the interior.** The wall thickens inward over the top
15 mm to give the rim ring enough width for the gasket and snap grooves, which
narrows the mouth to 221 × 121. A part sized to the 228 × 128 interior fits the box but *cannot be got
into it*. `installable_x/y()` exists for this and every internal part is sized
against it.

**Vent cartridge screws could not use heat-set inserts.** Once the 3 mm flange
recess is cut there is only 5.5 mm of material left, and the frame cannot grow
inward because the PSU is 6.5 mm away. Self-tapping M3 into a 4 mm blind pilot,
instead.

**The latch had to move.** Two side latches fouled the PSU, and a cantilever only
as long as the plug (5.5 mm) would need ~10 % strain to deflect 1 mm — it would
snap, not click. One latch on the **top edge**, where both ports have clear air,
with a 12.5 mm arm running past the hook: ~1.9 % strain, which ASA takes happily.
The tail doubles as the release tab. `checks.py` asserts the strain figure.

**OCC would not chamfer the old lid's perimeter** at any length once the 14
countersinks existed on the same face, even though they were 5 mm clear of it.
Exactly the flakiness the repo's gotchas warn about. Both the lid and the tray
rim now use a **boolean** chamfer (`util.top_chamfer_tool`) — an oversized slab
minus a lofted keep-frustum, which cannot fail that way.

## 6. Watertightness is not just geometry

A 3D-printed wall is not inherently watertight — it leaks between layers. The
geometry here (gasketed snap-in lid behind a plug labyrinth, IP68 connectors,
glands, no fastener piercing the shell) gets you a sealed *design*; getting a sealed *part* also needs
≥ 4 perimeters, good layer bonding, and ideally a wipe of epoxy on the outside.
Treat the result as a solid IP54–IP65 in practice, not a certified IP67.

Downward-facing cable exits would have been better still, but the floor is fully
occupied by the PSU. The connectors are horizontal on the front wall with an
integral rain hood above the row, which is what commercial boxes of this shape do.
