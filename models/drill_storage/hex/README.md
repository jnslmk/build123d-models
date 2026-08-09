# drill_storage.hex

Gridfinity storage for a **16-piece 1/4" hex-shank driver-bit set** (Torx /
Phillips / Pozidriv / slotted, all 25 mm), and one of the five top-level
drill_storage sets. Two-material, like the others: a rigid black ASA base
guides each bit upright and holds the cartridge, the black TPU insert grips it
on a short land, and the translucent PETG cover snaps over the collar.

```bash
uv run show drill_storage.hex                # the BITS box, all 16 bits standing
uv run export drill_storage.hex.bits.base    # 1x1, foot down, cavity up
uv run export drill_storage.hex.bits.insert  # TPU, flat down, bores up
uv run export drill_storage.hex.bits.cover   # translucent, pillow top down
uv run check drill_storage.hex
```

| part | model | material | print pose |
| --- | --- | --- | --- |
| BITS base | `drill_storage.hex.bits.base` | ASA, black | foot down, cavity up |
| BITS insert | `drill_storage.hex.bits.insert` | TPU, black | flat bottom down, bores up |
| BITS cover | `drill_storage.hex.bits.cover` | PETG, translucent | pillow top down, mouth up |

**BITS** — 1x1 Gridfinity (41.5 mm, pad, body and cover alike), sixteen sockets in a
**literal 4x4 grid**, no legend: the driver bits are a mixed bag with no single
size scale to engrave, so you read the tips themselves. Sixteen sockets cannot
meet the cartridge's clearances on the family's numbers (the mouth lead-ins
alone need an 8.88 mm pitch where the wall allows 8.27 mm), so BITS **shaves**
three clearances — the two mouth chamfers and the guide fit — and the margins
that result are pinned by `checks.py`. The full argument and every shaved
number are in [`config.py`](config.py).

**Cover**: 31 mm (49 mm / 7U assembled). The base is 30 mm — the family's
36 mm is for drills that need the depth. Bits rest on the guide floor at z = 15
and stand 10 mm proud of the rim, which is how you pinch them out.

The sibling set, `drill_storage.allen`, is the 8-piece 50 mm hex-key box —
same geometry, the family's clearances kept outright — see
[`../allen/README.md`](../allen/README.md). The clearances, the fit classes and
the argument behind the two-material split are the drill family's — see [the
family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).
