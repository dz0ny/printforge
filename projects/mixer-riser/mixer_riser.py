"""Riser for the mixer sleeve on a Yamaha Tyros 3, made with smlibpy.

Two side pieces screw into the rear panel holes and hook over the rear edge with a ledge.
Each piece carries half of the tilted plate, and the halves meet in a dovetail puzzle joint.
The four sleeve screws on the 80 x 80 pattern hold both halves, so no screws join the prints.
X points forward, Y across and Z up, with the panel at x = 0 and the holes at z = 0.
Run `uv run mixer_riser.py` for the STEP and one STL per part, or add `--serve` for the configurator.
"""
import math

from smlibpy import (Align, Box, Circle, Cylinder, Plane, Polygon, Rectangle, X, Y)

# 🎹 Keyboard holes: four threaded holes in one row on the Tyros 3 rear panel.
OUTER = 330.0        # Distance between the two outer holes, measured 33 cm. [100:400].
INNER = 270.0        # Distance between the two inner holes, measured 27 cm. [80:380].
SCREW_D = 5.0        # Screw thread, M5, with 0.5 mm clearance in the holes. [3:8].
HEAD_D = 9.0         # Screw head diameter, so the two heads of a pair do not touch. [5:14].

# 📏 Keyboard top above the holes.
PANEL_TOP = 25.0     # Height of the top edge of the panel above the holes, measured. [0:150].
TOP_TILT = 8.0       # Slope of the keyboard top toward the player in degrees, for the ghost. [0:25].
TOP_DEPTH = 300.0    # Forward reach of the keyboard top from the panel, for the ghost. [100:600].

# 🎛️ Mixer sleeve from projects/mixer-sleeve, which this riser carries.
SLEEVE_W = 198.2     # Sleeve width, across. [100:300].
SLEEVE_L = 213.5     # Sleeve length, along the slope. [100:300].
SLEEVE_T = 34.0      # Sleeve height off its back plate. [10:80].
PATTERN = 80.0       # Mount pattern of the sleeve, 80 x 80 mm, M1 to M4. [40:160].
SLEEVE_SCREW_D = 4.0  # Sleeve screws, M4, through both plate halves into its pads. [3:6].

# 🖨️ Printer. The side pieces print on their side.
NOZZLE = 0.4
LINE = 0.45          # Line width, about 1.1 x the nozzle.
LAYER = 0.2

# 🧱 Bracket: one side profile extruded across BRK_W.
T = 6.0              # Thickness of the plate and the ledge. [4:12].
ARM_T = 20.0         # Thickness of the base plate and the arm, which the screws bear on. [6:30].
BRK_W = 50.0         # Bracket width across the keyboard, with its pair of holes in the centre. [30:100].
BASE_DOWN = 20.0     # Base plate length below the holes. [10:60].
LEDGE = 15.0         # Length of the ledge that rests on the keyboard top, over the rear edge. [0:40].

# 📐 Plate on the slope.
EDGE_GAP = 20.0      # Gap between the keyboard top edge and the plate underside, for a thumb. [14:60].
TILT = 15.0          # Slope toward the player, in degrees from horizontal. [0:40].
PLATE_L = 90.0       # Plate reach forward from the arm, along the slope. [60:200].
PLATE_BACK = 80.0    # Plate reach backward over the arm, so the side view is a T. [0:150].

# 💪 Stiffness and edges.
GUSSET = True        # Full-width gusset from the plate underside down to the ledge. [0:1].
ROUND = 1.5          # Radius on the bottom corners of the base plate. [0:4].

# 🪢 Puzzle joint where the two halves meet.
JOINT = 14.0         # Tongue length into the other half. [8:30].
JOINT_W = 30.0       # Tongue width at its root. [15:50].
JOINT_FLARE = 3.0    # Dovetail flare on each side of the tip, so the halves cannot pull apart. [0:6].
JOINT_FIT = 0.2      # Clearance per side between tongue and socket. [0:0.6].
PLATE_MARGIN = 0.0   # Plate reach beyond the outer bracket face, zero so the face sits on the bed. [0:30].

