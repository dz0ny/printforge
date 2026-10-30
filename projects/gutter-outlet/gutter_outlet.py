"""Outlet funnel from a half-round NW 280 gutter to a round downpipe, made with smlibpy.

No joint has an inner lip, so water never climbs a step.
The gutter goes into the skirt, the floor only goes down, and the pipe goes over the spigot.
X is the gutter axis, +X into the gutter, Y across, Z up, open top at Z = 0.
Run `uv run gutter_outlet.py` to write the STEP and the STL.
Add `--serve` to adjust the part in the browser.
"""
import math

from smlibpy import (Align, Box, Circle, Cone, Cylinder, Line, Part, ThreePointArc, Wire, Y,
                     make_face, ruled, stitch)

# 🌧️ Gutter size in mm.
GUTTER_ID = 127.0      # Gutter inside diameter, NW 280 half-round. [80:200].
SHEET = 0.6            # Gutter sheet thickness. [0.4:2].
FIT = 0.4              # Clearance per side between the skirt and the gutter. [0:1.5].
BEAD_D = 16.0          # Diameter of the rolled front bead on the ghost, zero for none.
HOOK_D = 8.0           # Diameter of the rear hook on the ghost, zero for none.

# 🖨️ Printer. The part stands on the spigot tip, so the walls lie across the bed.
NOZZLE = 0.4
LINE = 0.48            # Line width, 1.2 x the nozzle.
LAYER = 0.2

# 🧱 Skirt over the gutter end.
WALL = 5 * LINE        # Spigot wall of 5 lines, so the bore stays wide.
FUNNEL_WALL = 8 * LINE  # Skirt and funnel wall of 8 lines, because they carry the water.
SKIRT_L = 25.0         # Skirt length over the gutter. [10:60].
SKIRT_TOP = -8.0       # Distance of the skirt top below the gutter top, clear of bead and hook. [-30:0].
ROUND = 1.0            # Radius on the free edges of the skirt.

# 🌀 Funnel from the gutter profile to the spigot.
FUNNEL_L = 50.0        # Funnel length, with sides of about 38 degrees. [30:120].
DROP = 3.0             # Drop of the floor along the funnel. [0:15].
LID_START = 12.0       # Open length of the funnel before the lid starts.

# 🪠 Downpipe, which slides over the spigot.
PIPE_OD = 58.0         # Outlet pipe outside diameter. [40:120].
PIPE_WALL = 1.0        # Outlet pipe wall, which sets the pipe inside diameter. [0.5:4].
PIPE_FIT = 0.3         # Clearance per side between the pipe and the spigot. [0:1].
SPIGOT_L = 40.0        # Spigot length into the pipe. [15:80].
COLLAR = 2.5           # Radial size of the pipe stop collar beyond the pipe OD.

R_SK_IN = GUTTER_ID / 2 + SHEET + FIT
R_SK_OUT = R_SK_IN + FUNNEL_WALL         # Skirt and funnel share one outer surface, with no step.
R_FN_OUT = R_SK_OUT
R_SP_OUT = (PIPE_OD - 2 * PIPE_WALL) / 2 - PIPE_FIT
R_SP_IN = R_SP_OUT - WALL
Z_FLOOR_B = -R_SK_IN - DROP
ZC = Z_FLOOR_B + R_SP_IN                 # Spigot axis, where the bore bottom meets the funnel floor.
R_COLLAR = PIPE_OD / 2 + COLLAR
X_B = -FUNNEL_L
X_TIP = X_B - SPIGOT_L
CONE_H = R_COLLAR - R_SP_OUT             # Cone of 45 degrees under the collar.


def check_design():
    """Check the design rules. The configurator shows a failed rule in its build log."""
    assert min(WALL, FUNNEL_WALL) >= 2 * LINE, "a wall is thinner than two lines"
    assert R_SP_IN > 5, "the spigot bore is too small for the wall"
    assert ZC - R_SP_IN <= -R_SK_IN + 1e-6, "the floor goes up along the flow: a lip would hold water"
    assert ROUND < FUNNEL_WALL / 2, "the round is too big for the skirt wall"


