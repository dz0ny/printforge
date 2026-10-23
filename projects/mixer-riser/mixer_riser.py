"""Riser bracket: screws to the two holes on a Yamaha Tyros 3 rear panel and holds
the mixer sleeve above the keyboard, tilted toward the player. Made with CadQuery.

Side view, X forward over the keyboard, Z up, Y across. The Tyros rear panel is
the plane x = 0; the bracket's base plate sits against it with its two screw holes
at z = 0. The arm rises to RISE, where the plate starts and slopes down toward the
player at TILT degrees. The plate carries the sleeve's 80 x 80 mount pattern.
Run `uv run mixer_riser.py` to write the STEP and the STL, or
`uv run mixer_riser.py --serve` to adjust it in the browser.
"""
import math

import cadquery as cq

# 🎹 Keyboard. The two threaded holes on the Tyros 3 rear panel.
HOLE_PITCH = 63.0    # Distance between the two holes, measured. [20:200]
SCREW_D = 5.0        # Screw thread, M5. The holes get 0.5 mm clearance. [3:8]
HEAD_D = 9.0         # Screw head diameter, for the counterbore. [5:14]
PANEL_TOP = 40.0     # Height of the panel's top edge above the holes. Measure it. [0:150]
TOP_TILT = 8.0       # The keyboard's top slopes toward the player by this, degrees, for the ghost. [0:25]
TOP_DEPTH = 300.0    # How far the keyboard's top reaches forward from the panel, for the ghost. [100:600]

# 🎛️ Mixer sleeve. The part this bracket carries, from projects/mixer-sleeve.
SLEEVE_W = 198.2     # Sleeve width, across. [100:300]
SLEEVE_L = 213.5     # Sleeve length, along the slope. [100:300]
SLEEVE_T = 34.0      # Sleeve height off its back plate. [10:80]
PATTERN = 80.0       # The sleeve's mount pattern, 80 x 80 mm, M1 to M4. [40:160]
SLEEVE_SCREW_D = 4.0  # Screws into the sleeve's mount pads, M4. [3:6]
SLEEVE_HEAD_D = 7.5  # Their head diameter, counterbored from below. [5:12]

# 🖨️ Printer. The part prints on its side, so the profile's walls are vertical.
NOZZLE = 0.4
LINE = 0.45          # Line width, about 1.1 x the nozzle.
LAYER = 0.2

# 🧱 Bracket. One side profile extruded across W, plus two ribs.
T = 6.0              # Thickness of the base plate, the arm and the tilted plate. [4:12]
W = 100.0            # Width across the keyboard, the two holes centred in it. [70:160]
BASE_DOWN = 20.0     # Base plate below the holes. [10:60]
LEDGE = 15.0         # A ledge from the arm rests on the keyboard's top, over the rear edge. [0:40]
EDGE_GAP = 20.0      # Gap between the keyboard's top edge and the plate's underside: a thumb. [5:60]
TILT = 15.0          # Plate slope toward the player, degrees from horizontal. [0:40]
PLATE_L = 110.0      # Plate length along the slope; the pattern sits at its middle. [90:200]
RIB_T = 4 * LINE     # Thickness of the two ribs that brace the plate down to the ledge, 4 lines. [1.2:8]
ROUND = 1.5          # Radius on the outer corners of the profile. [0:4]

ANG = math.radians(TILT)
UNDER_REAR_Z = PANEL_TOP + EDGE_GAP           # The plate's underside at the arm, a thumb above the edge.
RISE = UNDER_REAR_Z + T / math.cos(ANG)       # The plate's top at the arm.
PLATE_DX, PLATE_DZ = PLATE_L * math.cos(ANG), PLATE_L * math.sin(ANG)
assert min(T, RIB_T) >= 2 * LINE, "a wall is thinner than two lines"
assert PATTERN + 2 * SLEEVE_HEAD_D < min(W, PLATE_L), "the plate is too small for the sleeve's pattern"


