# Modular 24 V Addressable COB Lamp System

Daisy-chainable linear lamps built on 1.5 m aluminium T8 profile, driven by a
24 V addressable COB strip, each lamp containing an ESP32 Mini + power
distribution on an internal PCB. Industrial-style field wiring: standardized
cable, standardized connectors, no custom cabling.

This document is the system specification. CAD models for the printed parts
(endcaps, PCB mount, mounting hardware) land in this package as they are
designed.

## Goals

- Modular daisy-chainable linear lamps
- Native 24 V operation
- Optional USB-C PD standalone power
- WLED compatible
- Robust industrial-style wiring
- Easy field assembly and repair

## Lamp

### Mechanical

- 1.5 m aluminium T8 profile
- COB diffuser
- 3D printed endcaps
- Internal PCB for ESP32 + power distribution
- Input and output pigtails

### LED Strip

Current target:

- 24 V COB
- WS2811 Dual IC
- 960 LED/m RGBCCT
- 24 V constant-voltage architecture

Future compatible with newer 24 V pixel COB strips.

## Internal Wiring

Inside every lamp:

```
Incoming cable
        │
────────┴──────── 1.5 mm² +24V bus
────────┬──────── 1.5 mm² GND bus
        │
        └── short branch to LED strip
```

Power is passed through every lamp. The strip is only connected as a local
branch.

Advantages:

- minimal voltage drop
- easy servicing
- little current through strip solder joints

## Daisy Chaining

- 4–6 lamps without power injection
- Up to 8 lamps with midpoint injection

Data always continues through all lamps.

## Cabling

External cable: **LAPP ÖLFLEX CLASSIC 110 BK**

- 3×1.5 mm²
- Black
- 6.7 mm OD

Chosen because: industrial quality, low voltage drop, easy sourcing,
inexpensive (~€1.60/m).

## Connectors

Current choice: **SP16 or SP17, 3 pin**

- inline connectors on lamp pigtails
- panel connectors on controller

Chosen because: significantly higher current than BTF connectors, supports
larger cable, industrial quality, affordable.

## Pigtails

Each lamp:

```
SP16
 │
100–150 mm cable
 │
Cable gland
 │
Internal bus
```

Benefits: easier installation, less stress on enclosure, easy replacement.

## Cable Glands

Current choice: **M12, 3–7 mm range** — suitable for the 6.7 mm LAPP cable.
Provides IP sealing and strain relief.

## Controller

Ethernet ESP32 controller, current target:

- 4 outputs
- Ethernet
- WLED

Each output gets its own connector and its own fuse.

## Fusing

Recommended: **Mini ATM automotive blade fuses**.

Architecture:

```
Main fuse
   ↓
Power bus
   ↓
Output fuse
   ↓
Connector
```

One fuse per output.

## USB-C Power

The controller includes:

```
USB-C panel connector
   ↓
PD trigger
   ↓
20→24 V boost
   ↓
24 V bus
```

Allows powering: standalone lamp, controller, demonstration setups.

### USB-C Hardware

Preferred architecture (both modules replaceable):

```
USB-C panel extension
   ↓
PD trigger module
   ↓
Boost converter
   ↓
24 V rail
```

Boost converter current recommendation: **XL6019** — inexpensive, sufficient
for ~30 W lamp, proven, readily available. A future PCB revision may integrate
a newer synchronous converter.

## Power Topology

- Native voltage: **24 V**
- USB-C is only an optional input
- All lamps are fundamentally 24 V devices

## Internal Electronics

Each lamp contains:

- ESP32 Mini
- power distribution
- LED output
- optional USB-C power hardware

Only external connections required: **24 V, GND, DATA**.

## System Philosophy

- Modular
- Repairable
- Industrial components
- Consumer-friendly assembly
- Minimal custom cabling
- Standardized connectors
- Standardized cable
- Expandable without redesign

## Status

- [ ] System specification (this document)
- [ ] Endcap design (profile interface, PCB mount, pigtail gland)
- [ ] PCB (ESP32 Mini + power distribution + LED output)
- [ ] Mounting hardware
- [ ] Controller panel layout (4× SP16/17, fuse holders, USB-C, Ethernet)

Parts are added to `models/led_profiles/` and registered in this package's
`__init__.py` as they are designed:

```bash
uv run show led_profiles                # once a create() exists
uv run export led_profiles              # STL + STEP
```
