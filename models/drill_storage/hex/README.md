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
uv run export drill_storage.hex.bits.cover_stackable  # PETG stacking alternative
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

**Cover**: 24 mm (42 mm / 6U assembled). The base is 30 mm — the family's
36 mm is for drills that need the depth. Bits sink 15 mm below the rim
(`BITS_HOLE_DEPTH`), resting on the guide floor at z = 15, and stand 10 mm
proud, which is how you pinch them out. The ALLEN box sinks its keys deeper
(21 mm) on the same base; `config.guide_floor_z` is the one place that says
which box gets which.

**Stackable cover: 28.4 mm** (46.4 mm = 6U + 4.4 mm assembled).
The same eased snap bead fits the existing BITS collar, with a full-depth
socket seating the entire 4.4 mm of another unchanged 1×1 Gridfinity foot
for a 6U stack pitch. A built-in breakaway lattice supports its ceiling
during top-down printing; remove the lattice and nibs before stacking.
The experimental 42 mm lip mouth (~0.14 mm nominal wall, zero nominal
gap to neighbouring cells) needs a physical print and fit trial. The
original 24 mm smooth cover remains support-free. See the
[stackable-cover specification](../docs/stackable-cover-specification.md).

**Cover snap**: eased for this box alone — `BITS_SNAP_PROTRUSION` (0.35 mm)
against the family's 0.45, so the bead engages 0.15 mm rather than 0.25 once the
collar's slip gap is spent, and comes off with roughly 40% less force. A 24 mm
cover has no lip and nothing to grip but the mouth itself, and a pinch there
presses the bead *onto* the collar; the taller covers in the family are gripped
well above the snap and keep the family's bead. Only the cover changed — the
collar groove is the family's, so an eased cover goes onto a base already
printed and an already-printed cover still fits a new base. The argument, the
strain bound and the detent floor it must not cross are in
[`config.py`](config.py)'s *The cover's snap*.

**Grip**: both cartridges' lands are cut `HEX_LAND_TIGHTEN` (0.10 mm across the
flats) tighter than the family's, because a socket here is named by `HEX_AF` —
which already carries the guide's slip clearance — rather than by the shank the
family measures from. The argument is in [`config.py`](config.py)'s *The grip*.

The sibling set, `drill_storage.allen`, is the 8-piece 50 mm hex-key box —
same geometry, the family's clearances kept outright — see
[`../allen/README.md`](../allen/README.md). The clearances, the fit classes and
the argument behind the two-material split are the drill family's — see [the
family README](../README.md) and [`docs/design-notes.md`](../docs/design-notes.md).

## Labelled 1×2 BITS variant

The accepted extension stores **36 short ¼-inch hex-shank driver bits in a
literal 4×9 grid**, with full H / T / PZ / PH / SL socket labels and duplicate
Torx sizes side-by-side. It keeps the existing ASA / TPU / PETG construction
and leaves the original 1×1 BITS box unchanged. The
[labelled-bits specification](docs/labelled-bits-specification.md) records the
exact accepted layout.

The accepted rigid base is `drill_storage.hex.bits_double.base`: a
41.5×83.5 mm, 30 mm-tall ASA base with two Gridfinity feet. Its long walls carry
the nearest two socket columns each; labels read vertically, with each row's
left-to-right pair ordered toward −Y. Rows run back (+Y) to front (−Y).
Engravings are 0.8 mm deep, bold, and suitable for a contrasting paint fill.
Print feet-down, cavity-up, in an enclosure.

```bash
uv run view drill_storage.hex.bits_double.base
uv run export drill_storage.hex.bits_double.base
uv run check drill_storage.hex.bits_double.base
uv run view drill_storage.hex.bits_double.insert
uv run export drill_storage.hex.bits_double.insert
uv run check drill_storage.hex.bits_double.insert
```

The accepted **TPU cartridge**, `drill_storage.hex.bits_double.insert`, uses the
identical 36 coordinates, the existing BITS grip lands, and the keyed outward
retention bead. Print it flat-bottom down with sockets up in black TPU; it seats
on the base's cavity floor at z=23.2 mm.

The matching **PETG cover** is the current reviewable anchor,
`drill_storage.hex.bits_double.cover`: a 24 mm cover with the existing eased BITS
snap and engraved "BITS" identification on the long +X side, extended to
41.5 × 83.5 mm. Print it pillow-top down, open mouth up, in translucent PETG.
It seats at z=18 mm for a
42 mm / 6U assembled holder and leaves 1 mm above the 25 mm bits.

```bash
uv run view drill_storage.hex.bits_double.cover
uv run export drill_storage.hex.bits_double.cover
uv run check drill_storage.hex.bits_double.cover
```

The assembled scene waits for cover acceptance under the
[current CAD contract](docs/labelled-bits-cad-contract.md).
