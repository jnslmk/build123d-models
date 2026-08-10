# Sonicare charger holder

A wall cradle for the round Philips Sonicare charging puck. The charger drops
into a closed cup, the brush stands upright out of the top, and the whole thing
is held to the tile by double-sided foam tape on a flat bar across its back.
The bar runs past the cup on both sides and ends in a lobe carrying a **peg for
a spare brush head** — the head drops on stem-down, the way it sits on the
handle. The bar no longer hides behind the cup; that was the price of putting
the heads somewhere.

The floor is a ring: a ⌀41.6 mm hole through the middle with the charger
resting on a 3 mm seat around it, so you can push it back out with a finger once
the holder is glued to the wall. The cable leaves through a notch in the back
wall which is closed at the top and open at the bottom into that hole, then runs
left or right along a channel across the tape face toward the outlet.

The notch is open at the bottom for a reason worth stating: closed at *both*
ends it could only be threaded, and the free end of this cord has a mains plug
on it. An earlier version of this model was assembled-impossible for exactly
that reason while passing every geometric check written for it.

## Read this before you print

**Nobody here has held the charger.** Every dimension of the puck is
*researched* — taken from third-party 3D-print listings that claim to fit the
round HX6100-family base — and the cable dimensions are *assumed outright*.
Philips publishes no dimensional drawing for the base, so there is no
authoritative figure to check against. `config.py` records the provenance of
each number individually; the short version is:

| Number | Value | Provenance |
|---|---|---|
| Puck diameter | 47.4 mm | Researched. Two independent maker listings agree. Treat as ±1 mm. |
| Puck height, no post | 19.0 mm | Researched, same two listings. |
| Cord diameter | 3.0 mm | **Assumed.** It now sets the floor's thickness, and so the holder's height — a thinner cord makes a shorter holder. |
| Brush head bore | 5.0 mm | **Assumed.** What the peg stands in for. |
| Brush head width | 14.0 mm | **Assumed.** Only used to keep a stored head clear of the cup. |
| Strain-relief boot | 6.0 mm | **Assumed, and the number most likely to be wrong.** |

The cheap way to find out is to print the part and try it. If the puck does not
drop in, or will not sit flat because its cord boot fouls the slot, the fix is
one number rather than a re-model — see below.

## Re-cutting it to your charger

Measure four things: the puck's outside diameter, its height with the central
post excluded, the cord's diameter, and the diameter of the moulded strain
relief where the cord leaves the puck. Then either

- drag the sliders on the website, which clamps whatever you give it and always
  produces a part that builds and prints; or
- edit `PUCK_DIA` / `PUCK_HEIGHT` / `CABLE_DIA` / `CABLE_BOOT_DIA` in
  `config.py` and re-run `uv run check sonicare_charger_holder`.

Everything else is derived. There is no second place to change and nothing that
can be left behind: the cup, the tape bar, the slot, the channel and all five
edge treatments are expressions on those numbers.

## What the shape is for

**Closed in front.** There is no cutout, no finger scallop and no drain hole in
the front or the sides. From the room the holder reads as a plain round cup with
a toothbrush standing in it, and the charger is invisible. That is a stated
requirement, not a by-product, and `checks.py` asserts it by probing every angle
at five heights rather than by looking at a render — a render only ever shows
one side.

**The rim is level with the top of the charger.** The shallowest cup that still
hides the puck completely, so the brush handle stands clear and is easy to grab.

**The tape bar is the only thing holding it up.** It is a flat plane, wider than
it is tall, deliberately narrower than the cup so it stays hidden behind it in
front view. The cord is buried *below* that plane rather than run over it: a cord
standing even a couple of tenths proud would hold the pad off the tile along its
whole length and turn a shear joint into a peel joint. About 760 mm² of contact,
against a holder-plus-brush load of roughly 0.2 kg at 26 mm of lever arm — a
large margin for VHB-class foam tape.

**The floor is closed.** One opening only, and it is the cable's. This is a
deliberate trade in a wet room: a toothbrush drips, and nothing drains from a
closed floor except through the cable notch at the very back. If you would rather
have drainage, the honest change is to add drain holes and say so — not to widen
the cable route until it happens to work.

## Printing

PETG, 0.4 mm nozzle, 0.2 mm layers, no supports. `create()` returns the part
already in print pose: floor flat on the bed, cup mouth up, tape face standing
vertical. That happens to be the pose it is used in, but it is chosen for the
print — it makes the floor a solid first layer instead of a bridge and leaves
every wall vertical. There is no overhang anywhere in the part.

Four perimeters is plenty; this part carries almost no load. Do not skimp on the
first layer: the bed-side chamfer is elephant's-foot relief, and a splayed first
layer is what rocks the tape pad off the tile.

## Mounting

1. Choose a spot where the cord can reach the outlet running straight *down*.
   The channel exits at the bottom edge; the holder is not designed to route a
   cord upward or sideways.
2. Clean the tile with isopropyl alcohol and let it dry. Foam tape does not
   stick to soap residue.
3. **Tape both halves of the bar.** The channel runs the full height, so the
   pad is two separate pads (about 660 mm² between them). Taping only one side
   loads the joint in peel about the other.
4. Lay the cord into the channel from above and let the puck down after it,
   then press the holder to the tile for 30 seconds. Full bond strength takes
   about a day — do not hang the brush on it immediately.

## Notes for whoever changes this next

The defect worth learning from is the one no check caught: the cable channel was
closed at both ends, so the cable could not be fitted. Every geometric assertion
passed, the renders looked right, and the part was unusable -- because everything
being verified was a property of the *solid*, and nothing asserted a property of
*assembly*. `check_cable_route` now walks the cord's actual path and asserts the
junction into the floor hole; it goes red on the old shape.

Everything else that has gone wrong here has been one shape of mistake: **a face
landing exactly on another face.** Five instances, all found by sweeping the
sliders rather than by looking at the default, and every one of them announced
itself as OCC silently refusing a chamfer rather than as anything visible:

- the side channels' back face tangent to the bore, when `wall == side_depth`;
- the channel exactly as wide as the arms, when `boot == cord`;
- the arms exiting through the bar's *rounded* corner instead of its flat end;
- the cup's outer cylinder crossing that same corner arc instead of the flat
  front face;
- the cable notch's crown crowding the bore's lead-in cone;
- and the profile's blend fillets, which fit the gap between two junctions but
  not the arc on their far side — OCC's answer there is not a silent skip but a
  hard `StdFail_NotDone` that aborts the sketch, so `_profile` rebuilds a rung
  down rather than trusting one radius.

Each is now a derived bound with a named constant (`CHANNEL_OVERCUT`,
`JUNCTION_STEP`, `CORNER_CLEAR`, `RIM_KEEPOUT`) rather than a number that
happened to work at the defaults. If you add a feature cut in from the tape
plane, assume it will land on something and derive its clearance from whatever
that is.

Three lessons, in the order they cost the most:

1. **Assert what the part is for, not only what it is.** A model can be
   geometrically perfect and functionally impossible.
2. **The checks that matter sweep the parameters.** The defaults are the one
   configuration anybody looks at; every bug above was invisible there.
3. **Point-sample the solid.** Every interior defect here was invisible in an
   SVG, a render and the viewer alike.

The slider stops describe a round charging puck (35-70 mm across, 10-35 mm tall,
1.6-3.0 mm wall) rather than an arbitrary span. All sixteen corners of that box
build with every edge treatment applied and no sharp convex edges; widening it
reintroduces degenerate shapes rather than useful ones.

Every fix above was demonstrated to turn `uv run check sonicare_charger_holder`
red before it was accepted.
