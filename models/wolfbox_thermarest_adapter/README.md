# WOLFBOX MF100 → Therm-a-Rest inflation adapter

A funnel that lets a cordless air duster inflate a sleeping pad. The narrow end
pushes onto the blower's outlet, the wide end presses over the mattress valve.

```bash
uv run export wolfbox_thermarest_adapter   # the STL to print
uv run check  wolfbox_thermarest_adapter
uv run view   wolfbox_thermarest_adapter   # look at it first
```

47 mm tall, 36 mm across at the rim, about 7 cm³ — under 10 g of PETG and well
under an hour on any machine.

## Read this first: no dimension here was measured

Nobody in this repo has held an MF100 or a WingLock valve, and neither
manufacturer publishes a drawing of the interface. Every port diameter in
`config.py` is **assumed**, inside a range that is **researched** — the ledger
in that file names which is which, source by source.

That is why both ends are cones rather than copies. A taper seats wherever it
meets the port, so the socket works anywhere between Ø16 and Ø27 mm and the cup
anywhere between Ø22 and Ø34 mm, and a wrong guess changes *where* it seats
rather than *whether* it fits. A cloned bayonet or a cloned snap groove would
have been all-or-nothing.

**If you have callipers, use them.** Six numbers, all sliders on the website or
keyword arguments to `create()`:

| Symptom | Slider | Which way |
| --- | --- | --- |
| Socket bottoms out on the blower before it grips | `blower_mouth_dia` | down |
| Socket wobbles / slides straight on with no wedge | `blower_mouth_dia` | up |
| Socket goes on but the blower feels throttled | `blower_throat_dia` | up |
| Socket pops off under the blower's thrust | `socket_depth` | up |
| Cup rests on the valve's rim and rocks | `valve_seat_dia` | down |
| Cup swallows the valve and touches the pad fabric | `valve_seat_dia` | up |
| Cup will not drop over the valve's wings at all | `valve_mouth_dia` | up |
| Cup seats before it seals | `cup_depth` | up |

Re-export after a change; there is nothing to re-model.

## How to use it

1. Twist the stock nozzle off the MF100. The socket is sized for the bare
   outlet — it will also grip the body of a nozzle left on, just further in and
   with less air.
2. Push the socket on firmly. It wedges; it does not lock.
3. Open the pad's valve to inflate (wings out on a WingLock, so the one-way
   flap is doing the work).
4. Press the cup down over the valve and hold it. The blower's thrust helps
   seat it. Run the duster on its lowest useful speed — the pad wants volume,
   not pressure.
5. Take it off with a pull, close the valve, and top the pad off by mouth if
   you like it firm. A fan cannot beat a lung for the last few percent, which
   is the one thing this adapter does not change.

Nothing here latches, on purpose: at the end of a fill the fan is pushing
against a pad that is nearly full, and an adapter that could not simply be
lifted off would be the wrong tool to be holding.

## Printing

PETG, 0.2 mm layers, no supports, already in print pose — socket mouth on the
bed, cup mouth up. Three perimeters everywhere is plenty; the walls are 2.4 mm
at the socket and 1.2 mm at the cup, so the slicer will fill them with
perimeters either way.

The bore self-supports: every internal surface is vertical or leans outward as
it rises, except the 45° flare off the throat, which is the steepest angle that
prints dry.

**TPU 95A prints this file better than PETG does.** The cup wall is thin
because it is the sealing face, and an elastomer conforms to a moulded valve in
a way a rigid cone cannot. PETG is the repo default and works; TPU is the
upgrade if a spool is already loaded.

## Sources

The range each assumed number sits in, and where it came from:

- MF100 nozzles mount on a quarter-turn bayonet; makers who callipered the
  stock set quote a 6 mm round jet and a 12 × 3 mm flat jet —
  [Printables](https://www.printables.com/model/1122445-replacement-nozzles-for-wolfbox-air-duster),
  [MakerWorld](https://makerworld.com/en/models/1539673-wolfbox-mf100-replacement-nozzles).
- EXPED's own WingLock inflation adapter is quoted at 28 mm outside / 24 mm
  inside diameter —
  [Thingiverse](https://www.thingiverse.com/thing:7006258).
- DIY pump-sack builds cut a 25–30 mm hole for the valve and catch its groove
  with a lip — [Thingiverse](https://www.thingiverse.com/thing:5330010),
  [winglock-adapters](https://winglock-adapters.pages.dev/).
- A Backpacking Light thread describes ½" poly tubing pressed straight over the
  same valve —
  [Backpacking Light](https://backpackinglight.com/forums/topic/schnozzel-to-winglock-adapter-ideas/).
