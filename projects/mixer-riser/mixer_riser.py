"""Riser for the mixer sleeve on a Yamaha Tyros 3: two identical side pieces that
meet in the middle, tilted toward the player. Made with CadQuery.

The Tyros rear panel has four threaded holes in a row near its top edge: an outer
pair OUTER apart and an inner pair INNER apart, so each side has two holes close
together. Each side piece screws into its pair, hooks over the rear edge with a
ledge, and carries half of the tilted plate in one print. The two halves meet in
the middle with an in-plane dovetail puzzle joint that drops together; the
sleeve's own four screws on its 80 x 80 pattern then hold both halves. No screws
join the printed parts to each other.

Use frame: X forward over the keyboard, Y across, Z up. The panel is the plane
x = 0, the holes are at z = 0, the keyboard's middle is y = 0.
Run `uv run mixer_riser.py` to write the STEP of the assembly and one STL per
part in its print orientation, or `uv run mixer_riser.py --serve` to adjust it.
"""
import math

import cadquery as cq

# 🎹 Keyboard. The four threaded holes on the Tyros 3 rear panel, in one row.
OUTER = 330.0        # Distance between the two outer holes, measured 33 cm. [100:400]
INNER = 270.0        # Distance between the two inner holes, measured 27 cm. [80:380]
SCREW_D = 5.0        # Screw thread, M5. The holes get 0.5 mm clearance. [3:8]
HEAD_D = 9.0         # Screw head diameter, so the two heads of a pair do not touch. [5:14]
PANEL_TOP = 25.0     # Height of the panel's top edge above the holes, measured. [0:150]
TOP_TILT = 8.0       # The keyboard's top slopes toward the player by this, degrees, for the ghost. [0:25]
TOP_DEPTH = 300.0    # How far the keyboard's top reaches forward from the panel, for the ghost. [100:600]

# 🎛️ Mixer sleeve. The part this riser carries, from projects/mixer-sleeve.
SLEEVE_W = 198.2     # Sleeve width, across. [100:300]
SLEEVE_L = 213.5     # Sleeve length, along the slope. [100:300]
SLEEVE_T = 34.0      # Sleeve height off its back plate. [10:80]
PATTERN = 80.0       # The sleeve's mount pattern, 80 x 80 mm, M1 to M4. [40:160]
SLEEVE_SCREW_D = 4.0  # The sleeve's screws, M4, through both plate halves into its pads. [3:6]

# 🖨️ Printer. The brackets print on their side, the plate halves flat.
NOZZLE = 0.4
LINE = 0.45          # Line width, about 1.1 x the nozzle.
LAYER = 0.2

# 🧱 Bracket. One side profile extruded across BRK_W, two ribs, a tilted stub.
T = 6.0              # Thickness of the plate and the ledge. [4:12]
ARM_T = 20.0         # Thickness of the base plate and the arm against the panel: the screws bear on all of it. [6:30]
BRK_W = 50.0         # Bracket width across the keyboard, its pair of holes centred in it. [30:100]
BASE_DOWN = 20.0     # Base plate below the holes. [10:60]
LEDGE = 15.0         # A ledge from the arm rests on the keyboard's top, over the rear edge. [0:40]
EDGE_GAP = 20.0      # Gap between the keyboard's top edge and the plate's underside: a thumb. [14:60]
TILT = 15.0          # Slope toward the player, degrees from horizontal. [0:40]
PLATE_L = 90.0       # Depth of the stub and the plate along the slope: the pattern plus 5 mm each side. [85:200]
RIB_T = 4 * LINE     # Thickness of the two ribs bracing the stub down to the ledge, 4 lines. [1.2:8]
ROUND = 1.5          # Radius on the base plate's bottom corners. [0:4]

# 🪢 Puzzle joint. The two halves meet in the middle with a dovetail tongue and socket.
JOINT = 14.0         # Tongue length into the other half. [8:30]
JOINT_W = 30.0       # Tongue width at its root; the tip is JOINT_FLARE wider on each side. [15:50]
JOINT_FLARE = 3.0    # Dovetail flare, so the halves cannot pull apart. [0:6]
JOINT_FIT = 0.2      # Clearance per side between tongue and socket. [0:0.6]
PLATE_MARGIN = 0.0   # Plate reach beyond the bracket's outer face. Keep 0: printed on its side, the bracket face must sit on the bed. [0:30]

