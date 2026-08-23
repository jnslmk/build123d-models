# What the original is, and how it was measured

The source is [Printables 591325, *Adjustable Rope Clamp Rope Tensioner
(Parametric)*][src] by Twotone74, CC licensed and published as a Fusion 360
file, a STEP file, and **ten 3MF files for 3 to 12 mm rope**. The ten are what
this reconstruction is built on: the model here was never opened in Fusion, and
the STEP was not downloadable without an account, so everything below was read
off the meshes.

[src]: https://www.printables.com/model/591325-adjustable-rope-clamp-rope-tensioner-parametric

## Method

Each 3MF holds two objects, named `Body.stl` and `Screw.stl` by the slicer
project, at 18k-25k triangles each and watertight. Three passes, in the order
the `stl-reverse-engineering` skill puts them:

1. **Axis.** For each of the three axes, slice the mesh into 24 bands and score
   how circular each band is. Both objects come back with a mean radial spread
   of 0.13-0.20 about **Y** against 0.56-0.63 about X and Z, which is a
   turned part on Y and nothing else.
2. **Profile.** Take every vertex within 3 degrees of one meridian and plot
   radius against height. That is the section a lathe would cut, and on a
   threaded part it is the thread's own profile: crest and root radii come off
   it directly, and the pitch comes off the spacing of the crest plateaus.
3. **Cross-section.** `trimesh.intersections.mesh_plane` at chosen heights, for
   everything the meridian cannot see -- which turned out to be the two features
   that matter most, below.

Doing all ten sizes rather than one is what makes the table below a *ratio*
table rather than a set of numbers, and that is the finding.

## Everything scales, including the thread

Measured on all ten files, as a multiple of the nominal rope diameter `d`:

| Feature | Ratio to `d` | At 6 mm | At 3.1 mm |
| --- | --- | --- | --- |
| Body outside diameter | 3.000 | 18.00 | 9.30 |
| Body height | 2.500 | 15.00 | 7.75 |
| Knob outside diameter | 2.997 | 17.98 | 9.29 |
| Female thread minor diameter | 2.400 | 14.40 | 7.44 |
| Female thread major diameter | 2.600 | 15.60 | 8.06 |
| Male thread major diameter | 2.500 | 15.00 | 7.75 |
| Male thread minor diameter | 2.300 | 13.80 | 7.13 |
| Female thread length | 0.810 | 4.86 | 2.51 |
| Thread pitch | 0.360 | 2.16 | 1.12 |
| Thread tooth, radial | 0.100 | 0.60 | 0.31 |
| Thread clearance, diametral | 0.100 | 0.60 | 0.31 |
| Wall over the thread root | 0.200 | 1.20 | 0.62 |
| Screw length | 2.58 `d` + 0.3 | 15.78 | 8.30 |

The ratios hold to three decimal places across the whole published range, with
one exception that is not an exception: the file named `Rope_Clamp_3mm` measures
9.30 mm across, which is 3.000 x **3.1**, and the model's own description says
the parameter fails below 3.1 mm. So the smallest published clamp is a 3.1 mm
one.

**The thread rows are the finding.** Everything a printer has to resolve --
pitch, tooth height, clearance -- is a fixed fraction of a rope diameter, so the
smallest published clamp asks a 0.4 mm nozzle for a 0.31 mm tooth on a 1.12 mm
pitch. See `../checks.py`, which runs the printable-thread rules over exactly
these numbers and shows them passing at 12 mm and failing at 3.1 mm.

## The thread profile

Read off the meridian at 6 mm rope, where the features are big enough to
measure without argument:

- male crest radius 7.50, male root radius 6.90 -> 0.60 mm tooth
- female crest radius 7.20, female root radius 7.80 -> 0.60 mm tooth
- crest plateau 0.58 mm, root plateau 0.36 mm
- flank rise 0.60 mm over 0.60 mm of height -> **45 degrees**
- crest-to-crest 2.15 mm, root-to-root 2.17 mm -> pitch 2.16
- female thread runs 4.84 mm, or 2.24 turns, or **0.32 x the major diameter**
  -- against the 1.0 x D floor the printable-thread table gives, which is the
  one rule the original misses at *every* size rather than only the small ones
- profile closes: 0.58 + 0.60 + 0.60 + 0.36 = 2.14 against a 2.16 pitch

So it is a symmetric 45 degree trapezoid with flats, and the radial clearance is
0.30 mm at both crest and root -- which is the same number, because on a 45
degree flank a radial shift opens the flanks by the same amount along their
normal. That property is worth keeping and this model keeps it; see
`../thread.py`.

## The two features a meridian cannot see

Sections at 6 mm rope, taken just inside each face:

- **The plunger's face carries concentric ring grooves**, at radii 1.4, 3.5-4.0
  and 5.9-6.4, so roughly 2.4 mm apart -- `0.4 d`. Concentric, which is the only
  thing that can grip on a face that stops at an arbitrary rotation.
- **The channel floor carries straight ribs**, seven of them, running across the
  rope and spaced the same 2.4 mm along it, about 1.0 mm wide and 0.5 mm tall.

The two cross. That pairing is reproduced here for the same reason it exists
there: ribs resist the pull, rings bite wherever the screw stops.

## The mechanism, and where this model leaves it

The window is a stadium 1.9 `d` wide and 0.79 `d` tall in a wall whose bore is
2.4 `d`, and the channel floor sits 0.38 `d` below the window's sill. So a rope
threaded through lies across a gap, and the plunger pushes it down over two
sills. That is the design, and it is a good one.

What it cannot do is let the rope *past* the plunger. The plunger is a disc of
2.30 `d` in a bore of 2.40 `d`: a 0.05 `d` annular gap, 0.3 mm at 6 mm rope and
0.05 mm at 1 mm wire. Nothing goes through it at any size, so the rope is nipped
between the plunger's rim and the sill rather than clamped against the floor,
and the ribbed floor and the ringed face never touch each other or the rope
except in the middle of the span.

On 6 mm rope that is fine -- rope is compressible and has plenty of surface to
hold by. On 1 mm wire it is not, which is why the channel here is a slot rather
than a bore. `../config.py`'s `Clamp.wire_pass` carries that argument, and
`../checks.py` asserts both halves of it: a passage wider than the wire along
the wire's axis, and a gap narrower than the wire across it.
