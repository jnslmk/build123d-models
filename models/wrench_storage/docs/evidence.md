# Wrench evidence and dimensional interfaces

## Sources and limits

- Original photograph: `/home/jonas/Downloads/PXL_20261003_131441306.jpg`.
- Raw source ledger: [`exports/wrench_analysis/ledger.json`](../../../exports/wrench_analysis/ledger.json).
- [Traced overlay](../../../exports/wrench_analysis/traced_overlay.png),
  [mask](../../../exports/wrench_analysis/mask.png) and
  [rectified photograph](../../../exports/wrench_analysis/rectified_a4_assumed.png).
- The ledger records actual offline tracefinity `ImageProcessor`,
  `AITracer._trace_mask` and `PolygonScaler` output, using paper homography and
  a local colour-threshold/manual-mask workflow. No remote AI trace was used.
- The user subsequently confirmed the sheet is A4. Use landscape 297×210 mm,
  with 0.1 mm per rectified pixel. Original paper corners are
  `(1119,554), (3722,537), (3764,2380), (1133,2425)` in source-image pixels.
  The raw ledger's `ASSUMED A4 ... requires confirmation` status predates that
  confirmation; the source artifact is retained unchanged.
- The trace follows the real open jaws and handles but includes small shadow
  fringes. Corner choice, raised tool plane and lens distortion are not
  calibrated. A4 confirmation removes the paper-size assumption, not these
  sources of error. No numerical physical-error bound is established.
- Head/handle thicknesses below are the user's maximum measurements, not values
  inferred from the photograph. Their measurement tolerance was not supplied.

## Dimensional ledger

All dimensions are millimetres; ordering is biggest first. `head_width` is a
photo-derived face envelope, not a jaw-opening fit dimension.

| Label | Photo length | Photo head width | Measured head thickness | Measured handle thickness |
| --- | ---: | ---: | ---: | ---: |
| 16/17 | 203.80 | 37.60 | 6.10 | 4.40 |
| 14/15 | 188.41 | 33.34 | 5.80 | 4.15 |
| 12/13 | 172.47 | 29.13 | 5.50 | 3.65 |
| 10/11 | 152.52 | 25.29 | 4.80 | 3.30 |
| 8/9 | 136.87 | 20.53 | 4.30 | 3.20 |
| 6/7 | 123.01 | 15.78 | 3.90 | 2.80 |

The photo dimensions are copied from the ledger's `length_a4_assumed_mm` and
`head_width_a4_assumed_mm`. They are not silently replaced with the slightly
different aligned-contour bounds below. Envelope consumers should use the
larger of the recorded dimension and its aligned bound.

## Normalization of the actual profiles

`profiles.PROFILES` embeds the raw ledger's actual `profile_mm` polygons after
these data-preparation operations; it does not synthesize a spanner outline:

1. Compute the signed polygon area, area centroid and second moments from the
   full boundary using standard shoelace integration. Form the **filled-area**
   covariance matrix, not a covariance of vertices: trace vertex density near
   the jaws must not overweight those regions.
2. Choose the eigenvector `(ux,uy)` of the larger covariance eigenvalue. Choose
   its sign so `uy > 0`, consistently running from the top photographed jaw to
   the bottom one. The tools are nearly vertical in this rectified image; the
   resulting long axes agree with their visible straight handles.
3. Transform every original point `(px,py)` by
   `x = ux*px + uy*py - x0`, `z = uy*px - ux*py - z0`, where `x0` and `z0`
   are the minima of those respective unshifted projections. This is a rigid
   rotation/reflection and translation, **not** a scale or stretch. All tools
   therefore share the same photographed-end datum `x=0`; each full trace's
   lowest transverse point is `z=0`. In the bin, `z` is vertical and the
   directly measured tool thickness lies along the remaining transverse axis.
4. Split the closed boundary at its minimum and maximum longitudinal vertices.
   Apply Ramer–Douglas–Peucker independently to the two chains, with point-to-
   finite-segment tolerance 0.15 mm; join the chains without duplicating either
   endpoint. Round retained coordinates to 0.001 mm and close implicitly.
   Simplification removes small raster stair-steps, not the real jaw openings.
   The error allowance for a preview is 0.151 mm including coordinate rounding;
   it is not a physical accuracy claim. A simplified contour can omit the full
   trace's lowest point, but remains in the same positive-height reference frame.