ANG = math.radians(TILT)
PITCH = (OUTER - INNER) / 2                   # The two holes of one side.
YC = (OUTER + INNER) / 4                      # Bracket centre, each side.
UNDER_REAR_Z = PANEL_TOP + EDGE_GAP           # The plate's underside at the arm.
HALF_Y = YC + BRK_W / 2 + PLATE_MARGIN         # From the plate's outer end to the keyboard's middle.
DOWN = (-math.sin(ANG), -math.cos(ANG))       # Downward normal of the slope, (x, z).
assert min(T, RIB_T) >= 2 * LINE, "a wall is thinner than two lines"


def check_design():
    """Design rules, run inside build() so the configurator reports them in its build log."""
    assert PITCH >= HEAD_D + 0.5, f"the two heads of a pair would touch: pitch {PITCH:.1f}, heads {HEAD_D}"
    assert PITCH + HEAD_D + 10 <= BRK_W, "the bracket is narrower than its pair of screws"
    assert EDGE_GAP > T / math.cos(ANG) + T + 2, "the ledge needs room under the stub: raise EDGE_GAP"
    assert 2 * JOINT_W + 2 * JOINT_FLARE + 20 <= PLATE_L, "the plate is too short for the tongue and the socket"
    assert HALF_Y + JOINT <= 250, "a side piece is taller than the bed when printed on its side"


def slope_plane(origin=(0.0, 0.0, UNDER_REAR_Z)):
    """A workplane on the plate's underside: x along the slope, normal up."""
    return cq.Plane(origin=origin, xDir=(math.cos(ANG), 0, -math.sin(ANG)), normal=(-DOWN[0], 0, -DOWN[1]))


def bracket_profile():
    """Side profile in XZ: base plate, arm with its ledge, and the tilted stub."""
    top_rear = (0.0, UNDER_REAR_Z)
    top_front = (PLATE_L * math.cos(ANG), UNDER_REAR_Z - PLATE_L * math.sin(ANG))
    under_front = (top_front[0] + DOWN[0] * T, top_front[1] + DOWN[1] * T)
    under_rear = (0.0, UNDER_REAR_Z - T / math.cos(ANG))
    pts = [(-ARM_T, -BASE_DOWN), (0.0, -BASE_DOWN), (0.0, PANEL_TOP), (LEDGE, PANEL_TOP), (LEDGE, PANEL_TOP + T),
           (0.0, PANEL_TOP + T), under_rear, under_front, top_front, top_rear, (-ARM_T, UNDER_REAR_Z)]
    if LEDGE <= 0:
        pts = [(-ARM_T, -BASE_DOWN), (0.0, -BASE_DOWN), under_rear, under_front, top_front, top_rear, (-ARM_T, UNDER_REAR_Z)]
    return cq.Workplane("XZ").polyline(pts).close()


def joint_shape(x0, length, w_root, w_tip):
    """A dovetail outline in the plate's plane, as (x, y) points: root at y = 0,
    tip at y = length, width growing from w_root to w_tip."""
    cx = x0 + w_root / 2
    return [(cx - w_root / 2, 0.0), (cx + w_root / 2, 0.0), (cx + w_tip / 2, length), (cx - w_tip / 2, length)]


