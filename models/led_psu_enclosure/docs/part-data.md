# Component data

Researched July 2026. Everything the model depends on, with where it came from,
so the numbers can be re-checked rather than trusted. Values live in `config.py`.

---

## Mean Well RSP-320-24 — Case No. 207A

Datasheet: [`assets/rsp-320-datasheet.pdf`](assets/rsp-320-datasheet.pdf) (p. 4 is
the mechanical drawing).

| | |
|---|---|
| Outline | **215 × 115 × 30 mm**, 0.9 kg |
| Output | 24 V, 13.4 A, 321.6 W; adjustable 20–26.4 V |
| Input | 88–264 VAC, active PFC |
| Efficiency | **89 %** → **≈ 40 W dissipated** at full load |
| Cooling | **Forced air, built-in DC fan** (speed controlled), fan on the **top cover** |
| Temp | −30…+70 °C; **derates from 50 °C down to 50 % load at 70 °C** |

**Bottom face:** 4 × M4, **max screw penetration L = 3 mm**, pattern
**150 × 50 mm** centred. Cross-checked against the drawing's chain dimensions:
32.5 + 150 + 32.5 = 215 ✓ and 32.5 + 50 + 32.5 = 115 ✓.

**Side faces:** 4 × M4 (both sides), L = 5 mm, 150 mm apart, ≈ 12.5 mm above base.
Unused here — the PSU mounts off its bottom face.

**Terminal block** — 9 positions on one 115 mm end, ~13.5 mm tall:

| Pin | Function | Pin | Function |
|---|---|---|---|
| 1 | AC/L | 4–6 | DC OUT −V |
| 2 | AC/N | 7–9 | DC OUT +V |
| 3 | FG ⏚ | | |

The `+V ADJ` trimmer and the power LED are on this same end face. The model puts
it at **−X** (`PSU_TERMINAL_END`) and the shelf lifts out to reach it.

**Fan:** on the top cover, ≈ 47.45 mm in from the non-terminal end, ~Ø50. This is
the single most layout-relevant fact in this file — it is why the shelf sits
25 mm above the PSU instead of 10, and why the high vent port is at that end.

> ⚠ The 150 × 50 bolt pattern is derived from the drawing's chain dimensions.
> **Verify with calipers** before printing the plate.

---

## LXD-4P 4-way blade-fuse block

From the supplier's dimension drawing (the original image is no longer in cache;
every number it carried is transcribed here).

| | |
|---|---|
| Footprint incl. ears | **86.2 ±0.5 × 53 ±0.5 mm** |
| Height | **41.7 ±0.2 mm** |
| Mounting | **2 × Ø5.2**, **76.5 ±0.5 mm** apart, on the long centre line |
| Body | 65.5 ±0.5 long; terminal field 61.5 ±0.5 |
| Side-view features | 34 ±0.5, 20 ±0.2, 7.2 ±0.2 (stud/terminal heights) |
| Fuses | 4 × standard ATO blade, 2–40 A, 32 V |

The same family runs LXD-4P/5P/6P/10P/12P on a common 53 mm width and 41.7 mm
height; only the length changes. Swapping to a 6-way would need
`FUSE_X` = 115.5 and a re-check of the shelf packing.

---

## Weipu SP1712 — rear-nut mount panel socket

Datasheet: [`assets/weipu-sp17-datasheet.pdf`](assets/weipu-sp17-datasheet.pdf).
The datasheet's own term for this variant is **"Rear-nut mount"** — that is the
"back nut" part.

| | |
|---|---|
| Mates with | SP1710 cable connector (cable OD 6–10 mm) |
| Flange | **Ø25 mm** |
| **Panel cutout** | **Ø17 with a 15.6 mm flat** (D-cut, anti-rotation) |
| Thread | **M17 × 1** |
| **Max panel thickness** | **3 mm** |
| Depth | 19.7 mm behind the panel, 10.7 mm in front |
| 3-pin rating | 10 A, 500 V, contacts Ø1.5 × 3, wire ≤ 2 mm² / 14 AWG |
| Sealing | IP68 when mated |

Two consequences, both encoded in the model:

1. The 3 mm panel limit means each bore gets a **Ø29 counterbore on the inside**
   taking the local wall from 3.5 to 2.85 mm. `checks.py` measures this.
