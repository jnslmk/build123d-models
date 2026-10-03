"""Physical gate for the removable support and 1×1 Gridfinity stacking interface."""

from build123d import (
    Align,
    Box,
    BuildPart,
    Compound,
    Face,
    Mode,
    Part,
    Pos,
    Rotation,
    Shape,
    add,
)

from ..lib.checks import Report, is_solid_at
from ..lib.edges import as_part
from models.lib.gridfinity import BASE_H, FOOT_C3, HEIGHT_UNIT, PAD, gridfinity_foot
from .box import (
    CAP_H,
    STACK_FIT,
    STACK_LIP_W,
    STACK_SOCKET_DEPTH,
)


def check_split_lips(
    report: Report,
    split: Compound,
    clean: Part | Compound,
    socket_depth: float = STACK_SOCKET_DEPTH,
) -> None:
    """Compare assembled prints with the complete finished lid, not constants.

    Reassembly is independent of the splitter: undo only the measured preview
    X translation, turn the lips socket-down, and lift both to the floor datum.
    Equivalence includes socket walls/floors, closure, labels and no supports.
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
        abs(lip_box.size.Z - socket_depth) < 1e-6
        and abs(body_box.size.Z + socket_depth - clean.bounding_box().size.Z) < 1e-6,
        "split is at socket floor: entire receiver above, complete roof below",
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
        Pos(0, 0, socket_depth) * Rotation(180, 0, 0) * Pos(-offset_x, 0, 0) * lips
    )
    with BuildPart() as assembled:
        add(placed_body)
        add(placed_lips)
    # OCC integrates curved/text faces again after partitioning/fusing. A
    # sub-microlitre residual is not missing printed material: use the same
    # 0.01 mm³ physical volume tolerance as the existing foot-interface gate.
    volume_tolerance = 0.01
    common = (assembled.part & clean).volume
    missing = clean.volume - common
    extra = assembled.part.volume - common
    report.check(
        abs(missing) < volume_tolerance and abs(extra) < volume_tolerance,
        "glued prints retain socket, roof, closure and labels without supports",
        f"missing={missing:.6f}, extra={extra:.6f} mm³; "
        f"tolerance={volume_tolerance:g} mm³",
    )
    # Test physical overlap directly. Subtracting separately integrated total
    # volumes gave a -0.023048 mm³ residual on the long engraved wood lid even
    # though clean assembled equivalence passed; it is not an overlap measure.
    overlap = (placed_body & placed_lips).volume
    report.check(
        overlap < volume_tolerance,
        "reassembled prints meet without overlapping material",
        f"body/lips overlap={overlap:.6f} mm³; tolerance={volume_tolerance:g} mm³",
    )
    report.check(
        len(assembled.part.solids()) == 1,
        "flat glue faces meet with no vertical gap or separated receiver",
    )


def check_cover(
    cover: Part | Compound, foot_top: float, tool_tip_z: float, tip_clear: float
) -> Report:
    """Prove the foot fits after breaking out the grid, without relying on a view."""
    cover = as_part(cover)
    r = Report()
    r.section("stackable cover: foot interface and integral support")
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
    # The support is a single solid with the cover, but a tool can enter below
    # the lattice ribs and the center void remains removable after nib cutting.
    r.check(
        len(cover.solids()) == 1
        and is_solid_at(cover, 0, 0, 0.5)
        and not is_solid_at(cover, 2.5, 2.5, 0.5),
        "breakaway support is attached and has open lattice cells",
        f"{len(cover.solids())} solid(s), rib at center and adjacent open cell",
    )
    # Simulate snipping the lattice below the socket floor, then seat the actual
    # shared foot in the upright lid. An intersection means it cannot stack.
    with BuildPart() as trimmed:
        add(cover)
        Box(
            34,
            34,
            STACK_SOCKET_DEPTH,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    clean = trimmed.part
    r.check(
        not is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH - 0.1)
        and is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH + CAP_H / 2)
        and not is_solid_at(clean, 0, 0, STACK_SOCKET_DEPTH + CAP_H + 0.1),
        "removal exposes the socket floor with a solid cap beneath it",
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
    upright = Pos(0, 0, h) * Rotation(180, 0, 0) * clean
    foot = Pos(0, 0, h - STACK_SOCKET_DEPTH) * gridfinity_foot()
    r.check(
        upright.intersect(foot).volume < 0.01,
        "real Gridfinity foot enters the cleared socket without collision",
        "foot placed on the socket floor, all 1x1 bevels included",
    )
    lower_foot = Pos(0, 0, h - STACK_SOCKET_DEPTH - 0.3) * gridfinity_foot()
    r.check(
        upright.intersect(lower_foot).volume > 1.0,
        "socket floor actually supports the foot rather than leaving a through-hole",
        "foot driven 0.3 mm into the floor must intersect",
    )
    return r
