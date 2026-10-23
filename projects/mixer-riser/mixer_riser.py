"""Riser for the mixer sleeve on a Yamaha Tyros 3: two side brackets and a two-piece
plate, tilted toward the player. Made with CadQuery.

The Tyros rear panel has four threaded holes in a row near its top edge: an outer
pair OUTER apart and an inner pair INNER apart, so each side has two holes close
together. One identical bracket per side screws into its pair, hooks over the rear
edge with a ledge, and carries a stub tilted TILT degrees. Two identical plate
halves lie on the stubs, overlap in the middle with a half-lap, and are clamped
together by the sleeve's own four screws on its 80 x 80 pattern.

Use frame: X forward over the keyboard, Y across, Z up. The panel is the plane
x = 0, the holes are at z = 0, the keyboard's middle is y = 0.
Run `uv run mixer_riser.py` to write the STEP of the assembly and one STL per
part in its print orientation, or `uv run mixer_riser.py --serve` to adjust it.
"""
import math

import cadquery as cq

# 🎹 Keyboard. The four threaded holes on the Tyros 3 rear panel, in one row.
OUTER = 295.0        # Distance between the two outer holes, measured. [100:400]
INNER = 274.0        # Distance between the two inner holes, measured. [80:380]
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
T = 6.0              # Thickness of the base plate, the arm, the stub and the plate halves. [4:12]
BRK_W = 50.0         # Bracket width across the keyboard, its pair of holes centred in it. [30:100]
BASE_DOWN = 20.0     # Base plate below the holes. [10:60]
LEDGE = 15.0         # A ledge from the arm rests on the keyboard's top, over the rear edge. [0:40]
EDGE_GAP = 20.0      # Gap between the keyboard's top edge and the plate's underside: a thumb. [14:60]
TILT = 15.0          # Slope toward the player, degrees from horizontal. [0:40]
PLATE_L = 110.0      # Depth of the stub and the plate along the slope. [90:200]
RIB_T = 4 * LINE     # Thickness of the two ribs bracing the stub down to the ledge, 4 lines. [1.2:8]
STUB_SCREW_D = 4.0   # Screws through each plate half into its stub, M4, two per side. [3:6]
ROUND = 1.5          # Radius on the base plate's bottom corners. [0:4]

# 🪢 Plate halves. Two identical flat plates, overlapping in the middle.
OVERLAP = 100.0      # Length of the half-lap overlap, centred on the keyboard. [60:160]
PLATE_MARGIN = 10.0  # Plate reach beyond the bracket's outer face. [0:30]

ANG = math.radians(TILT)
PITCH = (OUTER - INNER) / 2                   # The two holes of one side.
YC = (OUTER + INNER) / 4                      # Bracket centre, each side.
UNDER_REAR_Z = PANEL_TOP + EDGE_GAP           # The plate's underside at the arm.
HALF_Y = YC + BRK_W / 2 + PLATE_MARGIN + OVERLAP / 2  # One plate half, across.
DOWN = (-math.sin(ANG), -math.cos(ANG))       # Downward normal of the slope, (x, z).
assert min(T, RIB_T) >= 2 * LINE, "a wall is thinner than two lines"


def check_design():
    """Design rules, run inside build() so the configurator reports them in its build log."""
    assert PITCH >= HEAD_D + 0.5, f"the two heads of a pair would touch: pitch {PITCH:.1f}, heads {HEAD_D}"
    assert PITCH + HEAD_D + 10 <= BRK_W, "the bracket is narrower than its pair of screws"
    assert EDGE_GAP > T / math.cos(ANG) + T + 2, "the ledge needs room under the stub: raise EDGE_GAP"
    assert OVERLAP / 2 > PATTERN / 2 + SLEEVE_SCREW_D, "the sleeve's screws must sit inside the overlap"
    assert HALF_Y <= 250, "a plate half is longer than the bed"


def slope_plane(origin=(0.0, 0.0, UNDER_REAR_Z)):
    """A workplane on the plate's underside: x along the slope, normal up."""
    return cq.Plane(origin=origin, xDir=(math.cos(ANG), 0, -math.sin(ANG)), normal=(-DOWN[0], 0, -DOWN[1]))


def bracket_profile():
    """Side profile in XZ: base plate, arm with its ledge, and the tilted stub."""
    top_rear = (0.0, UNDER_REAR_Z)
    top_front = (PLATE_L * math.cos(ANG), UNDER_REAR_Z - PLATE_L * math.sin(ANG))
    under_front = (top_front[0] + DOWN[0] * T, top_front[1] + DOWN[1] * T)
    under_rear = (0.0, UNDER_REAR_Z - T / math.cos(ANG))
    pts = [(-T, -BASE_DOWN), (0.0, -BASE_DOWN), (0.0, PANEL_TOP), (LEDGE, PANEL_TOP), (LEDGE, PANEL_TOP + T),
           (0.0, PANEL_TOP + T), under_rear, under_front, top_front, top_rear, (-T, UNDER_REAR_Z)]
    if LEDGE <= 0:
        pts = [(-T, -BASE_DOWN), (0.0, -BASE_DOWN), under_rear, under_front, top_front, top_rear, (-T, UNDER_REAR_Z)]
    return cq.Workplane("XZ").polyline(pts).close()


