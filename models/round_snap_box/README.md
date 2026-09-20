# Round snap box

A round, flush-closing printed box with a snap-on lid. Its default usable
interior is 78 mm in diameter and 20 mm deep; the website parameters can change
the interior size and the joint dimensions together.

`create_box()` and `create_lid()` return the individual printable parts;
`create()` lays both out side by side. Print the body floor-down with its mouth
up. The lid is already flipped into its print pose, mouth up.

## Design decisions

- The body and lid share the same outside radius when closed. The asymmetric
  wall budget reserves a recessed body lip, the radial joint clearance, and the
  lid wall while keeping the exterior flush.
- An external lip bead and matching internal lid bead make a detent: the lid
  flexes over the momentary peak, then drops into a lower-interference seated
  position instead of relying on a friction-only fit.
- The default 0.30 mm bead and 0.25 mm radial clearance keep the repeated-use
  snap strain below the PETG limit while retaining a 0.30 mm radial barrier.
- Lead-in chamfers at both joint mouths guide the lid on; their sizes are capped
  so a printable flat rim remains.
