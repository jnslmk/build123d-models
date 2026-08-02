"""Modular 24 V addressable COB linear lamp system.

Daisy-chainable 1.5 m lamps built on an aluminium T8 profile with 3D printed
endcaps, an internal ESP32 + power-distribution PCB, and industrial-style
wiring throughout (SP16/SP17 connectors, LAPP ÖLFLEX CLASSIC 110 cable, M12
glands). Native 24 V operation; USB-C PD is an optional standalone input.

The system specification lives in ``README.md`` in this package. Model entry
points are added here as the parts (endcaps, PCB mount, mounting hardware) get
designed -- until then there is deliberately nothing to show or export.

    uv run show led_profiles            # once a create() exists
"""
