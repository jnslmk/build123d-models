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

Ø12 x 12 mm body, Ø12 x 15 mm screw, 16 mm tall assembled and closed on an
empty clamp -- and a millimetre more than that per millimetre of wire in it. Thread a
loop of wire in through one side of the window and out the other, turn the knob
finger tight, and it holds. Back the knob off and the wire slides again -- so
it tensions a line, or ends a loop, without a knot and without a crimp.

Built for 1 mm, and **parametric from 0.5 to 6.0 mm on the website** -- one
control, which sizes everything:

| Wire | Thread | Body | Screw | Bore × channel | Filament |
| --- | --- | --- | --- | --- | --- |
| 0.5 mm | 8.0 × 2.5 | Ø11.1 × 11.6 | Ø11.1 × 14.1 | 6.5 × 8.3 | 1 g |
| **1.0 mm** | **8.0 × 2.5** | **Ø12.1 × 12.3** | **Ø12.1 × 14.8** | **6.5 × 9.3** | **2 g** |
| 2.0 mm | 9.0 × 2.5 | Ø15.1 × 15.8 | Ø15.1 × 17.6 | 7.5 × 12.3 | 3 g |
| 3.0 mm | 11.0 × 2.5 | Ø19.1 × 20.1 | Ø19.1 × 21.2 | 9.5 × 16.3 | 6 g |
| 4.0 mm | 13.0 × 2.5 | Ø23.1 × 24.5 | Ø23.1 × 24.9 | 11.5 × 20.3 | 10 g |
| 5.0 mm | 15.0 × 2.5 | Ø27.1 × 28.9 | Ø27.1 × 28.6 | 13.5 × 24.3 | 16 g |
| 6.0 mm | 17.0 × 2.5 | Ø31.1 × 33.2 | Ø31.1 × 32.2 | 15.5 × 28.3 | 24 g |

The pitch column never moves. That is the point — see below.

The control is on the two printed parts and on the one-plate layout, not only on
the assembly, because the website reads a model's parameters off whichever model
is on screen. Take `wire_clamp.printable` if you want a guaranteed matched pair:
both parts come off the same setting.

**Why it stops at 6 mm.** Nothing breaks above it — the geometry stays valid —
but past there the clamp stops being the right tool. The wire passages cost a
cord diameter at each end of the slot, so the body runs about `4 × d` across
against the original's `3 × d`; the ratio has already flattened out by 6 mm, so
going bigger buys bulk rather than proportion; and four bends through a slot are
what a thin, stiff, slippery line needs, where rope that thick is compressible
enough that the original's rim-nip works. Its own files cover 3–12 mm and are
five times smaller there. So: below 6 mm this model is the better tool, above it
the original is.

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
| Clearance, diametral | **0.40 mm** | 0.31 mm | 0.60 mm |
| Flank angle | 45° | 45° | 45° |
| Engagement | **0.75 × D** | 2.5 mm (0.32 × D) | 4.8 mm (0.32 × D) |

Every bold figure is above the floor the `fasteners-and-inserts` skill's
printable-thread table sets, and `checks.py` runs that table over this thread
*and* over the original's at both ends of its range -- the original passes at
12 mm and fails three of four rules at 3.1 mm. The clamp is 12 mm across because
the thread is 8 mm across; the wire has nothing to do with it.

**Only as much thread as the joint needs.** 2.4 turns of female thread and 2.2 of
male at the default size, at 0.75 × D of engagement rather than the 1.0 × D the
printed-thread table asks for — that rule is written for a structural thread, and
this one carries a finger. `config.THREAD_ENGAGE_RATIO` shows the arithmetic
(0.4 Nm of finger torque, K=0.30 through a printed thread, sheared over the root
flats) and `checks.py` computes 7.6 MPa against ABS's ~20 MPa across layers at
every slider position, failing under a factor of two. The bore's lead-in is the
thread's own chamfered last turn rather than a cone with a pitch of plain collar
under it, which took 3.3 mm off the body and the same off the screw.

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

- Both parts carry a 0.8 mm bevel on **both** rims, bottom as well as top, which
  scales up on the larger sizes. The bed-facing one is also elephant's-foot
  relief; the top one yields where the bore's lead-in is already eating into the
  same face, so the two never meet in a knife edge.
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