def side_piece(right=False):
    """One side piece in its own frame: the bracket at the plate's outer end (y near 0),
    the plate reaching to the keyboard's middle at y = HALF_Y, where a dovetail
    tongue and a socket meet the other piece. The right piece is the left one
    mirrored with tongue and socket swapped, so the two interlock."""
    body = bracket_profile().extrude(-BRK_W)
    bb = body.val().BoundingBox()
    body = body.translate((0, PLATE_MARGIN - bb.ymin, 0))
    if ROUND > 0:
        try:
            body = body.edges("|Y").edges(cq.selectors.BoxSelector((-ARM_T - 1, -1, -BASE_DOWN - 1), (1, 400, -BASE_DOWN + 1))) \
                .fillet(ROUND)
        except Exception as e:
            print(f"round skipped on the base plate's bottom: {e}")
    # Two ribs flush with the bracket's side faces, from the plate's underside down to the ledge.
    under_rear_z = UNDER_REAR_Z - T / math.cos(ANG)
    reach = under_rear_z - (PANEL_TOP + T)
    for y in (PLATE_MARGIN, PLATE_MARGIN + BRK_W - RIB_T):
        tri = [(0.0, under_rear_z), (0.0, PANEL_TOP + T), (reach * math.cos(ANG), under_rear_z - reach * math.sin(ANG))]
        body = body.union(cq.Workplane("XZ", origin=(0, y, 0)).polyline(tri).close().extrude(-RIB_T))
    # The pair of panel screws, through the base plate.
    for y in (PLATE_MARGIN + BRK_W / 2 - PITCH / 2, PLATE_MARGIN + BRK_W / 2 + PITCH / 2):
        body = body.cut(cq.Workplane("YZ", origin=(-ARM_T - 1, y, 0)).circle(SCREW_D / 2 + 0.25).extrude(ARM_T + 2))
    # The plate: the bracket's stub continued across to the middle, with the tongue,
    # drawn flat in the slope's plane and cut by the socket and the sleeve holes.
    plane = slope_plane()
    x_low, x_high = 10.0, PLATE_L - 10.0 - JOINT_W
    tongue_x, socket_x = (x_high, x_low) if right else (x_low, x_high)
    tx = joint_shape(tongue_x, JOINT, JOINT_W, JOINT_W + 2 * JOINT_FLARE)
    # Walk the outline: bottom edge, right edge up to the middle, the tongue, the left edge.
    outline = [(0.0, 0.0), (PLATE_L, 0.0), (PLATE_L, HALF_Y), (tx[1][0], HALF_Y), (tx[2][0], HALF_Y + JOINT),
               (tx[3][0], HALF_Y + JOINT), (tx[0][0], HALF_Y), (0.0, HALF_Y)]
    plate = cq.Workplane(plane).polyline(outline).close().extrude(T)
    socket = joint_shape(socket_x - JOINT_FIT, JOINT + JOINT_FIT,
                         JOINT_W + 2 * JOINT_FIT, JOINT_W + 2 * JOINT_FLARE + 2 * JOINT_FIT)
    sock = cq.Workplane(plane).workplane(offset=-1).polyline([(x, HALF_Y - y) for x, y in socket]).close().extrude(T + 2)
    plate = plate.cut(sock)
    holes = [(PLATE_L / 2 + sx * PATTERN / 2, HALF_Y - PATTERN / 2) for sx in (-1, 1)]
    plate = plate.cut(cq.Workplane(plane).workplane(offset=-1).pushPoints(holes).circle(SLEEVE_SCREW_D / 2 + 0.25).extrude(T + 2))
    return body.union(plate)


def build():
    """The assembly in the use frame: the left piece, and the same piece turned around for the right."""
    check_design()
    a = side_piece().translate((0, -HALF_Y, 0))                     # Left: outer end at -y, joint at y = 0.
    b = side_piece(right=True).mirror("XZ").translate((0, HALF_Y, 0))  # Right: the mirror, tongue and socket swapped.
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound([a.val(), b.val()])])


def parts():
    """The two printable parts in print orientation: on their side, the profile face on the bed."""
    out = {}
    # Stand each piece on its bracket: the bracket is at low y on the left piece and
    # at high y on the mirrored right one, so they turn opposite ways.
    for name, piece, angle in (("left", side_piece(), 90), ("right", side_piece(right=True).mirror("XZ"), -90)):
        p = piece.rotate((0, 0, 0), (1, 0, 0), angle)
        bb = p.val().BoundingBox()
        out[name] = p.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    return out


def device():
    """The keyboard's panel and sloped top, and the sleeve on the plate, for the ghost view."""
    span = OUTER + 2 * BRK_W
    panel = cq.Workplane("XY").box(2, span, PANEL_TOP + BASE_DOWN + 10, centered=(False, True, False)) \
        .translate((0.5, 0, -BASE_DOWN - 10))
    drop = TOP_DEPTH * math.tan(math.radians(TOP_TILT))
    top = cq.Workplane("XZ").polyline([(0.5, PANEL_TOP), (TOP_DEPTH, PANEL_TOP - drop),
                                       (TOP_DEPTH, PANEL_TOP - drop - 6), (0.5, PANEL_TOP - 6)]).close() \
        .extrude(span / 2, both=True)
    plane = slope_plane()
    sleeve = cq.Workplane(plane).workplane(offset=T).center(PLATE_L / 2, 0).rect(SLEEVE_L, SLEEVE_W).extrude(SLEEVE_T)
    return panel.union(top).union(sleeve)