2. The **flat is oriented up**. In a horizontal bore the top is where an arc
   would droop; a chord there gives a ~9.3 mm flat bridge that prints cleanly.

Pitch is 35 mm — Ø25 flanges plus finger room for the SP1710 coupling nut.

Series map for reference: SP1710 = cable connector, SP1711 = in-line coupler,
**SP1712 = rear-nut panel mount**.

---

## Athom / IoTorero Ethernet WLED ESP32 controller

**Dimensions are not published anywhere.** Checked athom.tech (both the "DMX" and
"Addressable + PWM" Ethernet variants), the HA-HQ reseller listing, the AliExpress
listing and Scargill's IoTorero review — none state a board or case size.
**Measured by Jonas:**

| | |
|---|---|
| Enclosed box | **102 × 65 × 22 mm** |
| Mounting | **2 × Ø4**, **110 mm apart**, on the long axis (tabs overhang each end) |
| Footprint incl. tabs | ≈ 118 × 65 mm |

Published specs: ESP32-WROOM-32E, LAN8720A 10/100 Ethernet, 5–24 V in, 16 A max,
**4 × addressable DAT channels**, MAX485 for DMX, 16 A relay, replaceable fuse,
I2S PDM microphone, USB-C. Four DAT channels lines up exactly with four fuses and
four SP1712 outputs.

> Confirm which face the RJ45 and terminal blocks exit before finalising the
> board's rotation on the shelf — it decides which way the wiring has to turn.
> The model currently only reserves the envelope.

---

## M12 cable gland

M12 × 1.5, thread ≈ 9 mm, panel hole **Ø12.5**, clamp range 3–6.5 or 4.5–7.8 mm
depending on variant. Needs a flat pad ≥ Ø20 and a panel ≤ ~6 mm.

> ⚠ **Sizing problem.** H05VV-F 3G1.5 mains flex is ~9.5 mm OD; an M12 gland
> clamps 7.8 mm max. Only 3G0.75 (~6.8 mm) fits. 320 W at 230 V ≈ 1.4 A so
> 0.75 mm² is electrically fine, but **M16 (5–10 mm clamp) is the safer
> mechanical choice**. `GLAND_HOLE_D` is a parameter for exactly this reason.

---

## Reusable CAD

No official STEP exists for the RSP-320. The closest available are a GrabCAD
`power-supply-rsp-320-12` model and a 3DContentCentral "Meanwell SMPS RSP320"
(both behind accounts), plus TraceParts' Mean Well catalogue.

The model therefore uses **hand-rolled mock solids** (`mocks.py`). For a keep-out
and fit check only the bounding envelope, the mounting holes and the mating faces
matter; a hand-rolled mock stays parametric, licence-clean and consistent with the
repo's builder-mode style — the same call as the existing "hand-roll Gridfinity
bases rather than add a dependency" decision.

---

## Sources

- [Mean Well RSP-320 datasheet](https://www.meanwell.com/Upload/PDF/RSP-320/RSP-320-SPEC.pdf)
- [Weipu SP17 series datasheet](https://componentbuddy.com/wp-content/uploads/2023/06/Weipu-SP17-Series.pdf)
- [Weipu SP17 series overview](https://www.weipuconnector.com/products/sp17/)
- [TME SP1712/S3-1N](https://www.tme.com/us/en-us/details/sp1712_s3/weipu-connectors/weipu/sp1712-s3-1n/)
- [Athom Ethernet WLED ESP32 DMX controller](https://www.athom.tech/blank-1/ethernet-wled-esp32-addressable-dmx-led-strip-controller)
- [Athom Ethernet WLED ESP32 Addressable + PWM](https://www.athom.tech/blank-1/ethernet-wled-esp32-address-and-pwm-strip-controller)
- [M12 gland dimensions (SourceASI)](https://www.sourceasi.com/shop/3001215-asi-3001215-m12-waterproof-cable-gland-light-gray-polyamide-pa-6-6-ip68-nema-6-6p-rated-3-5-7mm-clamping-range-m12-x-1-5mm-thread-36901)
- [GrabCAD RSP-320-12 model](https://grabcad.com/library/power-supply-rsp-320-12-1)
