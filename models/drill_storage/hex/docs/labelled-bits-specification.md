# Labelled 1×2 BITS specification

## Purpose

Store 36 short, ¼-inch hex-shank driver bits in a labelled 1×2 Gridfinity
variant of the existing two-material BITS holder. The original 1×1 model stays
unchanged. Public entry: [hex README](../README.md).

## Accepted requirements

Accepted by the user with “accepted, implement it” after grouping duplicate
Torx sizes side-by-side.

| ID | Requirement | Consequence |
| --- | --- | --- |
| LB1 | 1×2 Gridfinity footprint, literal four-column, nine-row socket grid | Two 42 mm-pitch feet; 41.5×83.5 mm external envelope |
| LB2 | Same construction as existing BITS, all short bits | Retain ASA base, TPU gripping insert, PETG cover; use the existing 25 mm BITS length, 15 mm insertion depth and fits |
| LB3 | Full family-and-size labels on assigned positions | H = hex, T = Torx, PZ = Pozidriv, PH = Phillips, SL = slotted blade width in mm |
| LB4 | Exact layout below; identical Torx sizes adjacent | No unassigned sockets; 14 Torx positions weighted to common sizes |
| LB5 | Existing 1×1 BITS stays unchanged | New variant lives under `drill_storage.hex.bits_double` |
| LB6 | Cover identification reads across a long side | User requested "Print the cover label on the long side"; engrave BITS on the +X wall, with existing depth and backing |

Rows run from back (+Y) to front (−Y), columns left (−X) to right (+X),
viewed from above:

| Row | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- |
| 1 | H1.5 | H2 | H2.5 | H3 |
| 2 | H4 | H5 | H6 | H8 |
| 3 | T10 | T10 | T15 | T15 |
| 4 | T20 | T20 | T20 | T27 |
| 5 | T25 | T25 | T25 | T40 |
| 6 | T30 | T30 | SL6.5 | SL8 |
| 7 | SL3 | SL4 | SL5 | SL6 |
| 8 | PZ1 | PZ2 | PZ2 | PZ3 |
| 9 | PH1 | PH2 | PH2 | PH3 |

## Evidence boundaries

“Short” is interpreted as the existing BITS model's 25 mm standard driver bits.
The socket fits are inherited, not newly calibrated. Slotted blade thickness and
manufacturer-specific tip envelopes remain purchasing/physical-fit considerations.
No print fit trial has been claimed. The current implementation boundary and
human geometry gate are in [the CAD contract](labelled-bits-cad-contract.md).
