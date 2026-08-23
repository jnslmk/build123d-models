# WOLFBOX MF100 ↔ Therm-a-Rest adapters

Two funnels, one for each end of the same air duster. The **inflate** adapter
pushes a socket into the blower's outlet and blows the pad up. The **deflate**
adapter caps the blower's tail and sucks it back down. Above the throat they are
the same part: the same cup, on the same valve, from the same numbers.

```bash
uv run export wolfbox_thermarest_adapter           # the STL that fills a pad
uv run export wolfbox_thermarest_adapter.deflate   # the STL that empties one
uv run check  wolfbox_thermarest_adapter           # both, in one report
uv run view   wolfbox_thermarest_adapter.deflate   # look at it first
```

| | Inflate | Deflate |
| --- | --- | --- |
| Hangs off | the outlet, nozzle twisted off | the intake grille at the tail |
| Machine end | socket **into** a Ø16–27 mm port | cap **over** a Ø34–46 mm barrel |
| Valve end | Ø22–34 mm cup | the same Ø22–34 mm cup |
| Size | 47 mm tall, Ø36 rim, ~7 cm³ | 52 mm tall, Ø51 base, ~12 cm³ |
| Print | under an hour, <10 g | about an hour, ~16 g |

**A fan that blows out of one end is pulling in at the other**, so no vacuum
mode is needed and nothing about the tool changes. The deflate adapter's only
job is to decide where that intake air comes from: cover the grille and every
cubic centimetre the fan draws has to come up through the cup.

## Read this first: no dimension here was measured

Nobody in this repo has held an MF100 or a WingLock valve, and neither
manufacturer publishes a drawing of the interface. Every diameter in
`config.py` is **assumed**, inside a range that is **researched** — the ledger
in that file names which is which, source by source.

That is why every end is a cone rather than a copy. A taper seats wherever it
meets the thing it is put on, so the socket works anywhere between Ø16 and
Ø27 mm, the cap anywhere between Ø34 and Ø46 mm, and the cup anywhere between
Ø22 and Ø34 mm — a wrong guess changes *where* it seats rather than *whether*
it fits. A cloned bayonet or a cloned snap groove would have been
all-or-nothing.

**If you have callipers, use them.** Six numbers per part, all sliders on the
website or keyword arguments to `create()`:

| Symptom | Slider | Which way |
| --- | --- | --- |
| **Inflate** | | |
| Socket bottoms out on the blower before it grips | `blower_mouth_dia` | down |
| Socket wobbles / slides straight on with no wedge | `blower_mouth_dia` | up |
| Socket goes on but the blower feels throttled | `blower_throat_dia` | up |
| Socket pops off under the blower's thrust | `socket_depth` | up |
| **Deflate** | | |
| Cap will not go over the tail at all | `body_mouth_dia` | up |
| Cap rattles on the barrel and whistles | `body_mouth_dia` | down |
| Cap bottoms out on its shoulder before it seals | `body_seat_dia` | down |
| Cap seals but leaves an intake vent uncovered | `cap_depth` | up |
| **Both** | | |
| Cup rests on the valve's rim and rocks | `valve_seat_dia` | down |
| Cup swallows the valve and touches the pad fabric | `valve_seat_dia` | up |
| Cup will not drop over the valve's wings at all | `valve_mouth_dia` | up |
| Cup seats before it seals | `cup_depth` | up |

Re-export after a change; there is nothing to re-model. The cup sliders are
shared, so a cup dialled in on one part is dialled in on the other.

## How to use it

**To fill a pad:**

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

**To empty one:**

1. Push the cap onto the *tail* of the duster, over the grille, until the cone
   wedges. Leave the nozzle end alone — that is now the exhaust, and it will
   blow at whatever is in front of it.
2. Set the pad's valve to deflate, so the one-way flap is held open. This is
   the step that catches people out: with the flap shut, the fan will happily
   pull a hard vacuum on the adapter and move no air at all.
3. Press the cup down over the valve and run the duster. Suction seats both
   joints for you — the pressure difference pulls the cap onto the barrel and
   the cup onto the valve the whole time it is working, which is the opposite
   of what happens on the inflate side.
4. Roll the pad from the far end as it empties, and close the valve before
   lifting the cup off.

Nothing here latches, on purpose, at either end: at the close of a fill the fan
is pushing against a nearly full pad, and an adapter that could not simply be
lifted off would be the wrong tool to be holding.

**Keep the deflate runs short.** Sealing the intake means the motor's cooling
air is now coming through the pad. Emptying a sleeping pad is a half-minute job
and nothing gets warm; leaving the duster running on a sealed cap is not
something this part is designed for.

## Printing

PETG, 0.2 mm layers, no supports, both already in print pose — machine end on
the bed, cup mouth up. Three perimeters everywhere is plenty; the walls are
2.4 mm at the socket and the cap, 2.8 mm at the deflate adapter's neck and
1.2 mm at both cups, so the slicer will fill them with perimeters either way.

Both bores self-support. The only downward-facing internal surface in either
part that is worth naming is the deflate adapter's 45° shoulder, from the cap's
seat down to the throat — 45° is the steepest that prints dry, and `checks.py`
fails on any slider position that would exceed it.

**TPU 95A prints these files better than PETG does.** Both cup walls are thin
because they are the sealing faces, and an elastomer conforms to a moulded valve
in a way a rigid cone cannot. PETG is the repo default and works; TPU is the
upgrade if a spool is already loaded. The deflate adapter's neck is the one
place stiffness is worth anything — a 160 mm baton hanging off a 46 mm cap is a
lever — and 2.8 mm of TPU there is still plenty for a 366 g tool.

## Sources

The range each assumed number sits in, and where it came from:

- MF100 nozzles mount on a quarter-turn bayonet; makers who callipered the
  stock set quote a 6 mm round jet and a 12 × 3 mm flat jet —
  [Printables](https://www.printables.com/model/1122445-replacement-nozzles-for-wolfbox-air-duster),
  [MakerWorld](https://makerworld.com/en/models/1539673-wolfbox-mf100-replacement-nozzles).
- The rear of the tool is a **fixed grille around the metal fan disc**, not a
  port and not a removable filter cap — which is why the deflate adapter caps
  the barrel from outside instead of plugging into anything —
  [Gough's Tech Zone](https://goughlui.com/2026/05/22/quick-review-generic-air-duster-vs-wolfbox-super-power-turbofan-mf100-mf200/).
- The whole tool measures 1.57 × 1.57 × 6.3 in (39.9 × 39.9 × 160 mm), so
  nothing on it — barrel, collar or grille — is wider than 39.9 mm —
  [Amazon](https://www.amazon.com/WOLFBOX-MF100-Duster-150000RPM-Rechargeable-Adjustable/dp/B0DHNG4DL8).
- EXPED's own WingLock inflation adapter is quoted at 28 mm outside / 24 mm
  inside diameter —
  [Thingiverse](https://www.thingiverse.com/thing:7006258).
- DIY pump-sack builds cut a 25–30 mm hole for the valve and catch its groove
  with a lip — [Thingiverse](https://www.thingiverse.com/thing:5330010),
  [winglock-adapters](https://winglock-adapters.pages.dev/).
- A Backpacking Light thread describes ½" poly tubing pressed straight over the
  same valve —
  [Backpacking Light](https://backpackinglight.com/forums/topic/schnozzel-to-winglock-adapter-ideas/).
