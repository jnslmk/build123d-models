# Wire clamp

A screw clamp for thin wire and cord: reconstruction of [Printables 591325,
*Adjustable Rope Clamp Rope Tensioner (Parametric)*][src] by Twotone74, rebuilt
for **1 mm wire** and around a thread a 0.4 mm nozzle can actually print.

```bash
uv run show wire_clamp                # the assembled clamp, wire and all
uv run export wire_clamp.body         # the STL to print
uv run export wire_clamp.screw
uv run export wire_clamp.printable    # both, on one plate
uv run check wire_clamp
```

[src]: https://www.printables.com/model/591325-adjustable-rope-clamp-rope-tensioner-parametric

## What it is

Ø12 x 17 mm body, Ø12 x 20 mm screw, 22 mm tall assembled and closed on an
empty clamp -- and a millimetre more than that per millimetre of wire in it. Thread a
loop of wire in through one side of the window and out the other, turn the knob
finger tight, and it holds. Back the knob off and the wire slides again -- so
it tensions a line, or ends a loop, without a knot and without a crimp.

Built for 1 mm, and **parametric from 0.5 to 4.0 mm on the website** -- one
slider, which sizes everything:

| Wire | Thread | Body | Screw | Slot |
| --- | --- | --- | --- | --- |
| 0.5 mm | 8.0 × 2.5 | Ø11.1 × 16.3 | Ø11.1 × 19.6 | 6.5 × 8.3 |
| **1.0 mm** | **8.0 × 2.5** | **Ø12.1 × 17.0** | **Ø12.1 × 20.3** | **6.5 × 9.3** |
| 2.0 mm | 8.0 × 2.5 | Ø14.1 × 19.4 | Ø14.1 × 22.4 | 6.5 × 11.3 |
| 2.9 mm | 8.5 × 2.5 | Ø16.4 × 22.2 | Ø16.4 × 24.8 | 7.0 × 13.6 |
| 4.0 mm | 10.5 × 2.5 | Ø20.6 × 27.0 | Ø20.6 × 29.2 | 9.0 × 17.8 |

The pitch column never moves. That is the point — see below.

The slider is on the two printed parts and on the one-plate layout, not only on
the assembly, because the website reads a model's parameters off whichever model
is on screen. Take `wire_clamp.printable` if you want a guaranteed matched pair:
both parts come off the same setting.

## Why it is bigger than the wire suggests

Because a printed thread has a minimum size and a wire does not.

The original is published in ten sizes from 3 to 12 mm rope, and the ten are one
shape scaled ten ways: **every dimension, the thread included, is a fixed
multiple of the rope diameter**. At the top of that range the thread has a
2.16 mm pitch and a 0.60 mm tooth and prints beautifully. At the bottom the same
ratios give a 1.12 mm pitch and a **0.31 mm tooth** -- narrower than a single
0.4 mm extrusion, with 5.6 layers to a turn -- so the 3 mm clamp's thread is not
a tight thread, it is a thread the printer never resolved. In ABS it is worse
again, because the warp on a 9 mm cylinder is bigger than the whole tooth is
tall. Carry the scaling on down to 1 mm wire and you get a 3 mm bead with a
0.36 mm pitch.

So the thread here is split in two. **Pitch, tooth, crest flat and clearance are
absolute** and identical at every slider position — those four are what the
nozzle has to resolve, and each has a floor. The **diameter** does follow the
wire, from an 8 mm floor upward, because it is the one thread dimension with no
floor to fall through: the plunger passes *through* the thread to be assembled,
so the thread caps how wide a pair of strands can be, and a bigger thread is
strictly easier to print than a smaller one.

The original scales the numbers a printer has to hit. This scales the number a
printer does not care about:

