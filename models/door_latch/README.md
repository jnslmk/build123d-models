# Door latch

A compact, pivoting L-shaped latch for holding a door or panel closed. It is an
85 mm long, 10 mm wide printed arm with a 3.5 mm through-hole for the pivot
screw and a rounded hook at its free end.

Print it flat on one broad face, in the pose returned by `create()`. Mount it
through the pivot hole, then arrange the mating door or frame so the hook can
swing over its catch.

## Design decisions

- The pivot is inset 5 mm from the arm end, keeping the 3.5 mm hole inside the
  10 mm arm with material around its end and long edges.
- The hook is a short perpendicular stem ending in a half-round cap. This gives
  the latching end a rounded contact profile rather than a sharp corner.
- Vertical corners are filleted; the front and back rims use a boolean chamfer
  tool because direct OCC edge chamfers are unreliable on the latch outline.
  This retains the flat print face.

## Known limitation

The hook transition still has a documented residual sharp-edge patch where the
boolean chamfer meets the tight curved notch. `uv run check door_latch` reports
it explicitly rather than treating the edge treatment as complete.
