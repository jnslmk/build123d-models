# Drill Fit Tester

Coupons that settle how a `drill_storage` bore should grip a bit, without
printing a holder to find out.

A holder is an eight-hour print. A coupon is a flat strip carrying every size in
the set, at the real bore geometry and the real engagement depth, and it comes
off the bed in twenty minutes. You drop the actual bits in and feel the fit.

```bash
uv run show drill_fit_tester          # ribbed: the holder's real geometry
uv run show drill_fit_tester.plain    # nominal holes, no ribs
uv run show drill_fit_tester.taper    # slightly tapered, self-centring
uv run show drill_fit_tester.sweep    # 5 flat grip values, all sizes on each
uv run show drill_fit_tester.small    # the 2-5 mm compensation table
uv run show drill_fit_tester.full     # the whole wood set, 5 offsets
uv run show drill_fit_tester.land     # TPU: the flex cartridge's grip land, 5 offsets
```

## Two families, two questions

**Single-value coupons — "which way of cutting a hole works?"** One strip per
strategy, all sharing the frame in `frame.py`, all carrying the same sizes so
they are directly comparable.

| module | holes |
|---|---|
| `ribbed.py` | Three compliant ribs at the production interference — what the holder actually cuts. |
| `plain.py` | Plain cylinders, undersized a fixed *percentage* of the bit (a fixed mm leaves small holes tight and big ones loose). |
| `taper.py` | Slightly tapered: clearance at the top, undersize at the bottom, so a bit wedges where the taper matches its true diameter. |

**Sweep coupons — "which *number* is right?"** Several bars on one plate, each
cut at a different interference, so a winner is picked by hand rather than
argued about.

| module | sweeps |
|---|---|
| `sweep.py` | A flat grip value: five bars at 0.14 → 0.46 mm, five representative sizes on each. |
| `small.py` | An *offset applied to the production law*, across 2-5 mm — the span where the compensation table lives. |
| `full.py` | The same offsets, but every hole the wood holder carries, hex socket included. |
| `land.py` | **Print in TPU.** The short grip land `drill_storage.flex` holds a drill on, at five offsets. The only thing that settles `flex.config.LAND_FIT`, which currently ships uncalibrated. |

The distinction matters. Once `grip_for()` stopped being a constant, a flat
sweep could no longer answer "is the law right?" — only a shifted law can. Bar
`+0.00` is the holder exactly as it would be cut today.

## Reading a sweep

Each bar engraves its own grip (or offset) on the back and the sizes on the
front, and exports as its own STL, so you can print one, a few, or all — and run
the same file in PETG and again in TPU to compare materials.

- **One bar wins at every size** → the whole law sits that far off. Shift it.
- **The winner changes across the row** → the *shape* of the law is wrong, not
  its height. Edit the offending entry in `box.RIB_GRIP_SMALL` by the winning
  offset and leave the rest alone. Every entry is a measurement; revise them one
  at a time rather than fitting a curve.

`report()` prints the key — the grip each bar will cut at each size:

```bash
uv run python -c "from models.drill_fit_tester import full; full.report()"
```

## Printing

Flat, bores-up, no supports. Bars are `RIB_ZONE_H` thick — exactly the holder's
rib band — so a bar reproduces the real engagement length rather than a fraction
of it, and the feel transfers directly. Bits go in shank first, the same way they
sit in the holder.