| | this model | original at 3.1 mm | original at 6 mm |
| --- | --- | --- | --- |
| Major diameter | 8.00–10.50 mm | 7.75 mm | 15.00 mm |
| Pitch | **2.50 mm** | 1.12 mm | 2.16 mm |
| Tooth, radial | **0.75 mm** | 0.31 mm | 0.60 mm |
| Crest flat | **0.50 mm** | 0.30 mm | 0.58 mm |
| Layers per turn @ 0.2 mm | **12.5** | 5.6 | 10.8 |
| Clearance, diametral | **0.50 mm** | 0.31 mm | 0.60 mm |
| Flank angle | 45° | 45° | 45° |
| Engagement | **1.0 × D** | 2.5 mm (0.32 × D) | 4.8 mm (0.32 × D) |

Every bold figure is above the floor the `fasteners-and-inserts` skill's
printable-thread table sets, and `checks.py` runs that table over this thread
*and* over the original's at both ends of its range -- the original passes at
12 mm and fails three of four rules at 3.1 mm. The clamp is 12 mm across because
the thread is 8 mm across; the wire has nothing to do with it.

`checks.py` re-runs the gate, the kinematics and the wire path at five slider
positions — including one either side of the point where the thread steps up —
and takes a boolean between the two solids across the plunger's whole travel at
both ends of the range. The website slider can make the thread bigger. It cannot
make it finer. That is the fix.

## The other change: the wire goes *past* the plunger

The original's plunger is a disc 0.3 mm smaller than a round bore, so nothing
thicker than 0.3 mm can get underneath it. A rope is not clamped against the
floor -- it is nipped between the plunger's rim and the window sill and
squashed, which works well on something compressible with a lot of surface.

A 1 mm wire is neither compressible nor grippy, and a rim nip on a plastic part
yields the plastic before it holds the wire. So the channel here is a **slot**:

- **as wide as the plunger** (0.11 mm a side), which guides it and means a
  strand cannot escape sideways from under it;
- **longer than the plunger by a wire's width at each end**, so the wire's two
  legs run down past it.

Tightening therefore pulls the wire *through*: down over one sill, flat along
the ribbed floor under the plunger, up over the other sill and out. Four bends
and a squeeze, instead of a squeeze. Both halves are asserted in `checks.py` --
a passage wider than the wire along it, a gap narrower than the wire across it.

Everything else is the original's: the window's proportions, the ribbed floor,
the concentric ridges on the plunger's face that cross those ribs, the
ten-lobed knob flush with the body.

## Printing

**ABS**, because the reported failure was an ABS one and these sizes are the
ones that survive it. PETG and PLA print the same files and are more forgiving.

- Both parts are already in print pose. The body stands on its base; the screw
  lies **knob down**, which puts a 12 mm disc on the bed and leaves nothing
  unsupported.
- **No supports.** The only downward-facing thing that is not a 45° cone is the
  top of the window, a 4.9 mm bridge.
- **4 perimeters**, so the thread is perimeter all the way through and never
  infill. 0.2 mm layers or finer: the rule is at least six layers to a turn and
  2.5 mm of pitch gives twelve.
- ABS wants an enclosure and a brim. The body's Ø12 base is small enough that a
  lifted corner takes the thread out of round with it, which is the failure this
  model is a response to.

## Using it

1. Back the knob out until the plunger clears the top of the window. It will not
   come out -- a turn and a half of thread is still engaged there.
2. Push the wire in through one side of the window and out the other. Both legs
   of a loop go through the same window, side by side.
3. Turn the knob finger tight. The wire is pulled down into the slot as you go.
4. The knob stands proud of the body by about the wire's diameter when it is
   holding. Flush means there is nothing in there.

## Files

| | |
| --- | --- |
| `config.py` | every number, and which of the two rules set it |
| `thread.py` | the one 45° trapezoid, for whichever half asks |
| `body.py` | the part with the window |
| `screw.py` | knob, thread, plunger |
| `wire.py` | the wire in the assembly view -- a mock-up, not a part |
| `printable.py` | both parts on one plate |
| `checks.py` | the assertions, including the thread gate |
| `docs/reverse-engineering.md` | what the original measures, and how it was measured |