def check_design():
    """Design rules, run inside build() so the configurator reports them in its build log."""
    assert HOLE_PITCH + HEAD_D + 10 <= W, "the base plate is narrower than the two screws"
    assert EDGE_GAP > T + 2, "the ledge needs room under the plate: raise EDGE_GAP"


def profile():
    """The side profile in the XZ plane: base plate, arm with its ledge, and the tilted plate."""
    top_rear = (0.0, RISE)
    top_front = (PLATE_DX, RISE - PLATE_DZ)
    nx, nz = -math.sin(ANG), -math.cos(ANG)  # Downward normal of the plate.
    under_front = (top_front[0] + nx * T, top_front[1] + nz * T)
    under_rear = (0.0, UNDER_REAR_Z)
    pts = [(-T, -BASE_DOWN), (0.0, -BASE_DOWN), (0.0, PANEL_TOP), (LEDGE, PANEL_TOP), (LEDGE, PANEL_TOP + T),
           (0.0, PANEL_TOP + T), under_rear, under_front, top_front, top_rear, (-T, RISE)]
    if LEDGE <= 0:
        pts = [(-T, -BASE_DOWN), (0.0, -BASE_DOWN), under_rear, under_front, top_front, top_rear, (-T, RISE)]
    return cq.Workplane("XZ").polyline(pts).close()


def build():
    check_design()
    body = profile().extrude(-W).translate((0, -W / 2, 0))  # XZ extrudes along -Y; centre it.
    body = body.translate((0, W, 0)) if body.val().BoundingBox().ymax < 1 else body
    bb = body.val().BoundingBox()
    body = body.translate((0, -bb.ymin - W / 2, 0))
    if ROUND > 0:
        try:
            body = body.edges("|Y").edges(cq.selectors.BoxSelector((-T - 1, -W, -BASE_DOWN - 1), (1, W, -BASE_DOWN + 1))) \
                .fillet(ROUND)
        except Exception as e:
            print(f"round skipped on the base plate's bottom: {e}")
    # Two ribs, one near each edge, from the plate's underside down to the
    # ledge: they take the mixer's weight off the plate's root.
    nx, nz = -math.sin(ANG), -math.cos(ANG)
    reach = EDGE_GAP - T
    for y in (-W / 2, W / 2 - RIB_T):  # Flush with the side faces, so they print on their side.
        tri = [(0.0, UNDER_REAR_Z), (0.0, PANEL_TOP + T),
               (reach * math.cos(ANG), UNDER_REAR_Z - reach * math.sin(ANG))]
        rib = cq.Workplane("XZ", origin=(0, y, 0)).polyline(tri).close().extrude(-RIB_T)
        body = body.union(rib)
    # Screw holes into the panel, counterbored from the front (the keyboard side
    # is x > 0, the heads sit in the base plate's rear face at x = -T).
    for y in (-HOLE_PITCH / 2, HOLE_PITCH / 2):
        hole = cq.Workplane("YZ", origin=(-T - 1, y, 0)).circle(SCREW_D / 2 + 0.25).extrude(T + 2)
        body = body.cut(hole)
    # The sleeve pattern on the plate, counterbored from below, centred on the plate.
    cx, cz = PLATE_DX / 2, RISE - PLATE_DZ / 2
    plane = cq.Plane(origin=(cx, 0, cz), xDir=(math.cos(ANG), 0, -math.sin(ANG)), normal=(nx, 0, nz))
    pts = [(sx * PATTERN / 2, sy * PATTERN / 2) for sx in (-1, 1) for sy in (-1, 1)]
    holes = cq.Workplane(plane).workplane(offset=-T - 1).pushPoints(pts).circle(SLEEVE_SCREW_D / 2 + 0.25).extrude(T + 2)
    # Counterbores from below: the heads sit under the plate, 2 mm of plate stays above them.
    bores = cq.Workplane(plane).workplane(offset=2.0).pushPoints(pts).circle(SLEEVE_HEAD_D / 2 + 0.25).extrude(T)
    body = body.cut(holes).cut(bores)
    return body


