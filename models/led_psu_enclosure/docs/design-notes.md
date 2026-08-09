# Design notes

Why the box is shaped the way it is. Mostly a record of constraints that are not
obvious from the geometry, and of things that were wrong first.

---

## 1. The thermal problem, and why the vent slides

The RSP-320-24 is 89 % efficient at 321 W, so it sheds **~40 W**. It is also
fan-cooled from its top cover and derates from 50 °C ambient down to 50 % load at
70 °C. Those two facts fight the word "waterproof".

### The sealed-box sum, done properly

An earlier version of this file counted only the outside of the box —
40 W / (7 W/m²·K × 0.15 m²) ≈ 30 K — and concluded that sealed was comfortable
to half load. That is optimistic by about a factor of two, because heat has to
get *into* the wall before it can leave it. The three resistances in series, for
the box as it now stands (0.147 m² of exterior, 3.5 mm ASA at k ≈ 0.17):

| | R (K/W) |
|---|---|
| inside air → inner wall face (h ≈ 20, stirred by the PSU's own fan) | 0.34 |
| through the wall | 0.14 |
| outer wall face → ambient (h ≈ 7.5, natural + radiation) | 0.91 |
| **total** | **1.39** |

| Load | Heat | ΔT | Internal at 25 °C ambient |
|---|---|---|---|
| 50 % | ~20 W | ~28 K | ~53 °C — at the derating knee |
| 75 % | ~30 W | ~42 K | ~67 °C — well into it |
| 100 % | ~40 W | ~56 K | ~81 °C — past the 70 °C limit |

So a sealed box is fine for a lightly loaded install and genuinely not fine for a
heavily loaded one, which is the argument against deciding at print time.

Both end walls therefore carry the **same** port with a **sliding shutter** in
it: `vent_shutter` (a louvred panel, screwed in once) plus `vent_slider` (a
slotted plate riding in a channel on its face). Down is open, up half a slot
pitch is shut, and it is adjusted with a thumb on a closed box. This replaced the
earlier swappable cartridge set, where changing your mind meant unscrewing a
cartridge and fitting another one you had to have printed in advance.

### What opening the sliders is actually worth

Less than it looks, and the arithmetic is worth keeping because it is what
justifies the fan in §1a.

Wide open, each port passes ~765 mm² measured on the face, ~540 mm² of throat
(a 45° slot's throat is its opening × cos 45°). Buoyancy across the 30 mm height
difference between the two ports, at a 30 K internal rise:

    Δp = ρ·g·Δh·(ΔT/T) = 1.15 × 9.81 × 0.030 × (30/310) ≈ 0.033 Pa
    v  = √(2Δp / ρK) with K ≈ 8 for two ports in series      ≈ 0.085 m/s
    Q  = v × A                                               ≈ 0.046 L/s
    P  = ρ·c_p·Q·ΔT                                          ≈ **1.6 W**

**Under 2 W of the 40 W.** And the PSU's own fan does not make that up. It is a
*recirculating* fan: the path from its outlet back to its inlet through the box
interior has near-zero resistance, while the path out one port and in the other
costs ~13 Pa at 1 L/s. Flow splits inversely with resistance, so essentially all
of it short-circuits inside the box. The PSU fan stirs the air — which is worth
real money, it is the h ≈ 20 in the table above — but it does not ventilate.

Two consequences, and neither is obvious from looking at the box:

- **The height difference between the ports earns almost nothing.** What earns
  its keep is that they are at opposite *ends*, so a fan-driven flow sweeps the
  PSU's whole length instead of looping in one corner. The low port is low
  because that is where the PSU's own case louvres are, not to make a chimney.
- **Convection alone will not cool this box at full load, vented or not.** Only
  a fan in series with a port will — hence §1a.

Three more things fall out of the geometry and are worth stating:

- **The slot tilt is the weatherproofing.** Slots are cut at 45° through the
  3 mm panel, climbing *up-and-in*, so the offset across the panel (3 mm) is at
  least the slot's own opening (3 mm) and no straight line runs from outside to
  inside. 45° is also the steepest self-supporting overhang, so the same number
  does both jobs. `checks.py` samples directly behind each opening to prove it.
- **The slider is on the outside, not behind the louvre.** Behind it would be
  tidier, but the PSU passes within 6.5 mm of these walls and the frame already
  spends 5 of them — there is no room inward at the low port. Outside it costs
  4 mm of proud panel, which a part you operate by hand wants anyway.
- **Failure is toward open.** Shut is up, held by the top block; open is down,
  where the slider rests on the detent rod. A slider that lost its friction would
  sag *open*, which overheats nothing.

`vent_blank` (fully sealed) still fits the same recess and the same two screws.
So does `vent_fan`, the original wall-mounted 40 mm cartridge — kept, but no
longer the recommended way to force air, because it replaces the louvre it sits
in. See §1a.

Ports are placed **low at the terminal end, high over the PSU's top-cover fan**,
so a fitted pair gives cross-flow. One port alone would do very little. The shelf
is slotted so the plenum under it stays connected to the high port.

This also drives the material choice: at 55–80 °C internal, **PLA creeps and is
not an option**. ASA (or ABS if shaded) is the right answer; PETG is a distant
third.

## 1a. The internal fan, and why it decides how tall the box is

§1 leaves one conclusion: nothing short of a fan in series with a port produces
real through-flow. Carrying 40 W at a 15 K air rise needs ~2.3 L/s (~5 CFM),
which a 40 mm 24 V fan reaches through a louvre and a 60 mm one reaches
comfortably. The 24 V rail is already on the PSU's output terminals.

It is mounted **inside, behind the high port's louvre**, on a printed yoke
(`vent_fan_yoke`), rather than in the wall like `vent_fan`. That is the whole
point: the tilted-slot labyrinth stays in front of the blades, so forced
ventilation costs nothing in weatherproofing. Fitting it does mean the high port
can no longer take a `vent_blank` — the plug body and the fan want the same
volume, and `checks.py` asserts that mutual exclusion rather than treating the
clash as a bug.

**Only the high port can host it.** At the low port the PSU passes within 6.5 mm
of the wall and the frame already spends 5 of them. The high port is above the
PSU, which is the only place inside this box with 10 mm of depth to spare.

### The depth budget, which is where it nearly did not fit

    inner wall face                x = 114.0
    fan, 40 × 40 × 10              x = 104.0 … 114.0   (face flush, blowing in)
    yoke plate, 2.5 mm             x = 101.5 … 104.0
    controller's mounting tab tip  x = 103.0           ← 1.0 mm

The controller's tabs overhang its body by 8 mm at each end and are the furthest
thing along X on the shelf. With 204.2 mm of component (fuse block 86.2 +
controller 118) on a 215 mm shelf there is nowhere to move them to, so the layout
works by a millimetre and by one deliberate trick: **the tab passes through the
yoke's own throat.** The yoke's Ø38 bore is centred on the fan, the tab crosses
it 8–11 mm below centre where the bore is still ~35 mm wide, and there is simply
no plate there. `check_internal_fan()` samples the yoke at the tab's actual
coordinates instead of trusting the arithmetic.

### Why its screws are beside the fan, not above and below it

The yoke's four M3s go into blind pilots in the frame's **side** bands, at the
same radius as the shutter's own screws but offset 12 mm in Z (the two sets are
driven into opposite faces of a 5.5 mm slab and would otherwise meet head-on).

The obvious alternative — screws above and below the fan — costs about 7 mm of
enclosure, and the chain is worth spelling out because it is not intuitive:

1. The yoke's lowest edge hangs over the PSU's plan, so it cannot go below the
   top cover. That fixes how low the high port can sit.
2. The port's frame must finish below `rim_band_z()`, or it narrows the mouth.
3. So `interior_z` ≥ port centre + aperture/2 + frame margin + rim band.

Rails above and below the fan add ~7 mm to step 1 and therefore ~7 mm to the box.
Rails at the sides add nothing. `config.interior_z()` computes all of this, so
changing `VENT_FAN_SIZE` to 30 re-derives a box 5 mm shorter, and the trade is
visible instead of buried.

## 2. The PSU nearly fills the box, and everything follows from that

The PSU is 215 × 115 inside a 228 × 125 interior — **6.5 mm to the end walls,
5 mm to the front and back**. An SP1712 needs 19.7 mm behind the panel plus wire
bend room, so *no wall at PSU height can host a connector*. This is the
constraint that shapes the layout:

- The shelf underside sits **13 mm above the PSU** — the top-cover fan needs a
  plenum to breathe into, and ~0.25 × D is the floor for a Ø50 fan.
- The connectors go in the **front wall at z = 74**, in the space above the PSU.
- Everything mounted on the shelf is held **36 mm back from the front wall**
  (`SHELF_FRONT_KEEPOUT`) so the connector bodies have somewhere to be. That
  number is set by the deepest intruder — the RJ45 coupler at 32 mm — not by the
  SP1712s at 19.7 mm.
- The vent frames are capped at 5 mm thick because thicker would foul the PSU.
- The PSU plate is only 0.5 mm bigger than the PSU, for the same reason.
- **X is not compressible.** 215 mm of PSU plus 5 mm of vent frame plus 1.5 mm of
  drop clearance at each end *is* the 228 mm interior.

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
- **Vent shutter screws** are blind self-tapping pilots.

The only holes through the wall are the ones a sealed component deliberately
fills.

## 5. Things that fought back

**The rim opening is not the interior.** The wall thickens inward over the top
12 mm to give the rim ring enough width for the gasket and snap grooves, which
narrows the mouth to 221 × 118. A part sized to the 228 × 125 interior fits the
box but *cannot be got into it*. `installable_x/y()` exists for this and every
internal part is sized against it.

**...and the rim opening is not the narrowest point either.** The two vent
frames stand 5 mm proud of the end walls, so the real clear opening in X is
**218 mm**, not the mouth's 221. The shelf was sized as `installable_x() - 3`,
which came out at exactly 218 — *zero clearance* against the frames it has to
slide past, on the largest printed dimension in the box. It passed the old check
because that check compared against the mouth with a `<=`. `drop_opening()` now
returns the minimum of the two, every drop-in part is sized against it, and
`check_installability()` demands a real ≥ 0.5 mm per side.

**Vent screws could not use heat-set inserts.** Once the 3 mm flange recess is
cut there is only 5.5 mm of material left, and the frame cannot grow inward
because the PSU is 6.5 mm away. Self-tapping M3 into a 4 mm blind pilot, instead.

**The shutter has no snap latch, on purpose.** The cartridges have one (a top-edge
cantilever with a 12.5 mm arm: ~1.9 % strain, which ASA takes happily — side
latches fouled the PSU and a plug-length arm would have needed ~10 % strain to
deflect 1 mm). A latch is what makes a part you *swap in the dark* click home.
The shutter is fitted once and then adjusted in place, so it is held by the two
screws that were always what compressed the gasket, and the cantilever goes away
with the swapping it existed for. `checks.py` still asserts the strain figure for
the cartridges.

**The cartridge gasket groove was on the wrong face.** It was cut from local
z = 0, which is the *outer* face — the weather side — so the cord had nothing to
seal against and the flange met the recess floor bare. Both families now cut the
groove on whichever face beds against the recess floor. The same pass opened up
`vent_fan`'s flange, which was a solid plate: the fan had been blowing straight
into it.

**A slider needs somewhere to be inserted.** Both ends of the channel cannot be
closed or the slider can never get in, and an open end at the top would let it be
pushed out. Hence: solid block at the top (the shut stop), open at the bottom
(insertion, and drainage for anything that gets past the slider), and a detent
rod across the mouth that the slider clicks over once. The rod is the open stop,
the click, and the retainer — the slider has to be lifted 0.4 mm out of plane to
pass it, and it has 0.45 mm of slack in the channel to do that with.

**OCC would not chamfer the old lid's perimeter** at any length once the 14
countersinks existed on the same face, even though they were 5 mm clear of it.
Exactly the flakiness the repo's gotchas warn about. Both the lid and the tray
rim now use a **boolean** chamfer (`util.top_chamfer_tool`) — an oversized slab
minus a lofted keep-frustum, which cannot fail that way.

## 5a. Making it smaller: what was there, and what was not

The box was 235 × 135 × 121.5 (3.85 L). It is now **235 × 132 × 111.5 (3.46 L)**,
about 10 % less, and the interesting part is where the millimetres came from —
because most of the places that *look* like slack are not.

**Taken:**

| | | |
|---|---|---|
| Plenum over the PSU's fan | 23 → 13 mm | 0.25 × D is the published floor for a Ø50 fan; 23 was a guess |
| Y clearance around the PSU | 6.5 → 5.0 mm a side | nothing lives there; the vent frames are on the X ends |
| Rim band | 15 → 12 mm | it only has to swallow the 10 mm lid plug |
| PSU-plate boss | 6 → 5 mm | see below — this one nearly was not available |
| Connector row | z = 85 → 74 | it follows the shelf down |

The rim band is worth 1:1 twice over, because the vent frame has to finish below
it *and* the band sits on top of everything: 3 mm off the band is 3 mm off the
box.

**Refused:**

- **The 10 mm under the PSU plate is not dead air — it is the snap studs' spring
  length.** The C-spring tube runs from its base block to the head, and
  cantilever strain goes as 1/L², so trimming the boss from 6 mm to 3 mm would
  have taken the stud from 1.5 % strain to ~12 %: it would snap on the first
  press instead of clicking. 6 → 5 mm was available (2.0 %, still inside the
  2.5 % the check enforces); anything more was not. `PSU_PLATE_BOSS_H` now carries
  a comment saying so, because it is the most obviously trimmable number in the
  file and it is a trap.
- **X, entirely.** 215 mm of PSU + 5 mm of vent frame + 1.5 mm of drop clearance
  at each end is 228 mm. There is nothing to give unless the vents move off the
  end walls, which would cost the cross-flow.
- **A flat side-by-side layout** (PSU and electronics on one floor, ~235 × 208 ×
  58) was costed and dropped. It is 2.86 L on paper, but the exterior surface
  comes out at 0.150 m² against 0.147 — no thermal gain — the total shell area is
  within 2 %, so it is the same print mass, and the footprint grows 55 %. A
  quarter less volume for half again the bench space is not a trade worth a
  redesign.

**And one thing got bigger on purpose:** clearance over the fuse block went from
9.3 mm to 10.3. At 9.3 you could not get a finger to an ATO fuse — changing one
meant lifting the whole wired shelf out. It is now the chain that *sets* the box
height (`config.interior_z()`), which is the right thing to be bound by: the box
is as short as its tallest component plus room to service it.

## 6. Watertightness is not just geometry

A 3D-printed wall is not inherently watertight — it leaks between layers. The
geometry here (gasketed snap-in lid behind a plug labyrinth, IP68 connectors,
glands, no fastener piercing the shell) gets you a sealed *design*; getting a sealed *part* also needs
≥ 4 perimeters, good layer bonding, and ideally a wipe of epoxy on the outside.
Treat the result as a solid IP54–IP65 in practice, not a certified IP67.

Downward-facing cable exits would have been better still, but the floor is fully
occupied by the PSU. The connectors are horizontal on the front wall; the row is
bare (an integral rain hood over it was tried and dropped), so mount the box
under cover or rely on the connectors' own IP68 seals for splash protection.

## 7. The portable variant, and where 24 V comes from without mains

Not built, and nothing in this package depends on it — this section exists so the
option is on the record with its arithmetic done, because it was contemplated
twice and re-argued from scratch both times.

The premise: a box that runs a few lamps off a battery, on a site with no socket
or on a shoot. Two candidate sources were considered, **USB-C Power Delivery**
and a **Bosch 12 V power-tool pack** (including the cheap AliExpress clones of
it). The numbers are in [`part-data.md`](part-data.md#portable-power-sources)
with sources; this is the argument.

**The load.** A lamp is 1.5 m of 24 V FCOB WS2811 dual-IC RGBCCT at a spec
19 W/m, so **~30 W at full white**, and the family's own thermal note budgets
30–45 W. Every lamp count below is at 30 W; halve your expectations of it at
saturated colour and double them at anything resembling normal use.

### The premise that was backwards: USB-C needs *less* converter, not more

The reason the Bosch route was attractive was "12 V is closer to 24 V, so no step
up". It is the other way around, twice over:

- **A "12 V" tool pack is 3S Li-ion — 12.6 V full, 10.8 V nominal, ~9 V at
  cutoff.** It is *always* below 24 V, so it always needs a **boost**, across a
  1.4:1 input window, at ~10 A in for 100 W out (and ~12 A by the time the pack
  is flat). Boost is the harder direction: input current is the output current
  times the ratio, so the inductor, the input cap and the pack's own BMS all see
  the ugly side.
- **USB-C PD 3.1 EPR can just be asked for 24 V.** EPR's *Adjustable Voltage
  Supply* is a 15–48 V range in 100 mV steps, so a trigger set to 24.0 V gives
  24 V off the connector with **no converter in the box at all** — a wire and a
  fuse. Capped at 5 A, that is **120 W**. Where AVS is not on offer, the fallback
  is the 28 V fixed PDO and a **buck** to 24 V, which is the easy direction.

So on electronics complexity the ranking is the reverse of the one that motivated
looking at Bosch: PD trigger only < PD trigger + buck < tool pack + boost.

### What each one can deliver

| Source | Bus | Ceiling | Conversion | At 24 V | Lamps @30 W |
|---|---|---|---|---|---|
| PD 3.0 SPR (any laptop charger/bank) | 20 V | 100 W | boost 20→24 | ~92 W | 3 |
| **PD 3.1 EPR, AVS at 24 V** | 24 V | **120 W** (5 A) | **none** | 120 W | **4** |
| PD 3.1 EPR, 28 V fixed | 28 V | 140 W | buck | ~133 W | 4 |
| PD 3.1 EPR, 36 V / 48 V fixed | 36/48 V | 180 / 240 W | buck | ~171 / 228 W | 5 / 7 |
| Bosch 12 V pack + boost | 10.8 V | pack, not bus | boost 12→24 | 100 W typ. | 3 |

Two ceilings are not what the spec sheet says:

- **36 V and 48 V do not exist on a battery.** They are mains-brick PDOs. Every
  EPR *power bank* on the market tops out at 28 V / 5 A = **140 W**, so a portable
  USB-C build is a 140 W build no matter what PD 3.1's headline 240 W says. Above
  100 W it also needs a 240 W e-marked cable, which is a real thing to get wrong.
- **The Bosch ceiling is thermal and temporal, not electrical.** A 3S pack on
  HG2/VTC6-class cells will pass 20–25 A, which is 240 W through a boost — and
  empties a 6.0 Ah pack in **16 minutes**. Rating the box for what the pack can
  momentarily source is meaningless; it is sized by energy.

### Which is the real constraint: energy, and it is close

Both sources are within a factor of 1.5 of each other and both are small.

|  | Nameplate | Delivered at 24 V | 3 lamps (90 W) |
|---|---|---|---|
| Power bank, 140 W class | 83–99.5 Wh | ~75–86 Wh | 50–57 min |
| Bosch GBA 12V 6.0Ah | 64.8 Wh | ~58 Wh | 39 min |
| Bosch GBA 12V 2.0Ah | 21.6 Wh | ~19 Wh | 13 min |

**A power bank cannot get much better than that**, and the reason is regulatory
rather than technical: 100 Wh is the airline carry-on limit, so the whole premium
end of the market stops just under it (the Anker Prime is 99.54 Wh, which is not
a coincidence). Buying a more expensive bank buys ports and watts, not hours.

The Bosch side has the opposite shape — **65 Wh is the ceiling per pack, but packs
swap in five seconds and you probably own four.** That, and nothing else, is the
honest case for the tool battery: not cost, not simplicity, not power. If the
portable variant is for a shoot where someone is standing next to it with a bag
of charged packs, Bosch wins on the only axis that matters. If it is for a
demo you carry onto a train, USB-C wins.

### Cost, which does not go the way the "cheap clones" framing suggests

Per nameplate watt-hour, at mid-2026 German street prices:

| | Price | Wh | €/Wh |
|---|---|---|---|
| AMEGAT 140 W, 27 600 mAh | ~€70 | 83 | **€0.84** |
| INIU 140 W, 27 000 mAh | ~€80 | 85 | €0.94 |
| Anker 737 (PowerCore 24K) | ~€100 | 89 | €1.12 |
| Anker Prime 27650, 250 W | ~€140 | 99.5 | €1.41 |
| Bosch GBA 12V 6.0Ah | ~€64 | 64.8 | €0.99 |
| Bosch GBA 12V 2.0Ah | ~€27 | 21.6 | €1.25 |
| "3.0 Ah" clone (Advtronics/Vanon) | ~€22 | 32.4 *claimed* | €0.68 *claimed* |
| ...the same clone, **measured** | ~€22 | **~19** | **€1.16** |

**The cheap clones are not cheap.** Independently tested, the €22 "3.0 Ah" packs
returned 1.5–2.0 Ah, which puts them level with or worse than a genuine Bosch
2.0 Ah at €27 and clearly behind the 6.0 Ah — the one case where the cheap option
loses on its own metric. And a budget 140 W power bank beats every Bosch pack on
€/Wh outright.

The box-side hardware is noise next to either:

| | |
|---|---|
| PD trigger board, 28 V/140 W, DIP-selectable | €5–10 |
| Buck 28→24 V, 150 W | €8–15 |
| Boost 12→24 V, 10 A / 240 W, synchronous | €10–20 |
| Bosch battery foot, bought | €9–13 |
| Bosch battery foot, **printed here** | filament |

So the marginal cost of the decision, for someone who already owns one side or
the other, is **~€8 for USB-C** (a trigger board and a fuse) against **~€25 for
Bosch** (foot plus a boost module that is actually rated for 10 A input). The
printed foot is the interesting half of the Bosch route from this repo's point of
view — it is exactly the sort of part this package would gain — but note that a
tool-pack foot has to carry a BMS that may trip on a boost converter's inrush and
has no low-voltage cutoff of its own beyond the pack's.

### What the portable variant does to the box

Enough that it is a different model, not a parameter — which is why this is a
note and not a `config.py` flag:

- **The RSP-320 is the box.** §2: 215 mm of PSU + 5 mm of vent frame + 1.5 mm of
  drop clearance each end *is* the 228 mm interior, and the connector row exists
  where it does only because no wall at PSU height can host one. Delete the PSU
  and every constraint in §2 evaporates. What is left — controller (118 × 65),
  fuse block (86 × 53 × 41.7) and a converter — packs into roughly 140 × 90 × 60.
- **The thermal apparatus goes too.** §1 sizes the vents and the fan against 40 W
  of PSU loss. A 140 W-in build sheds maybe 8–12 W in the converter, which the
  sealed-box sum in §1 handles at ~15 K rise. No shutters, no fan, no yoke — and
  PLA becomes defensible again, though ASA still wins outdoors.
- **The mains gland is replaced by the socket**, and the whole `⚠ check your
  gland` problem in the README goes away with it.
- **Four fused outputs stop making sense.** 120–140 W is 4 lamps at the very most
  and one connector's worth of current; two outputs and one fuse is the honest
  layout.

### The conclusion, for whoever picks this up

**USB-C PD 3.1 EPR, AVS at 24 V, is the recommended portable source** — cheapest
per watt-hour, most power (140 W against a Bosch pack's usable ~100 W), least
electronics (no converter at all where AVS is offered), and the source is a thing
people already carry. Keep the Bosch foot as a *second* input on the same 24 V
bus for the hot-swap case; it is a €25 option, not an architecture.

Either way the portable variant is **energy-limited, not power-limited**: an hour
of three lamps is what an hour of three lamps costs, and no amount of connector
spec changes it. Running the triangle assembly for an evening is what the
RSP-320 box in this package is for.
