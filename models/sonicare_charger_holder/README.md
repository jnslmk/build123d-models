# Sonicare charger holder

A wall cradle for the round Philips Sonicare charging puck. The charger drops
into a closed cup, the brush stands upright out of the top, and the whole thing
is held to the tile by double-sided foam tape on a flat bar across its back.
The cable is the only opening: a channel through the back, open from the bed to
the rim, deep enough that the cord lies below the surface the tape sticks to.

The channel is open at the top so the cord can be **laid in from above** with
the puck following it down. Closed at the top it would have to be threaded, and
the free end of this cord has a mains plug on it — which is to say the earlier
closed-top version could not be assembled at all.

| | |
|---|---|
| Model | `sonicare_charger_holder` |
| Parts | one |
| Material | PETG |
| Size | 52.4 mm across, 21 mm tall |
| Supports | none |

```bash
uv run show sonicare_charger_holder
uv run export sonicare_charger_holder   # STL + STEP + GLB
uv run check sonicare_charger_holder
```

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
| Cord diameter | 3.0 mm | **Assumed.** Only the channel depends on it, and the channel is oversize. |
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
closed at the top, so the cable could not be fitted. Every geometric assertion
passed, the renders looked right, and the part was unusable — because everything
being verified was a property of the *solid*, and nothing asserted a property of
*assembly*. The check that now covers it sweeps the channel's full height at
three points across its width, and it goes red on the old shape.

Two earlier bugs were invisible for a different reason — they were interior, and
the cup's own wall stands in front of them in every projection. Both were the
same mistake in different axes: the slot's floor surviving as a horizontal ledge
inside the cup, because the channel meant to remove it was first narrower than
the slot and then, at thicker walls, shallower than the wall. Merging the two
features into one open channel dissolved that class of bug rather than fixing it
again — there is no longer a slot floor to leave behind. `channel_depth` still
carries the second half of the rule, because below the floor line the channel is
a blind notch and can still stop inside the wall.

A third constraint has been deleted rather than kept: `RIM_KEEPOUT` reserved a
sliver of plain wall between the slot's crown and the bore's lead-in cone,
because OCC silently refused two chamfers when they crowded. Opening the channel
to the rim removed the crown, so there is nothing left to crowd.

Three lessons, in the order they cost the most:

1. **Assert what the part is for, not only what it is.** A model can be
   geometrically perfect and functionally impossible.
2. **The checks that matter sweep the parameters.** The defaults are the one
   configuration anybody looks at; both ledge bugs only appear elsewhere in the
   range.
3. **Point-sample the solid.** Every interior defect here was invisible in an
   SVG, a render and the viewer alike.

Every fix above was demonstrated to turn `uv run check sonicare_charger_holder`
red before it was accepted.