5. Compute `PROFILE_EXTENTS` and `HANDLE_SPANS` from the **unsimplified**
   aligned polygons before step 4, rounding extents upward and span minima down /
   maxima up to 0.001 mm. Notch floors never depend on simplified vertices.

For reproducibility, with successive vertices `a,b`, let
`cross = ax*by - bx*ay`, `A = sum(cross)/2`.
The raw area expectations are:

```text
E[x]  = sum((ax+bx)*cross)/(6*A)
E[y]  = sum((ay+by)*cross)/(6*A)
E[x²] = sum((ax²+ax*bx+bx²)*cross)/(12*A)
E[y²] = sum((ay²+ay*by+by²)*cross)/(12*A)
E[xy] = sum((2*ax*ay+ax*by+bx*ay+2*bx*by)*cross)/(24*A)
Cxx = E[x²] - E[x]²; Cyy = E[y²] - E[y]²
Cxy = E[xy] - E[x]*E[y]
theta = atan2(2*Cxy, Cxx-Cyy)/2
(ux,uy) = (cos(theta),sin(theta)); negate both if uy < 0
```

These projection parameters were produced by arithmetic/data preparation of
that ledger. The displayed precision is for reproducing the transformation,
not for asserting physical measurement precision.

| Label | Original → retained vertices | ux | uy | x0 | z0 | Full aligned extents, rounded up |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 16/17 | 403 → 243 | 0.003408164 | 0.999994192 | 4.734937 | 15.711296 | 203.771 × 37.611 |
| 14/15 | 369 → 231 | 0.012105129 | 0.999926730 | 20.775433 | 59.791844 | 188.503 × 33.323 |
| 12/13 | 351 → 199 | 0.009447395 | 0.999955372 | 37.028306 | 101.021045 | 172.429 × 29.162 |
| 10/11 | 281 → 177 | 0.007226290 | 0.999973890 | 55.615761 | 138.698474 | 152.457 × 25.335 |
| 8/9 | 253 → 164 | 0.013180017 | 0.999913140 | 71.845455 | 171.058151 | 136.808 × 20.580 |
| 6/7 | 191 → 112 | 0.016050637 | 0.999871180 | 86.419329 | 202.240438 | 123.028 × 15.786 |

## Handle-only support facts

Use common stations `x=50` and `x=85` mm from the common photographed end.
Both lie in all six visibly straight handle regions, away from either head;
longitudinal line intersections at these stations each have two boundary
crossings in the raw aligned polygons. For each **whole 2 mm rack band**
(`49..51` and `84..86`), collect every polygon vertex in the band and every
intersection of a polygon edge with either band limit. Linear edges have no
other interior extrema, so the smallest/largest collected heights bound the
whole source trace there, not merely its centerline.

| Label | 49..51 mm band: min / max z | 84..86 mm band: min / max z |
| --- | --- | --- |
| 16/17 | 11.655 / 27.012 | 11.679 / 27.279 |
| 14/15 | 10.426 / 22.929 | 10.320 / 23.146 |
| 12/13 | 8.552 / 20.124 | 8.459 / 20.521 |
| 10/11 | 7.234 / 18.050 | 7.681 / 17.897 |
| 8/9 | 5.539 / 14.590 | 5.949 / 14.677 |
| 6/7 | 4.490 / 11.433 | 4.728 / 11.352 |

For a tool seated with reference height `seat_z`, its notch floor must be no
higher than `seat_z + band_min_z`. If using the simplified contour to prove
preview clearance, also allow 0.151 mm below that minimum for its known shape
approximation. That allowance is not a mating fit. The slot width is measured
`handle_thickness + SLOT_CLEARANCE`; `SLOT_CLEARANCE` is a **total**, not a
per-side, PETG free-fit allowance. Physical photo uncertainty still requires
an actual fit trial; these source-trace bounds alone cannot certify it.

Facts apply only to the stated common-end orientation and 2 mm bands. A wider
rack or a different station requires re-deriving the facts from the raw ledger;
no interpolation of station minima can establish a safe band bound.

## Footprint arithmetic, not geometry acceptance

The existing Gridfinity pitch is 42 mm and the external pad setback is 0.5 mm
in total. With 1 mm walls, a one-cell transverse body has 39.5 mm clear width:

