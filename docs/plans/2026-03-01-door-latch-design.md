# Door Latch Model Design

## Goal
Add a new parametric `build123d` model for a printable pivoting door latch with a rounded L-shaped body that rotates around a screw.

## Confirmed Requirements
- Pivot clearance hole: `3.5 mm` diameter.
- Main arm length to L start: `65 mm`.
- Total length: `78 mm`.
- Hook length: `20 mm`.
- Body thickness: `10 mm`.
- Body width: `20 mm`.
- Shape approach: build from rectangular arms and apply generous fillets (rounded L look).

## Geometry
- Build a single solid as union of two prisms:
  - Main arm prism: `78 x 20 x 10 mm`.
  - Hook prism: `20 x 20 x 10 mm`, attached at the distal end to form an L.
- Add outside fillets on edges to soften the profile and create rounded transitions.
- Subtract a through-hole near the pivot end:
  - Hole diameter: `3.5 mm`.
  - Hole center located on body centerline with `10 mm` inset from pivot-side end.

## Parametric Constants
Expose dimensions as top-level constants in `models/door_latch.py`:
- `LATCH_LENGTH`, `ARM_WIDTH`, `THICKNESS`
- `BEND_START`, `HOOK_LENGTH`
- `PIVOT_HOLE_DIAMETER`, `PIVOT_INSET`
- `OUTER_FILLET_RADIUS`

## API and Integration
- Implement `create() -> Part` in `models/door_latch.py` to match existing model pattern.
- Export/preview continues through existing CLI (`uv run model door_latch`, `uv run render door_latch`) without extra wiring if dynamic model loading is already used.

## Validation Strategy
- Add tests that verify:
  - `create()` returns a valid non-empty part.
  - Bounding box thickness equals `10 mm`.
  - Bounding box dimensions are consistent with latch footprint.
  - Pivot hole subtraction exists at expected location (volume/face sanity check).

## Non-Goals
- No mating strike plate in this task.
- No fastener hardware modeling.
- No kinematic assembly constraints.
