# WEIPU SP16 / SP17 connector designation and dimensions

**Accessed:** 2026-09-15  
**Scope:** identify the connector family used by the soldering aid, establish manufacturer designations, and record dimensions that are safe to use in CAD.

## Bottom line for CAD

- **Use `WEIPU SP17`, specifically the `SP1712` rear-nut panel socket, for the documented panel connector.** Its manufacturer drawing specifies a **M17 × 1** rear mounting thread and a keyed/D-shaped panel cutout: **Ø17 mm with 15.6 mm across the flat**. The drawing limits panel thickness to **3 mm max**. [WEIPU SP1712 2D drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1712-2D-scaled.png)
- The corresponding cable connector is **SP1710**; WEIPU lists it as mating with SP1712. [WEIPU SP17 product page](https://www.weipuconnector.com/products/sp17/)
- **Do not label the left-hand part “WEIPU SP16.”** Current WEIPU primary material found for the SP family lists SP11, SP13, SP17, SP21, SP25 and SP29; no official SP16 or 1P16 designation was found. A supplier’s generic “SP16-compatible” connector may use a different thread and must be dimension-checked from that seller’s drawing or the physical part before printing.
- The soldering aid’s existing generic `M16 × 1.5` assumption is therefore **not a verified WEIPU specification**. Keep it explicitly provisional, or change the part to the actual supplier/model once identified.

## Manufacturer facts: SP17

### Designation and variants

WEIPU’s official SP17 page calls the family **“SP17 Series”** and lists the connector types **SP1710, SP1711C, SP1712 and SP1715**. It describes the family as IP68, threaded coupling, with solder, crimp, screw and horizontal-mount-screw termination options. [WEIPU SP17 product page](https://www.weipuconnector.com/products/sp17/)

The same page links the 2D drawings for the variants:

- [SP1710 2D drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1710-2D.png): cable connector; drawing shows **Ø24.6 mm** front diameter and **56.5 mm** overall length; cable OD ranges shown are **I: 5–8 mm, II: 6–10 mm**.
- [SP1711C 2D drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1711C-2D.png): in-line connector; drawing shows **Ø25 mm** front diameter and **55 mm** overall length; cable OD ranges shown are **I: 5–8 mm, II: 6–10 mm**.
- [SP1712 2D drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1712-2D-scaled.png): **rear-nut mount panel socket**, mates with SP1710.
- [SP1715 2D drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1715-2D.png): newer front-nut mount socket; this is a different mounting arrangement from SP1712 and must not be substituted without checking the drawing.

WEIPU’s official FAQ independently states that SP17 requires the smaller **17 mm panel cutout** when contrasting it with SP21’s 21 mm cutout. [WEIPU FAQ, “What is the difference between SP17 and SP21 connectors?”](https://www.weipuconnector.com/faq/)

### SP1712 thread and panel geometry

The official SP1712 drawing contains these dimensional callouts:

| Feature | Manufacturer-documented value | CAD interpretation |
|---|---:|---|
| Rear mounting thread | **M17 × 1** | Model the socket’s rear threaded neck as metric M17 coarse/fine pitch 1 mm, not as M16 or M18. |
| Panel cutout | **Ø17 mm** | Start from a 17 mm circular bore. |
| Anti-rotation flat | **15.6 mm across the flat** | Trim one side of the Ø17 bore to make the shown D/keyed profile; orient the flat according to the intended connector orientation. |
| Maximum panel thickness | **3 mm max** | A wall thicker than 3 mm is outside the drawing’s stated mount condition; use a counterbore or locally thin the wall if needed. |
| Front flange diameter | **Ø25 mm** | Reserve the flange envelope on the panel face. |
| Drawing depth callouts | **10.7 mm** and **19.4 mm** | Use the drawing’s reference surfaces when checking rear clearance; do not treat the 19.4 mm callout as the thread length. |

Primary sources for every row above:

1. [Official SP1712 2D drawing](https://www.weipuconnector.com/wp-content/uploads/2023/11/SP1712-2D-scaled.png), which visibly labels `M17×1`, `Ø17`, `15.6`, `3 max`, `Ø25`, `10.7` and `19.4`.
2. [WEIPU rear-nut socket assembly instruction PDF](https://www.weipuconnector.com/wp-content/uploads/2023/07/SP-SY-Rear-nut-Socket-Solder-Assembing-Instruction.pdf), page 1. Its panel-cutout table gives SP17 **A = 15.6 mm** and **B = 17 mm**; page 2 gives the SP17/SY17 rear-nut tightening torque as **0.9–1.0 N·m**.

The assembly instruction is useful because it confirms that 15.6 mm is the flat-to-flat panel dimension, not an approximate outside diameter. The drawing and instruction agree on the D-shaped/keyed cutout.

### SP17 family material and general specification

WEIPU’s official SP17 specification graphic lists: threaded coupling; shell material PC/Nylon66, V-0 fire resistance; PPS insert (maximum 260 °C); copper-alloy/brass contacts; solder, crimp, screw and H-screw termination; cable OD ranges I: 5–8 mm and II: 6–10 mm; IP68; 500 mating cycles; −40 to +85 °C temperature range; and 2000 MΩ insulation resistance. [WEIPU SP17 specification graphic](https://www.weipuconnector.com/wp-content/uploads/2023/11/WEIPU-SP17-spec.png)

These electrical/material values are not required to cut the soldering-aid threads, but they identify the part family and distinguish it from metal SF16 push-pull connectors.

## SP16 / 1P16 designation investigation

### What the official material does say

- WEIPU’s official SP17 page identifies SP17 and its SP1710/SP1711C/SP1712/SP1715 variants. [SP17 page](https://www.weipuconnector.com/products/sp17/)
- WEIPU’s official FAQ describes the SP family as size variants and explicitly compares **SP17 (17 mm cutout)** with **SP21 (21 mm cutout)**. [FAQ](https://www.weipuconnector.com/faq/)
- WEIPU’s current catalog-library filter includes **SP11, SP13, SP17, SP21, SP25 and SP29** among the SP-family documents, while it separately includes **SF16** and **SA16**. It does not list SP16 or 1P16. [WEIPU catalog library](https://www.weipuconnector.com/support_center_catolog/catalog-library/)

### What remains unresolved

No WEIPU primary product page, official drawing, official catalog entry, or official assembly instruction located in this research uses **SP16** or **1P16** as a WEIPU designation. Search results using those names lead to generic/third-party “SP16” or “M16” aviation connectors and to unrelated SF16/SA16 families. Those products cannot be assumed to share WEIPU SP17’s M17 × 1 thread, D-flat, or dimensions.

The terms may be:

- a seller’s generic **SP16-compatible** label;
- shorthand for another manufacturer’s 16 mm connector family; or
- a mistaken transcription of **SP17**.

A third-party SP17 datasheet mirror is retained in this repository at [`models/led_psu_enclosure/docs/assets/weipu-sp17-datasheet.pdf`](../models/led_psu_enclosure/docs/assets/weipu-sp17-datasheet.pdf). Its drawing reproduces the same SP1712 callouts (`M17×1`, `Ø17`, `15.6`, `3 max`) and identifies the document hosts as In2Connect/MBS/ComponentBuddy; it is corroboration only, not the primary source.

## CAD recommendation

For the right-hand documented WEIPU connector:

```text
family:          WEIPU SP17
panel socket:    SP1712 rear-nut mount
mating cable:    SP1710
rear thread:     M17 × 1
panel cutout:    Ø17 mm D-cut, 15.6 mm across flat
panel thickness: ≤3 mm at the socket
```

For the left-hand connector currently called “SP16”:

```text
family:          unresolved generic/supplier part
thread:          do not call it a WEIPU specification
current model:   M16 × 1.5 is provisional only
required before printing: seller drawing or physical measurement of the exact part
```

Do not silently substitute the generic M16 × 1.5 assumption for a WEIPU SP17 part: the verified WEIPU panel socket is M17 × 1, and its anti-rotation D-cut is part of the fit.

## Sources

All URLs above were accessed 2026-09-15. Primary/manufacturer sources are the WEIPU product page, WEIPU FAQ, WEIPU-hosted 2D drawings, WEIPU-hosted specification graphic, and WEIPU-hosted assembly instruction PDF. The repository PDF is listed only as a secondary corroboration and is not used to override the official dimensions.