def xcyl(r, x0, length, zc=0.0, y=0.0):
    """Make a cylinder along +X from x0, with its axis at (y, zc)."""
    return Cylinder(r, length, align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(Y, 90).translate(x0, y, zc)


def xring(r_out, r_in, x0, length, zc=0.0, y=0.0):
    """Make a tube along +X from x0, with its axis at (y, zc)."""
    return (Circle(r_out) - Circle(r_in)).extrude(length).rotate(Y, 90).translate(x0, y, zc)


def d_edges(r, ztop, x):
    """Return the edges of the D profile at x: a half circle below z = 0 and a flat top at ztop.

    With ztop at 0, the D is a half disc with two edges.
    With a higher ztop, the D has four edges.
    """
    edges = [ThreePointArc((x, r, 0), (x, 0, -r), (x, -r, 0))]
    if ztop > 1e-6:
        edges += [Line((x, -r, 0), (x, -r, ztop)), Line((x, -r, ztop), (x, r, ztop)),
                  Line((x, r, ztop), (x, r, 0))]
    else:
        edges.append(Line((x, -r, 0), (x, r, 0)))
    return edges


def c_edges(r, zc, x, top_fractions):
    """Return a circle of radius r about (x, 0, zc) as one bottom half arc and some top arcs.

    The top half splits in the given fractions.
    Each edge of the D then gets a circle edge of the same share, so the funnel does not twist.
    For a D with a flat top of height ztop, the fractions are ztop, 2r and ztop.
    """
    def at(a):
        return (x, r * math.cos(a), zc + r * math.sin(a))

    edges = [ThreePointArc(at(0), at(-math.pi / 2), at(math.pi))]
    total = sum(top_fractions)
    a0 = math.pi
    for f in top_fractions:
        a1 = a0 - math.pi * f / total
        edges.append(ThreePointArc(at(a0), at((a0 + a1) / 2), at(a1)))
        a0 = a1
    return edges


def ruled_loft(d, c):
    """Make a solid from one ruled face per edge pair and two end caps.

    The loft function pairs the two profiles by itself, and it twisted this funnel.
    Ruled faces keep the pairs that the two edge lists give.
    """
    body = stitch([ruled(a, b) for a, b in zip(d, c)], make_face(Wire(d)), make_face(Wire(c)))
    assert isinstance(body, Part), "the funnel did not close into a solid"
    return body


def build():
    check_design()
    # Skirt: a half ring over the gutter, from x = 0 to SKIRT_L, open above SKIRT_TOP.
    skirt = xring(R_SK_OUT, R_SK_IN, 0, SKIRT_L)
    skirt -= Box(SKIRT_L + 2, 2 * R_SK_OUT + 4, 100, align=(Align.MIN, Align.CENTER, Align.MIN)).translate(
        -1, 0, SKIRT_TOP)
    if ROUND > 0:
        # Round the top cut and the arcs of the open end before the union.
        # Use one fillet call for all edges, because two calls fail at the corners.
        top = [e for e in skirt.edges() if abs(e.center().z - SKIRT_TOP) < 0.1
               and abs(e.point_at(0).x - e.point_at(1).x) > 5]
        end = [e for e in skirt.edges() if abs(e.center().x - SKIRT_L) < 0.1 and e.geom_type == "circle"]
        try:
            skirt = skirt.fillet(top + end, ROUND)
        except Exception as e:  # A failed round leaves the edges sharp, and the part stays whole.
            print(f"round skipped on the skirt: {e}")

    # Funnel: from the D of the gutter at x = 0 to the circle of the spigot at x = X_B.
    # The outer D is FUNNEL_WALL outside the inner D, and the small end is FUNNEL_WALL outside the bore.
    r_end = R_SP_IN + FUNNEL_WALL
    outer = ruled_loft(d_edges(R_FN_OUT, FUNNEL_WALL, 0.0),
                       c_edges(r_end, ZC, X_B, [FUNNEL_WALL, 2 * R_FN_OUT, FUNNEL_WALL]))
    # The cavity starts 1 mm inside the skirt and 0.3 mm wider than its bore, so no faces touch.
    # The gutter end rests on the shoulder where the cavity becomes narrower.
    inner = ruled_loft(d_edges(R_SK_IN + 0.3, 0.0, 1.0), c_edges(R_SP_IN, ZC, X_B - 0.01, [1.0]))
    # The first LID_START mm of the funnel stay open like the gutter, level with the skirt cut.
    if LID_START > 0:
        outer -= Box(LID_START + 1, 2 * R_FN_OUT + 4, 100, align=(Align.MIN, Align.CENTER, Align.MIN)).translate(
            -LID_START, 0, SKIRT_TOP)

    # Spigot and stop collar, with a cone of 45 degrees under the collar for printing.
    # The collar starts 0.5 mm inside the cone, away from the end face of the cavity.
    assert R_COLLAR >= r_end, "the collar is smaller than the end of the funnel"
    spigot = xcyl(R_SP_OUT, X_TIP, SPIGOT_L + 0.5, ZC)
    collar = xcyl(R_COLLAR, X_B - 0.5, 3.5, ZC)
    cone = Cone(R_SP_OUT, R_COLLAR, CONE_H, align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(Y, 90)
    cone = cone.translate(X_B - 0.5 - CONE_H, 0, ZC)

    part = outer + skirt + spigot + collar + cone
    # Cut the funnel cavity and the bore, which ends on the end face of the cavity.
    part -= inner
    part -= xcyl(R_SP_IN, X_TIP - 1, SPIGOT_L + 0.99, ZC)
    return part


def keep_clear():
    """Return the volumes that must stay empty for check_part.py: the water channel."""
    return [xcyl(R_SP_IN - 0.5, X_TIP - 1, SPIGOT_L + 1 + 8, ZC)]


def device():
    """Return the gutter end with its bead and hook, and the downpipe, for the ghost view."""
    r = GUTTER_ID / 2 + SHEET
    gutter = xring(r, GUTTER_ID / 2, 0, SKIRT_L + 30)
    gutter -= Box(SKIRT_L + 40, 2 * r + 4, 100, align=(Align.MIN, Align.CENTER, Align.MIN)).translate(-5, 0, 0)
    for d, side in ((BEAD_D, -1), (HOOK_D, 1)):
        if d > 0:
            # The bead rolls outward from the top edge of the sheet.
            gutter += xring(d / 2, max(d / 2 - SHEET, 0.1), 0, SKIRT_L + 30, y=side * (r + d / 2 - SHEET))
    pipe = xring(PIPE_OD / 2, PIPE_OD / 2 - PIPE_WALL, X_TIP - 30, SPIGOT_L + 30 - CONE_H - 0.5, ZC)
    return gutter + pipe


def features():
    """Return the named features with an anchor, an outward normal and the settings behind each."""
    return {
        "Skirt": {"at": (SKIRT_L / 2, 0, -R_SK_OUT - 0.5), "normal": (0, 0, -1),
                  "params": ["SKIRT_L", "SKIRT_TOP", "FIT", "WALL", "ROUND"]},
        "Funnel": {"at": (X_B / 2, -(R_FN_OUT + R_SP_IN + FUNNEL_WALL) / 2 - 0.5, (ZC - 20) / 2), "normal": (0, -1, 0),
                   "params": ["FUNNEL_L", "DROP", "FUNNEL_WALL", "LID_START"]},
        "Stop collar": {"at": (X_B + 1.5, 0, ZC + R_COLLAR + 0.5), "normal": (0, 0, 1),
                        "params": ["COLLAR", "PIPE_OD"]},
        "Spigot": {"at": (X_B - SPIGOT_L / 2, 0, ZC + R_SP_OUT + 0.5), "normal": (0, 0, 1),
                   "params": ["SPIGOT_L", "PIPE_OD", "PIPE_WALL", "PIPE_FIT"]},
        "Gutter": {"at": (SKIRT_L + 15, 0, -GUTTER_ID / 2 - SHEET - 0.5), "normal": (0, 0, -1),
                   "params": ["GUTTER_ID", "SHEET", "BEAD_D", "HOOK_D"]},
        "Pipe": {"at": (X_TIP - 15, 0, ZC + PIPE_OD / 2 + 0.5), "normal": (0, 0, 1),
                 "params": ["PIPE_OD", "PIPE_WALL"]},
    }


def labels():
    """Return the named anchors in the frame of the STEP, for render_views.py."""
    out = {"_views": {"left": "Outlet end", "right": "Gutter side", "top": "Top", "bottom": "Bottom"}}
    for name, f in features().items():
        if name in ("Gutter", "Pipe"):
            continue  # The gutter and the pipe are not part of the print.
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

    part = build()
    assert part.is_valid(), "invalid solid"
    assert len(part.solids()) == 1, "the part is not one solid"
    size = part.bbox().size
    export_step(part, "gutter_outlet.step")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # Print orientation: the spigot tip is on the bed, so -X points down.
    pr = part.rotate(Y, -90)   # This turns (x, y, z) into (-z, y, x).
    low = pr.bbox().min
    pr = pr.translate(-low.x, -low.y, -low.z)
    psize = pr.bbox().size

    def slab_width(z0):
        s = (pr & Box(400, 400, 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(0, 0, z0)).bbox().size
        return max(s.x, s.y)

    lo, hi = slab_width(0), slab_width(psize.z - 1)
    assert lo < hi, (lo, hi)   # The spigot is on the bed and the skirt is on top.
    assert max(psize.x, psize.y) < 256, "the part does not fit the bed"
    export_stl(pr, "gutter_outlet.stl", tolerance=0.05)

    print(f"use size {size.x:.1f} x {size.y:.1f} x {size.z:.1f} mm, volume {part.volume / 1000:.1f} cm3")
    print(f"print size {psize.x:.1f} x {psize.y:.1f} x {psize.z:.1f} mm")
    print(f"skirt ID {2 * R_SK_IN:.1f}, spigot OD {2 * R_SP_OUT:.1f} / ID {2 * R_SP_IN:.1f}, collar {2 * R_COLLAR:.1f}")
    print("wrote gutter_outlet.step, gutter_outlet.stl, labels.json")
