"""Physical gate for two-print keyed glue joints and Gridfinity stacking."""

from build123d import (
    Align,
    Box,
    BuildPart,
    Compound,
    Face,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    Rotation,
    Shape,
    add,
    section,
)

from ..lib.checks import Report, is_solid_at
from ..lib.edges import as_part
from models.lib.gridfinity import BASE_H, FOOT_C3, HEIGHT_UNIT, PAD, gridfinity_foot
from .box import (
    CAP_H,
    STACK_FIT,
    STACK_LIP_W,
    STACK_SOCKET_DEPTH,
    STACK_JOINT_DEPTH,
    STACK_JOINT_RELIEF,
)


def check_split_lips(
    report: Report,
    split: Compound,
    clean: Part | Compound,
    socket_depth: float = STACK_SOCKET_DEPTH,
) -> None:
    """Reassemble independently and probe the actual lap, not its construction.

    Mutation red proof: monkeypatch box._keyed_stacking_joint to
    ``lambda body, lips, depth: (body, lips)`` before creating a fresh split.
    Lap height, transferred material, key, relief and crush probes must fail.
    Removing only the cylinders/cones must fail retention while location passes.
    """
    clean = as_part(clean)
    report.section("separate stacking lips: print and glue geometry")
    children = split.children
    named = len(children) == 2 and [child.label for child in children] == [
        "lid_body",
        "stacking_lips",
    ]
    report.check(named, "exactly two named prints expose body and complete lip field")
    if not named:
        return
    body, lips = (as_part(child) for child in children)
    body_box, lip_box = body.bounding_box(), lips.bounding_box()
    report.check(
        body.is_valid
        and lips.is_valid
        and len(body.solids()) == 1
        and len(lips.solids()) == 1,
        "body and all receiver walls each form one connected printable solid",
    )
    report.check(
        abs(body_box.min.Z) < 1e-6 and abs(lip_box.min.Z) < 1e-6,
        "both independent STLs rest on z=0",
    )
    report.check(
        lip_box.min.X - body_box.max.X >= 4.9,
        "exploded preview keeps the two print footprints separate",
    )
    report.check(
        abs(lip_box.size.Z - socket_depth - STACK_JOINT_DEPTH) < 1e-6
        and abs(body_box.size.Z + socket_depth - clean.bounding_box().size.Z) < 1e-6,
        "lap is transferred into the roof without changing the stacking height",
    )
    for part, label in ((body, "body"), (lips, "lips")):
        # Measure printable bed adhesion, not the common glued-contact area.
        # Receiver overhangs and Dremel's retained roof fillet mean only part
        # of these planar faces meets the other print after assembly.
        bed_faces = [
            face
            for face in Shape.get_shape_list(as_part(part), "Face")
            if isinstance(face, Face)
            and abs(face.bounding_box().min.Z) < 1e-6
            and abs(face.bounding_box().max.Z) < 1e-6
        ]
        bed_area = sum(face.area for face in bed_faces)
        report.check(
            bed_area > 100,
            f"{label} has substantial planar bed-adhesion faces",
            f"planar bed area={bed_area:.2f} mm²",
        )
    offset_x = lip_box.center().X - clean.bounding_box().center().X
    placed_body = as_part(Pos(0, 0, socket_depth) * body)
    placed_lips = as_part(
        Pos(0, 0, socket_depth + STACK_JOINT_DEPTH)
        * Rotation(180, 0, 0)
        * Pos(-offset_x, 0, 0)
        * lips
    )
    with BuildPart() as assembled:
        add(placed_body)
        add(placed_lips)
    volume_tolerance = 0.01
    # Joint clearance and reservoirs deliberately remove a little material.
    # Everywhere OUTSIDE that shallow layer must match the accepted anchor,
    # including the complete socket, tool-side roof, closure and engraving.
    bounds = clean.bounding_box()
    with BuildPart() as protected:
        add(clean)
        with Locations((bounds.center().X, bounds.center().Y, socket_depth)):
            Box(
                bounds.size.X + 2,
                bounds.size.Y + 2,
                STACK_JOINT_DEPTH + STACK_JOINT_RELIEF + 1e-4,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    missing = (protected.part - assembled.part).volume
    extra = (assembled.part - clean).volume
    report.check(
        missing < volume_tolerance and extra < volume_tolerance,
        "socket, tool-side roof, closure and labels retain the accepted envelope",
        f"protected missing={missing:.6f}, extra={extra:.6f} mm³",
    )
    floor = section(
        clean, section_by=Plane.XY.offset(socket_depth - 1e-5), mode=Mode.PRIVATE
    )
    cells = [
        wire.bounding_box()
        for face in Shape.get_shape_list(floor, "Face")
        for wire in face.inner_wires()
    ]
    cells.sort(key=lambda bounds: (bounds.center().X, bounds.center().Y))
    report.check(bool(cells), "finished anchor exposes real receiver floor contours")
    if not cells:
        return
    # Literal physical probe dimensions intentionally do not use the production
    # fit constants: a misplaced/doubled gap must not move its own test points.
    z = socket_depth + 0.2
    location_ok = retention_ok = relief_ok = seating_ok = lead_ok = True
    for cell in cells:
        x, y = cell.center().X, cell.center().Y
        half, half_y = cell.size.X / 2, cell.size.Y / 2
        probe_y = y - min(10, half_y * 0.55)
        relief_y = y - min(7, cell.size.Y / 5)
        location_ok &= (
            is_solid_at(placed_lips, x + half + 0.6, probe_y, z)
            and not is_solid_at(placed_body, x + half + 0.6, probe_y, z)
            and not is_solid_at(placed_lips, x + half - 0.1, probe_y, z)
            and not is_solid_at(placed_body, x + half - 0.1, probe_y, z)
            and is_solid_at(placed_body, x + half - 0.3, probe_y, z)
        )
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px, py = x + dx * (half - 0.225), y + dy * (half_y - 0.225)
            if dx == 1:
                py -= min(5, cell.size.Y / 6)
            retention_ok &= (
                is_solid_at(placed_lips, px, py, z)
                and is_solid_at(placed_body, px, py, z)
                # Entering tip is clear, so this is not a blunt press wall.
                and not is_solid_at(placed_lips, px, py, socket_depth + 0.39)
            )
        relief_ok &= not is_solid_at(
            placed_body, x + half + 0.6, relief_y, socket_depth + 0.45
        ) and is_solid_at(placed_body, x + half + 0.6, relief_y, socket_depth + 0.55)
        seating_ok &= is_solid_at(
            placed_lips, x + half + 0.6, probe_y, socket_depth + 0.39
        ) and is_solid_at(placed_body, x + half + 0.6, probe_y, socket_depth + 0.41)
        lead_ok &= (
            not is_solid_at(placed_lips, x + half + 0.05, probe_y, socket_depth + 0.39)
            and is_solid_at(placed_lips, x + half + 0.05, probe_y, socket_depth + 0.2)
            and not is_solid_at(
                placed_body, x + half - 0.3, probe_y, socket_depth + 0.02
            )
        )
    key = cells[0]
    key_y = key.center().Y
    key_offset = min(5, key.size.Y / 6)
    report.check(
        location_ok
        and is_solid_at(placed_lips, key.max.X - 0.7, key_y + key_offset, z)
        and not is_solid_at(placed_body, key.max.X - 0.7, key_y + key_offset, z)
        and not is_solid_at(placed_lips, key.max.X - 0.7, key_y - key_offset, z),
        "transferred lap and asymmetric inward key positively locate the lip field",
    )
    report.check(lead_ok, "both mating mouths have real 45-degree entering relief")
    report.check(relief_ok, "vented adhesive reservoirs retain a solid roof beneath")
    report.check(seating_ok, "unrelieved lap lands meet a hard 0.4 mm seating datum")
    overlap = (placed_body & placed_lips).volume
    withdrawing = as_part(Pos(0, 0, -0.1) * placed_lips)
    withdrawal_overlap = (placed_body & withdrawing).volume
    report.check(
        retention_ok
        and 1e-5 < overlap < len(cells) * 0.2
        and withdrawal_overlap > 1e-5,
        "sparse crush pads interfere during seating and withdrawal, not a loose rabbet",
        f"seated={overlap:.6f}, withdrawing={withdrawal_overlap:.6f} mm³; "
        "sacrificial PETG friction retention needs a printed fit trial",
    )
    report.check(
        len(assembled.part.solids()) == 1,
        "hard lap lands join the roof and all receivers at the seating datum",
    )


def check_cover(
    cover: Part | Compound, foot_top: float, tool_tip_z: float, tip_clear: float
) -> Report:
    """Prove the clean finished anchor retains foot fit and tool clearance."""
    cover = as_part(cover)
    r = Report()
    r.section("stackable cover: clean foot interface and roof")
    bb = cover.bounding_box()
    h = bb.size.Z
    r.check(
        abs(bb.min.Z) < 0.02
        and abs(bb.size.X - STACK_LIP_W) < 0.02
        and abs(bb.size.Y - STACK_LIP_W) < 0.02,
        "print pose is on the bed and lip uses the draft's 42 mm footprint",
        f"z={bb.min.Z:.3f}, lip={bb.size.X:.2f} x {bb.size.Y:.2f}; body={PAD:.2f}",
    )
    # Bounding-box width alone would also accept a uniformly widened cover.
    # Probe all four exterior flats just below the 4.4 mm lip in print pose.
    body_z = STACK_SOCKET_DEPTH + CAP_H + 0.2
    axes = ((1, 0), (-1, 0), (0, 1), (0, -1))
    r.check(
        all(
            is_solid_at(cover, dx * (PAD / 2 - 0.05), dy * (PAD / 2 - 0.05), body_z)
            for dx, dy in axes
        )
        and all(
            not is_solid_at(cover, dx * (PAD / 2 + 0.05), dy * (PAD / 2 + 0.05), body_z)
            for dx, dy in axes
        ),
        "cover body below the lip retains the original 41.5 mm width",
        f"body section z={body_z:.2f} in print pose, lip depth={STACK_SOCKET_DEPTH:.2f}",
    )
    stack_pitch = foot_top + h - STACK_SOCKET_DEPTH
    r.check(
        abs((stack_pitch / HEIGHT_UNIT) - round(stack_pitch / HEIGHT_UNIT)) < 0.003
        and abs(STACK_SOCKET_DEPTH - BASE_H) < 0.02,
        "full-foot seating gives a whole-7-mm-unit stack pitch",
        f"top={foot_top + h:.2f}, seat={STACK_SOCKET_DEPTH:.2f}, pitch={stack_pitch:.2f} mm",
    )
    ceiling_z = foot_top + h - STACK_SOCKET_DEPTH - CAP_H
    r.check(
        ceiling_z - tool_tip_z >= tip_clear - 0.02,
        "longest tool clears the solid ceiling below the stacking socket",
        f"tip at {tool_tip_z:.2f}, ceiling at {ceiling_z:.2f}",
    )
    clean = cover
    r.check(
        not is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH - 0.1)
        and is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH + CAP_H / 2)
        and not is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH + CAP_H + 0.1),
        "socket floor is open above a continuous solid cap",
        f"socket floor z={STACK_SOCKET_DEPTH:.2f} in print pose; cap={CAP_H:.2f}",
    )
    # Verify the straight band and the draft's experimental thin mouth wall;
    # nominal containment does not establish printed durability or fit.
    wall_x = (PAD - 2 * FOOT_C3 + STACK_FIT) / 2
    r.check(
        not is_solid_at(clean, wall_x - 0.05, 0, 2.5)
        and is_solid_at(clean, wall_x + 0.05, 0, 2.5),
        "socket straight band locates the foot on a PETG sliding fit",
        f"flat-side wall at x={wall_x:.2f}, gap={STACK_FIT / 2:.2f} mm radial",
    )
    mouth_x = (PAD + STACK_FIT) / 2
    r.check(
        not is_solid_at(clean, mouth_x - 0.05, 0, 0.02)
        and is_solid_at(clean, mouth_x + 0.05, 0, 0.02)
        and not is_solid_at(clean, STACK_LIP_W / 2 + 0.05, 0, 0.02),
        "full-width foot enters the thin experimental lip mouth",
        f"nominal lip wall={(STACK_LIP_W - PAD - STACK_FIT) / 2:.2f} mm per side",
    )
    upright = as_part(Pos(0, 0, h) * Rotation(180, 0, 0) * clean)
    foot = as_part(Pos(0, 0, h - STACK_SOCKET_DEPTH) * gridfinity_foot())
    r.check(
        (upright & foot).volume < 0.01,
        "real Gridfinity foot enters the socket without collision",
        "foot placed on the socket floor, all 1x1 bevels included",
    )
    lower_foot = as_part(Pos(0, 0, h - STACK_SOCKET_DEPTH - 0.3) * gridfinity_foot())
    r.check(
        (upright & lower_foot).volume > 1.0,
        "socket floor actually supports the foot rather than leaving a through-hole",
        "foot driven 0.3 mm into the floor must intersect",
    )
    return r