def features():
    c, s = math.cos(ANG), math.sin(ANG)
    mid = (PLATE_L / 2 * c, UNDER_REAR_Z - PLATE_L / 2 * s + T * c)  # Plate top, middle of the slope: (x, z).
    up = (s, 0, c)
    return {
        "Base plate": {"at": (-ARM_T - 0.5, -YC, 0), "normal": (-1, 0, 0), "params": ["ARM_T", "BRK_W", "BASE_DOWN"]},
        "Panel screws": {"at": (-ARM_T - 0.5, -YC + PITCH / 2, 0), "normal": (-1, 0, 0),
                         "params": ["OUTER", "INNER", "SCREW_D", "HEAD_D"]},
        "Arm": {"at": (-ARM_T - 0.5, -YC, UNDER_REAR_Z / 2), "normal": (-1, 0, 0), "params": ["ARM_T", "PANEL_TOP", "EDGE_GAP"]},
        "Ledge": {"at": (LEDGE / 2, -YC, PANEL_TOP + T + 0.5), "normal": (0, 0, 1), "params": ["LEDGE", "PANEL_TOP"]},
        "Rib": {"at": ((EDGE_GAP - T) / 4, -YC - BRK_W / 2 - 0.5, UNDER_REAR_Z - T - (EDGE_GAP - T) / 3), "normal": (0, -1, 0),
                "params": ["RIB_T", "EDGE_GAP"]},
        "Plate": {"at": (mid[0], -YC, mid[1] + 0.5), "normal": up, "params": ["TILT", "PLATE_L", "PLATE_MARGIN", "T"]},
        "Puzzle joint": {"at": (mid[0], 0, mid[1] + 0.5), "normal": up, "params": ["JOINT", "JOINT_W", "JOINT_FLARE", "JOINT_FIT"]},
        "Sleeve screws": {"at": (mid[0] + PATTERN / 2 * c, PATTERN / 2, mid[1] - PATTERN / 2 * s + 0.5), "normal": up,
                          "params": ["PATTERN", "SLEEVE_SCREW_D"]},
        "Sleeve": {"at": (mid[0] + SLEEVE_T * s, 0, mid[1] + SLEEVE_T * c + 0.5), "normal": up,
                   "params": ["SLEEVE_W", "SLEEVE_L", "SLEEVE_T", "TILT"]},
    }


def labels():
    out = {"_views": {"left": "Panel side", "right": "Player side", "top": "Top", "front": "Side"}}
    for name, f in features().items():
        if name == "Sleeve":
            continue
        out[name] = {"at": list(f["at"]), "normal": list(f["normal"])}
    return out


if __name__ == "__main__":
    import json
    import sys
    if "--serve" in sys.argv:
        from printforge_configurator import serve
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
        host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"  # --lan: reachable from a phone.
        serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
        sys.exit()

    asm = build()
    assert asm.val().isValid(), "invalid assembly"
    bb = asm.val().BoundingBox()
    cq.exporters.export(asm, "mixer_riser.step")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)
    for name, shape in parts().items():
        assert shape.val().isValid() and len(shape.solids().vals()) == 1, f"{name} is not one valid solid"
        pb = shape.val().BoundingBox()
        assert max(pb.xlen, pb.ylen) < 256 and pb.zlen < 250, f"{name} does not fit the bed"
        cq.exporters.export(shape, f"mixer_riser_{name}.stl", tolerance=0.05, angularTolerance=0.1)
        print(f"{name}: print size {pb.xlen:.1f} x {pb.ylen:.1f} x {pb.zlen:.1f} mm, "
              f"volume {shape.val().Volume() / 1000:.1f} cm3, print 1")
    print(f"assembly size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print("wrote mixer_riser.step and one STL per part")
