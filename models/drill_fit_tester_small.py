"""Small-bore coupons: does the 2-5 mm print compensation actually hold?

The main sweep settled the round bores at ``RIB_GRIP`` = 0.22 for 4-10 mm and
showed the small bores need far more, because their ribs print short. ``grip_for``
now carries those small-bore values as a measured table (``RIB_GRIP_SMALL``) with
linear interpolation between the entries -- the correction turned out to be
nearly flat from 2 to 3 mm and then to collapse over the next millimetre, so
there is no tidy formula, only the printer's behaviour.

Two points on that table are still not measurements: **2.5 mm** has never been on
a coupon (interpolated, on the flat part of the curve, so low-risk) and **5 mm**
is the endpoint where the ramp meets RIB_GRIP by construction. This coupon
carries the whole span so both get checked against their neighbours.

Unlike ``drill_fit_tester_sweep``, which sweeps a *flat* grip value, these bars
sweep an **offset applied to the production law**: bar ``+0.00`` is the holder
exactly as it would be cut today, and the others shift every bore in the row by
the same amount. So you are testing the compensation curve, not a constant.

For the whole set including the big bores and the hex socket, use
``drill_fit_tester_full`` instead -- this one is the quick small-bore subset.

Reading it: if ``+0.00`` feels right at all six sizes, the table is good and the
holder is ready. If one bar wins uniformly across the row, the whole table sits
that far off -- but so does the 6-10 mm baseline it joins, so check
``drill_fit_tester_full`` before moving anything. If the winning bar *changes
across the row* -- say 2 mm wants ``+0.00`` but 3.5 mm wants ``+0.08`` -- then it
is the shape of the table that is wrong, not its height: edit the offending entry
in ``RIB_GRIP_SMALL`` by the winning offset and leave the rest alone. Every entry
is a measurement, so revise them one at a time rather than fitting a curve.

Bar thickness is ``RIB_ZONE_H``, matching the holder's real rib band. Bits go in
SHANK first. Prints flat, bores-up, no supports.
"""

from build123d import Compound

from models.drill_fit_tester_sweep import create_offset_family, report_offsets

# The span that grip_for() interpolates across. 5 mm is the point where the ramp
# meets RIB_GRIP: it has never actually been on a coupon, so it is included here
# to check the join rather than as a control.
SMALL_DIAMS = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0]

# Offsets applied to grip_for(d). 0.04 is about the finest step that is still
# perceptible by hand, and +-0.08 brackets a plausible error in the ramp.
SMALL_OFFSETS = [-0.08, -0.04, 0.0, 0.04, 0.08]


def create() -> Compound:
    """All offset bars, laid out side by side (each exports as its own STL)."""
    return create_offset_family(
        SMALL_OFFSETS, SMALL_DIAMS, False, "drill_fit_tester_small"
    )


def main() -> None:
    from export import display_and_export

    report_offsets(SMALL_DIAMS, SMALL_OFFSETS)
    display_and_export(create(), "drill_fit_tester_small")


if __name__ == "__main__":
    main()