def device():
    """The keyboard's top and panel, and the sleeve on the plate, for the ghost view."""
    nx, nz = -math.sin(ANG), -math.cos(ANG)
    panel = cq.Workplane("XY").box(2, W + 60, PANEL_TOP + BASE_DOWN + 10, centered=(False, True, False)) \
        .translate((0.5, 0, -BASE_DOWN - 10))
    # The keyboard's top: a slab from the rear edge, sloping toward the player.
    drop = TOP_DEPTH * math.tan(math.radians(TOP_TILT))
    top = cq.Workplane("XZ").polyline([(0.5, PANEL_TOP), (TOP_DEPTH, PANEL_TOP - drop),
                                       (TOP_DEPTH, PANEL_TOP - drop - 6), (0.5, PANEL_TOP - 6)]).close() \
        .extrude((W + 60) / 2, both=True)
    cx, cz = PLATE_DX / 2, RISE - PLATE_DZ / 2
    plane = cq.Plane(origin=(cx, 0, cz), xDir=(math.cos(ANG), 0, -math.sin(ANG)), normal=(-nx, 0, -nz))
    sleeve = cq.Workplane(plane).rect(SLEEVE_L, SLEEVE_W).extrude(SLEEVE_T)
    return panel.union(top).union(sleeve)


def features():
    cx, cz = PLATE_DX / 2, RISE - PLATE_DZ / 2
    return {
        "Base plate": {"at": (-T - 0.5, 0, 0), "normal": (-1, 0, 0), "params": ["T", "W", "BASE_DOWN"]},
        "Panel screws": {"at": (-T - 0.5, HOLE_PITCH / 2, 0), "normal": (-1, 0, 0),
                         "params": ["HOLE_PITCH", "SCREW_D", "HEAD_D"]},
        "Arm": {"at": (-T - 0.5, 0, RISE / 2), "normal": (-1, 0, 0), "params": ["PANEL_TOP", "EDGE_GAP"]},
        "Ledge": {"at": (LEDGE / 2, 0, PANEL_TOP + T + 0.5), "normal": (0, 0, 1), "params": ["LEDGE", "PANEL_TOP"]},
        "Tilted plate": {"at": (cx, 0, cz + 0.5), "normal": (math.sin(ANG), 0, math.cos(ANG)),
                         "params": ["TILT", "PLATE_L", "PATTERN"]},
        "Sleeve screws": {"at": (cx + PATTERN / 2 * math.cos(ANG), PATTERN / 2, cz - PATTERN / 2 * math.sin(ANG) + 0.5),
                          "normal": (math.sin(ANG), 0, math.cos(ANG)), "params": ["PATTERN", "SLEEVE_SCREW_D", "SLEEVE_HEAD_D"]},
        "Rib": {"at": ((EDGE_GAP - T) / 3, -W / 2 - 0.5, UNDER_REAR_Z - (EDGE_GAP - T) / 2), "normal": (0, -1, 0),
                "params": ["RIB_T", "EDGE_GAP"]},
        "Sleeve": {"at": (cx, 0, cz + SLEEVE_T + 0.5), "normal": (math.sin(ANG), 0, math.cos(ANG)),
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

    part = build()
    solid = part.val()
    assert solid.isValid(), "invalid solid"
    assert len(part.solids().vals()) == 1, "the part is not one solid"
    bb = solid.BoundingBox()
    cq.exporters.export(part, "mixer_riser.step")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)
    # Print orientation: on its side, the profile face on the bed (Y becomes Z).
    pr = part.rotate((0, 0, 0), (1, 0, 0), -90)
    pb = pr.val().BoundingBox()
    pr = pr.translate((-pb.xmin, -pb.ymin, -pb.zmin))
    pb = pr.val().BoundingBox()
    assert abs(pb.zlen - W) < 0.01, "the print should stand W tall"
    cq.exporters.export(pr, "mixer_riser.stl", tolerance=0.05, angularTolerance=0.1)
    print(f"use size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, volume {solid.Volume() / 1000:.1f} cm3")
    print(f"print size {pb.xlen:.1f} x {pb.ylen:.1f} x {pb.zlen:.1f} mm")
    print("wrote mixer_riser.step, mixer_riser.stl, labels.json")
