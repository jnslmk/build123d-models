---
name: printed-text
description: >-
  Sizes, places and verifies engraved or embossed text on FDM-printed build123d
  parts. Covers the minimum character height, stroke width and engrave depth a
  0.4 mm nozzle can resolve, why build123d's Text(font_size=N) yields digits only
  ~0.75x N tall, when FontStyle.BOLD is the cheapest fix (it rescues a decimal
  point that would otherwise vanish), how the face's orientation changes
  legibility, aligning wall labels to the holes they name, and measuring real
  glyph geometry in code before trusting a font size. Use when adding a label,
  size number or lettering to a model, when picking a font size or style for
  Text(), when engraved text prints illegibly or a decimal point disappears, or
  when choosing between engraving and embossing. Keywords: engrave, emboss,
  label, text, font, glyph, lettering, numbers, FontStyle, Text, font_size. Load
  BEFORE calling `Text(font_size=...)` — the nominal font size is not the glyph
  height, and that gap is not documented anywhere else. TRIGGER: about to add a
  label, size number or engraved/embossed lettering to a model, or a printed
  decimal point or small glyph needs to survive.
---

# Printed text

FDM cannot resolve arbitrarily fine glyphs — a 0.4 mm nozzle lays down 0.4 mm
lines, so a label is designed against the nozzle, not against what looks right on
screen. Everything below is for FDM with a 0.4 mm nozzle and is corroborated
against glyph measurements taken in this repo.

## The budget

| Quantity | Absolute minimum | Preferred |
| --- | --- | --- |
| Character height | 3 mm | 5 mm+ |
| Stroke width | 0.4 mm (one nozzle) | 0.8 mm+ (two perimeters) |
| Engrave depth | 0.5 mm | 0.8 mm (this repo's default) |
| Embossed stroke | 1 mm | — |
| Embossed char height | 4 mm | — |

Engrave into solid walls only, and keep the depth below the wall thickness so it
cannot punch through.

**Font**: bold sans-serif, ALL-CAPS or digits — uniform, simple shapes. build123d
defaults to a system sans-serif, and `FontStyle.BOLD` resolves to its bold face.

## The two traps

**1. `font_size` is not the glyph height.** `Text(font_size=N)` renders a *digit*
only about 0.75x N tall — `font_size=4` gives ~2.97 mm digits, i.e. already under
the 3 mm floor. Size against the measured glyph, never against the nominal.

**2. A regular-weight period is about one nozzle wide and often vanishes**, so
"2.5" prints as "25". This is the failure that silently ruins a set of size
labels, because it looks fine in the viewer.

**The cheapest fix for both is `font_style=FontStyle.BOLD`.** At `font_size=4` it
roughly doubles stroke (~0.6 -> ~1.0 mm) and grows the decimal point from
**0.41 mm to 0.70 mm** — from below one nozzle to comfortably above it. Bold buys
that readability with **no change to size, spacing or alignment**, so it is a free
swap on an already laid-out label.

## Measure, do not guess

Verify in code, not in the viewer. Sample the glyph sketch and read off the real
numbers before committing to a font size:

```python
import fontfix  # noqa: F401  -- silences OCCT's fontconfig warnings on Text
from build123d import BuildSketch, FontStyle, Text

for style in (FontStyle.REGULAR, FontStyle.BOLD):
    for txt in ("2", ".", "2.5"):
        with BuildSketch() as sk:
            Text(txt, font_size=4, font_style=style)
        box = sk.sketch.bounding_box()
        print(f"{style.name:8} {txt!r:6} "
              f"w={box.size.X:.3f} h={box.size.Y:.3f} area={sk.sketch.area:.3f}")
```

Measured on this repo's default system sans at `font_size=4`:

| Text | Weight | Width | Height | Area |
| --- | --- | --- | --- | --- |
| `2` | regular | 1.852 | 2.969 | 2.157 |
| `2` | bold | 2.119 | 2.969 | 3.657 |
| `.` | regular | 0.412 | 0.496 | 0.204 |
| `.` | bold | 0.703 | 0.756 | 0.531 |
| `2.5` | regular | 5.719 | 3.025 | 4.666 |
| `2.5` | bold | 6.490 | 3.025 | 8.142 |

Read it as: `height` is the true character height (2.969 = 0.742x the nominal 4),
the `.` row is the decimal-point survival check, and the `area` growth at
identical height and near-identical width is the stroke getting thicker — bold
adds ink, not size.

The same probe answers layout questions. Measure at a probe size, then scale:
`run = box.size.X / probe` is the word's width per 1 mm of font size, so the
largest font that fits a face of width `W` is `W / run`. Glyph widths vary enough
(a `1` against a `W`) that a characters-times-width rule of thumb either overflows
the face or wastes it. See `_label_fit` in
`models/drill_storage/hex.py`, which uses this to choose between reading up a
cover face and reading across it.

## Orientation is the biggest lever

- **Up-facing horizontal top face** — crispest. Text prints at full layer
  resolution. Prefer this whenever the print pose allows.
- **Vertical wall** — the glyphs cross the layer lines. Often unavoidable (a base
  that prints bores-up has nowhere else to put its labels), so lean on bold plus
  extra depth there.
- **Bottom face** — worst. Avoid.

## Engrave or emboss

Embossed (raised) text generally prints more reliably than engraved, but it needs
the bigger minimums in the table above and cannot be paint-filled.

**Engraved plus a wipe of paint or marker in the recess gives the best contrast
for small labels**, which is why this repo engraves. For a crisper engraved edge,
chamfer the glyph mouths into a continuous V-groove — see `LABEL_CHAMFER` in
`models/drill_storage/box.py`.

## Aligning wall labels to holes

Place each label at its hole's own world-x, so the label tracks the hole through
the view mirror and the same number reads correctly on the front *and* the back
wall.

But labels live on the body's flat wall face, `±(PAD/2 − CORNER_R)`, which is
narrower than the collar the holes spread across. So each label must be clamped
inward off the rounded corners, and the outermost labels will end up sitting
slightly inboard of their holes. A bigger font needs more clamp, which makes edge
alignment worse — there is a real three-way tension between **text size, hole
spread and alignment**, and it has to be resolved deliberately rather than
discovered on the print.

`_engrave_row_legend` in `models/drill_storage/box.py` implements this:
`flat_half = PAD / 2 - CORNER_R`, then a per-label
`limit = flat_half - 0.31 * WALL_LABEL_SIZE * len(text) - 0.3` that the lateral
position is clamped to.

## Material note

**ABS** holds fine detail as well as PLA and PETG. But **do not acetone
vapour-smooth a labelled face** — the smoothing melts small glyphs shut and the
label is gone.

## Worked examples in this repo

| File | What it shows |
| --- | --- |
| `models/drill_storage/box.py` | `_engrave_row_legend` — bold 4 mm wall numbers clamped off the rounded corners and aligned to hole world-x; constants `WALL_LABEL_SIZE`, `WALL_LABEL_DEPTH`, `WALL_LABEL_STYLE`, `WALL_LABEL_MAX_LAT`. Cover label with a chamfered V-groove mouth. |
| `models/drill_storage/hex.py` | `_label_fit` — probe-measures the word to pick the largest font and the better reading direction for a cover face. |
| `models/drill_fit_tester/frame.py` | `engrave` — the minimal sketch-on-a-plane, extrude-subtract engraving helper. |
