# Cable spool

A 180 mm reel for a coiled patch cable. Four printed parts, no hardware: three
identical discs stack on one hub at three heights and leave two 7 mm channels
between them, and three clips hold the stack together at the rim.

```bash
uv run show cable_spool           # assembled
uv run export cable_spool.base    # the STLs to print
uv run export cable_spool.middle
uv run export cable_spool.cover
uv run export cable_spool.clip    # print three
uv run check cable_spool
```

## What it fits

About 20 m of round Cat-5e/Cat-6 patch cable up to 6 mm across, wound in two
layers. The winding depth is 65 mm a side (hub at r = 25, rim at r = 90) and
each channel is 7 mm clear. A flat patch cable fits the same channels with room
to spare; anything fatter than 6.5 mm will not lie flat at the crossover.

## Where it comes from

The three discs are a parametric reconstruction of
[Printables 27496 — "cable spool ethernet cable"](https://www.printables.com/model/27496-cable-spool-ethernet-cable)
by rgeissler, measured off the published STLs. `docs/design-notes.md` is the
measurement ledger — every number, whether it was read, solved or re-derived,
and how closely the result grades against the original mesh.

**The clip is not a reconstruction.** The original's falls off, and the mesh
says why in three independent ways; `clip.py` carries the argument and
`docs/design-notes.md` §4 has the numbers. The replacement holds on with a
detent that drops into one of the base's own windows instead of by clamping.

## Printing

| Part | Qty | Notes |
| --- | --- | --- |
| `cable_spool.base` | 1 | 180 mm disc with the hub. The biggest part; needs a 200 mm bed |
| `cable_spool.middle` | 1 | 2 mm plate |
| `cable_spool.cover` | 1 | 2 mm plate |
| `cable_spool.clip` | 3 | ~9 g each |

**Material: PETG**, and for the clips that is not the house default talking —
the detent arm is a spring, and PETG's 1.0% repeated-use allowable strain is
what the arm is sized against. In PLA the same arm is over its limit and will
crack rather than flex. The discs are indifferent; print them in whatever you
like.

Every part is supplied in print pose and none of them needs supports. The
discs go on the bed chamfered-face-up. The clips stand on their lower jaw; the
only overhang on the whole model is the 3.8 mm ledge under a clip's upper jaw,
which is inside what any printer bridges unsupported.

Suggested settings: 0.2 mm layers, 3 perimeters, 20% infill. The clip's detent
arm is 1.8 mm thick — four perimeters at a 0.4 mm nozzle — so it comes out
solid whatever the infill is.

## Assembly

1. **Thread the cable's end down the hub** and out through the full-height slot
   before you wind anything. That anchors the tail; without it the first turn
   pulls the whole coil round.
2. **Wind the lower channel**, then drop the **middle disc** down the hub. Line
   its four relief pockets up with the four guide ribs — it will not go past
   them otherwise — and turn it until its two keys drop into the hub's two
   slots. It comes to rest on the collar, 7 mm above the base.
3. **Wind the upper channel** and drop the **cover** on. It has no relief
   pockets, so it stops on the rib tops and leaves the second channel clear.
4. **Push the three clips on**, each centred on a window. Push straight in
   until the detent clicks. Three windows apart is 120 degrees, which is
   exactly where you want them.

To take a clip off again, lift the spool and press the free end of the arm
under it down about 2 mm, then slide the clip out. It does not pull off — see
below.

## Why the clip is captive

The catch is a vertical face, and it has to be. It engages the outer wall of
one of the base's windows, which is a 2 mm-tall step inside a 2 mm-thick plate;
there is no room to slope the catch back and still have it reach that wall. A
sloped catch would be a clip that can be pulled off, and a clip that can be
pulled off is the thing this design exists to stop.

The trade is deliberate: fitting takes about 8 N of straight push, removing one
takes a deliberate press on a tab you can see. The original clip took nothing
at all to remove, which is the complaint.

## Spinning it while you wind

There is a 2.5 mm hole straight through the middle of the hub. Put a nail or a
length of filament through it and the whole spool turns on it, which makes
winding 20 m a two-handed job instead of a four-handed one. (The source model's
hole is blind from the top and cannot do that.)

## Credits

Original design: rgeissler, [Printables 27496](https://www.printables.com/model/27496-cable-spool-ethernet-cable).
The discs here follow that geometry; the clip does not.