ANG = math.radians(TILT)
PITCH = (OUTER - INNER) / 2                   # Distance between the two holes of one side.
YC = (OUTER + INNER) / 4                      # Bracket centre on each side.
UNDER_REAR_Z = PANEL_TOP + EDGE_GAP           # Height of the plate underside at the front face of the arm.
S_MID = (PLATE_L - PLATE_BACK) / 2            # Middle of the plate along the slope, where the sleeve sits.
HALF_Y = YC + BRK_W / 2 + PLATE_MARGIN         # Distance from the outer end of the plate to the keyboard middle.
DOWN = (-math.sin(ANG), -math.cos(ANG))       # Downward normal of the slope, as (x, z).
assert T >= 2 * LINE, "a wall is thinner than two lines"


def check_design():
    """Check the design rules. The configurator shows a failed rule in its build log."""
    assert PITCH >= HEAD_D + 0.5, f"the two heads of a pair would touch: pitch {PITCH:.1f}, heads {HEAD_D}"
    assert PITCH + HEAD_D + 10 <= BRK_W, "the bracket is narrower than its pair of screws"
    assert EDGE_GAP > T / math.cos(ANG) + T + 2, "the ledge needs room under the stub: raise EDGE_GAP"
    assert 2 * JOINT_W + 2 * JOINT_FLARE + 20 <= PLATE_L, "the plate is too short for the tongue and the socket"
    assert PLATE_L + PLATE_BACK >= PATTERN + 10, "the plate is shorter than the sleeve's pattern"
    assert HALF_Y + JOINT <= 250, "a side piece is taller than the bed when printed on its side"


def slope_plane(origin=(0.0, 0.0, UNDER_REAR_Z)):
    """Return a plane on the plate underside, with x along the slope and the normal up."""
    return Plane(origin=origin, x_dir=(math.cos(ANG), 0, -math.sin(ANG)), z_dir=(-DOWN[0], 0, -DOWN[1]))


def bracket_profile():
    """Return the side profile of the bracket as a sketch: base plate, arm, ledge and sloped top.

    The plate is a separate slab in the plane of the slope.
    """
    arm_top_rear = (-ARM_T, UNDER_REAR_Z + ARM_T * math.tan(ANG))  # Plate underside at the rear face of the arm.
    pts = [(-ARM_T, -BASE_DOWN), (0.0, -BASE_DOWN), (0.0, PANEL_TOP), (LEDGE, PANEL_TOP), (LEDGE, PANEL_TOP + T),
           (0.0, PANEL_TOP + T), (0.0, UNDER_REAR_Z), arm_top_rear]
    if LEDGE <= 0:
        pts = [(-ARM_T, -BASE_DOWN), (0.0, -BASE_DOWN), (0.0, UNDER_REAR_Z), arm_top_rear]
    return Polygon(pts)


def joint_shape(x0, length, w_root, w_tip):
    """Return a dovetail outline in the plate plane as (x, y) points, root at y = 0 and tip at y = length."""
    cx = x0 + w_root / 2
    return [(cx - w_root / 2, 0.0), (cx + w_root / 2, 0.0), (cx + w_tip / 2, length), (cx - w_tip / 2, length)]