- Head thickness sum: **30.4 mm**.
- Five shared neighbour gaps of `fits.FREE=0.4` plus 0.4 mm total at the two
  sides gives **32.8 mm** for the six-tool packing envelope, or **34.8 mm**
  including two walls. Do not add two free-fit allowances to each shared gap.
- Five longitudinal cells give `5*42-0.5 = 209.5` mm outer / **207.5 mm** inner.
  The longest envelope is `max(203.80,203.771) + 2*1.0 = 205.8` mm,
  leaving **1.7 mm** beyond the named end allowances.
- Four longitudinal cells give only 165.5 mm inner length. Even the external
  diagonal of the most elongated four-cell bounding box (167.5×41.5 mm) is
  about 172.56 mm, shorter than this wrench. Other four-face-connected-cell
  bounding boxes are shorter diagonally. Thus fewer than five occupied cells
  cannot contain its longitudinal span in this connected whole-cell scheme.

This supports **1×5 as the default minimum planar cell candidate**. It does
not prove corner clearance, rack geometry, printability or physical insertion.
The anchor's layout and physical gates must establish those separately. It
also says nothing about minimum assembled Z: a low tray may need a taller cover.

With consecutive biggest-first groups, a column's required cell count is
`ceil((max(length, aligned_length) + 2*PHOTO_END_ALLOWANCE + 2*WALL + 0.5)/42)`.
Each group fits one transverse cell by the same thickness budget. The candidate
lengths are:

| Wrenches per column | Longitudinal cells per column | Occupied cells |
| ---: | --- | ---: |
| 1 | 5, 5, 5, 4, 4, 4 | 27 |
| 2 | 5, 5, 4 | 14 |
| 3 | 5, 4 | 9 |
| 4 | 5, 4 | 9 |
| 5 | 5, 4 | 9 |
| 6 | 5 | 5 |

Common-end alignment keeps these adjacent unequal-length columns connected.
Their footprint is the union of occupied cells, not the fully populated
rectangular bounding box.

## Explicit exported interfaces

No runtime JSON dependency is needed: both modules are plain Python inputs
suitable for the browser source bundle.

### `config.py`

- `Wrench`: frozen dataclass with `label: str`, `length: float`,
  `head_width: float`, `head_thickness: float`, `handle_thickness: float`.
- `WRENCHES`: tuple of six `Wrench` instances, biggest first, labels above.
- `WALL = 1.0`, `TOOL_GAP = fits.FREE`, `SLOT_CLEARANCE = fits.FREE`.
  The last two are total clearances at the PETG baseline (currently 0.4 mm).
- `PHOTO_END_ALLOWANCE = 1.0`: functional photo-envelope reserve **per end**,
  not a fit class or a measured uncertainty bound.
- `FUTURE_LID_HEADROOM = 3.0`: vertical cover-envelope reserve over the seated
  highest tool; this does not require a tall tray rim or authorize a lid.
- `RACK_THICKNESS = 2.0`: longitudinal band thickness used for support facts.
- `DEFAULT_WRENCHES_PER_COLUMN = 6`.
- `PARAMS`: existing browser numeric-control schema, one
  `wrenches_per_column` control, min 1, max 6, step 1, default 6. The layout
  consumer must enforce integer semantics and use consecutive tuple groups.

### `profiles.py`

- `PROFILES`: dictionary keyed by the exact `Wrench.label` strings, with tuples
  of `(x,z)` float pairs in millimetres, closed implicitly. Extrude the face
  profile through measured head/handle thickness as appropriate for a preview;
  no thickness may be read from the photograph.
- `PROFILE_EXTENTS`: dictionary label → `(longitudinal_extent,height_extent)`
  of the full aligned trace, rounded upward. Use `max` with the spec dimensions
  when budgeting tool envelopes.
- `PROFILE_SIMPLIFICATION = 0.15`: preview contour reduction tolerance.
- `HANDLE_STATIONS = (50.0,85.0)` and `HANDLE_BAND_WIDTH = 2.0`.
- `HANDLE_SPANS`: dictionary label → two `(min_z,max_z)` pairs in station
  order, computed from the full traces over the entire bands. No general span
  helper is exported: these fixed facts make the safe support boundary explicit.
