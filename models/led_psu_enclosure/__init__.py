"""Weatherproof enclosure for a 24 V addressable-LED driver stack.

Houses a Mean Well RSP-320-24 PSU, an Athom/IoTorero Ethernet WLED ESP32
controller, an LXD-4P 4-way blade-fuse block, four Weipu SP1712 rear-nut 3-pin
output connectors, an M12 mains gland and an IP68 RJ45 bulkhead.

Both end walls carry a sliding-shutter vent: a louvred panel with a slider you
push shut or let open with a thumb, so the airflow is adjusted in service instead
of being chosen at print time. Above about half load that is not enough on its
own -- convection through the ports is worth under 2 W of the PSU's 40 -- so the
high port can also carry a 40 mm 24 V fan on a printed yoke, mounted *behind* the
louvre so forced ventilation costs nothing in weatherproofing. See ``README.md``
and ``docs/`` for the design rationale and the researched component dimensions.

    uv run show led_psu_enclosure           # assembled, contents visible
    uv run show led_psu_enclosure.tray      # a single part
"""

from .assembly import create, create_mocks_only, create_print_layout

__all__ = ["create", "create_print_layout", "create_mocks_only"]