def side_piece(right=False):
    """Return one side piece in its own frame, with the bracket at y near 0 and the joint at y = HALF_Y.

    The right piece is the left piece with tongue and socket swapped.
    The assembly mirrors it, so the two pieces interlock.
    """
    # On the front plane, a negative extrusion grows toward +Y.
    body = bracket_profile().on(Plane.XZ).extrude(-BRK_W)
    body = body.translate(0, PLATE_MARGIN - body.bbox().min.y, 0)
    if ROUND > 0:
        corners = [e for e in body.edges().parallel_to(Y)
                   if -ARM_T - 1 <= e.center().x <= 1 and abs(e.center().z + BASE_DOWN) < 1]
        try:
            body = body.fillet(corners, ROUND)
        except Exception as e:  # A failed round leaves the corners sharp, and the part stays whole.
            print(f"round skipped on the bottom of the base plate: {e}")
    # The gusset is as wide as the bracket and goes from the plate underside down to the ledge.
    # Thin ribs would have a side that faces down in the print, and the gusset has none.
    if GUSSET:
        reach = UNDER_REAR_Z - (PANEL_TOP + T)
        tri = [(0.0, UNDER_REAR_Z), (0.0, PANEL_TOP + T), (reach * math.cos(ANG), UNDER_REAR_Z - reach * math.sin(ANG))]
        body += Polygon(tri).on(Plane.XZ).extrude(-BRK_W).translate(0, PLATE_MARGIN, 0)
    # The pair of panel screws goes through the base plate.
    for y in (PLATE_MARGIN + BRK_W / 2 - PITCH / 2, PLATE_MARGIN + BRK_W / 2 + PITCH / 2):
        hole = Cylinder(SCREW_D / 2 + 0.25, ARM_T + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(Y, 90)
        body -= hole.translate(-ARM_T - 1, y, 0)
    # The plate continues the stub of the bracket across to the middle, with the tongue at its end.
    # Draw it flat in the slope plane, then cut the socket and the sleeve holes.
    plane = slope_plane()
    x_low, x_high = 10.0, PLATE_L - 10.0 - JOINT_W
    tongue_x, socket_x = (x_high, x_low) if right else (x_low, x_high)
    tx = joint_shape(tongue_x, JOINT, JOINT_W, JOINT_W + 2 * JOINT_FLARE)
    # The outline goes along the bottom, up the right edge, round the tongue and down the left edge.
    outline = [(-PLATE_BACK, 0.0), (PLATE_L, 0.0), (PLATE_L, HALF_Y), (tx[1][0], HALF_Y), (tx[2][0], HALF_Y + JOINT),
               (tx[3][0], HALF_Y + JOINT), (tx[0][0], HALF_Y), (-PLATE_BACK, HALF_Y)]
    plate = Polygon(outline).on(plane).extrude(T)
    socket = joint_shape(socket_x - JOINT_FIT, JOINT + JOINT_FIT,
                         JOINT_W + 2 * JOINT_FIT, JOINT_W + 2 * JOINT_FLARE + 2 * JOINT_FIT)
    below = plane.offset(-1)
    plate -= Polygon([(x, HALF_Y - y) for x, y in socket]).on(below).extrude(T + 2)
    for sx in (-1, 1):
        hole = Circle(SLEEVE_SCREW_D / 2 + 0.25).translate(S_MID + sx * PATTERN / 2, HALF_Y - PATTERN / 2, 0)
        plate -= hole.on(below).extrude(T + 2)
    return body + plate


def build():
    """Return the assembly in the use frame as a list: the left piece, and its mirror for the right.

    The two pieces stay separate, because a fuse would join their plates where they touch.
    """
    check_design()
    a = side_piece().translate(0, -HALF_Y, 0)                          # Left: outer end at -y, joint at y = 0.
    b = side_piece(right=True).mirror(Plane.XZ).translate(0, HALF_Y, 0)  # Right: the mirror, tongue and socket swapped.
    return [a, b]


def parts():
    """Return the two printable parts in print orientation, on their side with the profile face on the bed."""
    out = {}
    # The bracket is at low y on the left piece and at high y on the right piece.
    # The two pieces thus turn opposite ways.
    for name, piece, angle in (("left", side_piece(), 90), ("right", side_piece(right=True).mirror(Plane.XZ), -90)):
        p = piece.rotate(X, angle)
        low = p.bbox().min
        out[name] = p.translate(-low.x, -low.y, -low.z)
    return out


def device():
    """Return the panel and the sloped top of the keyboard, and the sleeve on the plate, for the ghost view."""
    span = OUTER + 2 * BRK_W
    panel = Box(2, span, PANEL_TOP + BASE_DOWN + 10, align=(Align.MIN, Align.CENTER, Align.MIN))
    panel = panel.translate(0.5, 0, -BASE_DOWN - 10)
    drop = TOP_DEPTH * math.tan(math.radians(TOP_TILT))
    top = Polygon([(0.5, PANEL_TOP), (TOP_DEPTH, PANEL_TOP - drop), (TOP_DEPTH, PANEL_TOP - drop - 6),
                   (0.5, PANEL_TOP - 6)]).on(Plane.XZ).extrude(-span).translate(0, -span / 2, 0)
    sleeve = Rectangle(SLEEVE_L, SLEEVE_W).translate(S_MID, 0, 0).on(slope_plane().offset(T)).extrude(SLEEVE_T)
    return panel + top + sleeve


def features():
    """Return the named features with an anchor, an outward normal and the settings behind each."""
    c, s = math.cos(ANG), math.sin(ANG)
    mid = (S_MID * c, UNDER_REAR_Z - S_MID * s + T * c)  # Plate top in the middle of the slope, as (x, z).
    up = (s, 0, c)
    return {
        "Base plate": {"at": (-ARM_T - 0.5, -YC, 0), "normal": (-1, 0, 0), "params": ["ARM_T", "BRK_W", "BASE_DOWN"]},
        "Panel screws": {"at": (-ARM_T - 0.5, -YC + PITCH / 2, 0), "normal": (-1, 0, 0),
                         "params": ["OUTER", "INNER", "SCREW_D", "HEAD_D"]},
        "Arm": {"at": (-ARM_T - 0.5, -YC, UNDER_REAR_Z / 2), "normal": (-1, 0, 0), "params": ["ARM_T", "PANEL_TOP", "EDGE_GAP"]},
        "Ledge": {"at": (LEDGE / 2, -YC, PANEL_TOP + T + 0.5), "normal": (0, 0, 1), "params": ["LEDGE", "PANEL_TOP"]},
        "Gusset": {"at": ((EDGE_GAP - T) / 4, -YC - BRK_W / 2 - 0.5, UNDER_REAR_Z - (EDGE_GAP - T) / 3), "normal": (0, -1, 0),
                   "params": ["GUSSET", "EDGE_GAP"]},
        "Plate": {"at": (mid[0], -YC, mid[1] + 0.5), "normal": up, "params": ["TILT", "PLATE_L", "PLATE_BACK", "T"]},
        "Back wing": {"at": (-PLATE_BACK * 0.6 * c, -YC, UNDER_REAR_Z + PLATE_BACK * 0.6 * s - 0.5), "normal": (-s, 0, -c),
                      "params": ["PLATE_BACK"]},
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
        host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"  # Use --lan to open the page from a phone.
        serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
        sys.exit()

    from smlibpy import export_step, export_stl

    asm = build()
    assert all(p.is_valid() for p in asm), "invalid assembly"
    export_step(asm, "mixer_riser.step")
    lo = [min(p.bbox().min[i] for p in asm) for i in range(3)]
    hi = [max(p.bbox().max[i] for p in asm) for i in range(3)]
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)
    for name, shape in parts().items():
        assert shape.is_valid() and len(shape.solids()) == 1, f"{name} is not one valid solid"
        ps = shape.bbox().size
        assert max(ps.x, ps.y) < 256 and ps.z < 250, f"{name} does not fit the bed"
        export_stl(shape, f"mixer_riser_{name}.stl", tolerance=0.05)
        print(f"{name}: print size {ps.x:.1f} x {ps.y:.1f} x {ps.z:.1f} mm, volume {shape.volume / 1000:.1f} cm3, print 1")
    print(f"assembly size {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm")
    print("wrote mixer_riser.step and one STL per part")
