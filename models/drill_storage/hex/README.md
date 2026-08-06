# drill_storage.hex

Gridfinity storage for a **1/4" hex-shank bit set**: eight 50 mm hex keys
(1.5 – 8 mm) and sixteen 25 mm driver bits (Torx / Phillips / Pozidriv /
slotted). All twenty-four bits share the same 6.35 mm (1/4") hex shank, so
every socket is the same drop-in hex pocket.

Two-material, like the drill sets: a rigid black ASA base guides each bit
upright and holds the cartridge, the black TPU insert grips it on a short land,
and the translucent PETG cover snaps over the collar.

```bash
uv run show drill_storage.hex                # both boxes, all 24 tools standing
uv run export drill_storage.hex.allen_base   # rigid, foot down, cavity up
uv run export drill_storage.hex.allen_insert # TPU, flat down, bores up
uv run export drill_storage.hex.allen_cover  # translucent, pillow top down
uv run export drill_storage.hex.bits_base    # 1x1, foot down, cavity up
uv run export drill_storage.hex.bits_insert  # TPU, flat down, bores up
uv run export drill_storage.hex.bits_cover   # translucent, pillow top down
uv run check drill_storage.hex
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| ALLEN base | `drill_storage.hex.allen_base` | ASA, black | foot down, cavity up |
| ALLEN insert | `drill_storage.hex.allen_insert` | TPU, black | flat bottom down, bores up |
| ALLEN cover | `drill_storage.hex.allen_cover` | PETG, translucent | pillow top down, mouth up |
| BITS base | `drill_storage.hex.bits_base` | ASA, black | foot down, cavity up |
| BITS insert | `drill_storage.hex.bits_insert` | TPU, black | flat bottom down, bores up |
| BITS cover | `drill_storage.hex.bits_cover` | PETG, translucent | pillow top down, mouth up |

**ALLEN** — 1x1 Gridfinity (41.5 mm, pad, body and cover alike), eight sockets, the sizes engraved on the
body walls largest → smallest, so the set reads as an ordered grid.

**BITS** — 1x1 Gridfinity (41.5 mm, pad, body and cover alike), sixteen sockets in a
**literal 4x4 grid**, no legend: the driver bits are a mixed bag with no single
size scale to engrave, so you read the tips themselves. Sixteen sockets cannot
meet the cartridge's clearances on the family's numbers (the mouth lead-ins
alone need an 8.88 mm pitch where the wall allows 8.27 mm), so BITS **shaves**
three clearances — the two mouth chamfers and the guide fit — and the margins
that result are pinned by `checks.py`. The full argument and every shaved
number are in [`config.py`](config.py).

**Covers**: ALLEN 52 mm (70 mm / 10U assembled), BITS 31 mm (49 mm / 7U). Bases
are 30 mm — the family's 36 mm is for drills that need the depth. Bits rest on
the guide floor at z = 15 and stand 35 mm (ALLEN) / 10 mm (BITS) proud of the
rim, which is how you pinch them out.

The clearances, the fit classes and the argument behind the two-material split
are the drill family's — see [the family README](../README.md) and
[`docs/design-notes.md`](../docs/design-notes.md). The hex package only re-derives
the heights and the BITS box's shaved clearances, in [`config.py`](config.py).