def bracket():
    """One side bracket, centred on y = 0, in the use frame."""
    body = bracket_profile().extrude(-BRK_W)
    bb = body.val().BoundingBox()
    body = body.translate((0, -bb.ymin - BRK_W / 2, 0))
    if ROUND > 0:
        try:
            body = body.edges("|Y").edges(cq.selectors.BoxSelector((-T - 1, -BRK_W, -BASE_DOWN - 1), (1, BRK_W, -BASE_DOWN + 1))) \
                .fillet(ROUND)
        except Exception as e:
            print(f"round skipped on the base plate's bottom: {e}")
    # Two ribs flush with the side faces, from the stub's underside down to the ledge.
    under_rear_z = UNDER_REAR_Z - T / math.cos(ANG)
    reach = under_rear_z - (PANEL_TOP + T)
    for y in (-BRK_W / 2, BRK_W / 2 - RIB_T):
        tri = [(0.0, under_rear_z), (0.0, PANEL_TOP + T), (reach * math.cos(ANG), under_rear_z - reach * math.sin(ANG))]
        body = body.union(cq.Workplane("XZ", origin=(0, y, 0)).polyline(tri).close().extrude(-RIB_T))
    # The pair of panel screws, through the base plate.
    for y in (-PITCH / 2, PITCH / 2):
        body = body.cut(cq.Workplane("YZ", origin=(-T - 1, y, 0)).circle(SCREW_D / 2 + 0.25).extrude(T + 2))
    # Two screws through the stub, for the plate half, along the slope.
    pts = [(PLATE_L / 2 - 30, 0), (PLATE_L / 2 + 30, 0)]
    body = body.cut(cq.Workplane(slope_plane()).workplane(offset=-T - 1).pushPoints(pts)
                    .circle(STUB_SCREW_D / 2 + 0.25).extrude(T + 2))
    return body


def plate_half():
    """One plate half, flat, in its own frame: x along the slope, y across from its outer
    end (y = 0 over the bracket's outer face) to the lap at y = HALF_Y, z up from 0 to T.
    The lap removes the top half of the thickness over the last OVERLAP; the other
    half is the same part turned over."""
    plate = cq.Workplane("XY").box(PLATE_L, HALF_Y, T, centered=(False, False, False))
    plate = plate.cut(cq.Workplane("XY").box(PLATE_L + 2, OVERLAP, T, centered=(False, False, False))
                      .translate((-1, HALF_Y - OVERLAP, T / 2)))
    yb = PLATE_MARGIN + BRK_W / 2  # The bracket's centre line, in this frame.
    stub = [(PLATE_L / 2 - 30, yb), (PLATE_L / 2 + 30, yb)]
    plate = plate.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints(stub).circle(STUB_SCREW_D / 2 + 0.25).extrude(T + 2))
    yc = HALF_Y - OVERLAP / 2  # The keyboard's middle, in this frame.
    pattern = [(PLATE_L / 2 + sx * PATTERN / 2, yc + sy * PATTERN / 2) for sx in (-1, 1) for sy in (-1, 1)]
    plate = plate.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints(pattern).circle(SLEEVE_SCREW_D / 2 + 0.25).extrude(T + 2))
    return plate


def place_half(half, side):
    """Put a plate half on the slope: side -1 is the left half, +1 the right one, turned over."""
    y_outer = -(YC + BRK_W / 2 + PLATE_MARGIN)
    if side > 0:
        half = half.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, T))  # Turn it over: lap now at the bottom.
        half = half.translate((0, -y_outer, 0))                               # Its outer end at +y.
    else:
        half = half.translate((0, y_outer, 0))
    return half.rotate((0, 0, 0), (0, 1, 0), TILT).translate((0, 0, UNDER_REAR_Z))


def build():
    """The assembly in the use frame: two brackets and two plate halves, as one compound."""
    check_design()
    b = bracket()
    pieces = [b.translate((0, -YC, 0)), b.translate((0, YC, 0)),
              place_half(plate_half(), -1), place_half(plate_half(), +1)]
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound([p.val() for p in pieces])])


def parts():
    """Each printable part in its print orientation, at the origin."""
    b = bracket().rotate((0, 0, 0), (1, 0, 0), -90)  # On its side: the profile face on the bed.
    bb = b.val().BoundingBox()
    b = b.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    h = plate_half()  # Flat, lap step on top.
    return {"bracket": b, "plate_half": h}


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
        "Base plate": {"at": (-T - 0.5, -YC, 0), "normal": (-1, 0, 0), "params": ["T", "BRK_W", "BASE_DOWN"]},
        "Panel screws": {"at": (-T - 0.5, -YC + PITCH / 2, 0), "normal": (-1, 0, 0),
                         "params": ["OUTER", "INNER", "SCREW_D", "HEAD_D"]},
        "Arm": {"at": (-T - 0.5, -YC, UNDER_REAR_Z / 2), "normal": (-1, 0, 0), "params": ["PANEL_TOP", "EDGE_GAP"]},
        "Ledge": {"at": (LEDGE / 2, -YC, PANEL_TOP + T + 0.5), "normal": (0, 0, 1), "params": ["LEDGE", "PANEL_TOP"]},
        "Stub": {"at": (PLATE_L * 0.8 * c, -YC - BRK_W / 2 - 0.5, UNDER_REAR_Z - PLATE_L * 0.8 * s - T / 2), "normal": (0, -1, 0),
                 "params": ["TILT", "PLATE_L", "STUB_SCREW_D"]},
        "Rib": {"at": ((EDGE_GAP - T) / 4, -YC - BRK_W / 2 - 0.5, UNDER_REAR_Z - T - (EDGE_GAP - T) / 3), "normal": (0, -1, 0),
                "params": ["RIB_T", "EDGE_GAP"]},
        "Plate half": {"at": (mid[0], -YC, mid[1] + 0.5), "normal": up, "params": ["PLATE_L", "PLATE_MARGIN", "T"]},
        "Lap joint": {"at": (mid[0], 0, mid[1] + 0.5), "normal": up, "params": ["OVERLAP"]},
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
              f"volume {shape.val().Volume() / 1000:.1f} cm3, print 2")
    print(f"assembly size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print("wrote mixer_riser.step and one STL per part")
