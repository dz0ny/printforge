"""Outlet funnel for a half-round gutter, NW/RS 280, to a round downpipe. Made with CadQuery.

No inner lip: every joint steps DOWN in the flow direction.
- The gutter goes INTO the skirt (the skirt sits on the outside of the gutter).
- The funnel narrows the gutter profile to the spigot; the floor goes down all the way.
- The pipe goes OVER the spigot (the pipe sits on the outside).

Design frame: X is the gutter axis (+X into the gutter, -X is the flow out),
Y across the gutter, Z up. The gutter axis lies on the X axis, open top at Z = 0.
Run `uv run gutter_outlet.py` to write the STEP and the STL, or
`uv run gutter_outlet.py --serve` to adjust it in the browser.
"""
import math

import cadquery as cq

# 🌧️ Gutter. Measure yours and correct these.
GUTTER_ID = 127.0      # Gutter inside diameter, NW 280 half-round. [80:200]
SHEET = 0.6            # Gutter sheet thickness. [0.4:2]
FIT = 0.4              # Clearance per side, skirt over the gutter. [0:1.5]

# 🖨️ Printer. The part stands on the spigot tip, so walls lie across the bed.
NOZZLE = 0.4
LINE = 0.48            # Line width, 1.2 x the nozzle.
LAYER = 0.2

# 🧱 Skirt and funnel. The skirt sits over the gutter end; the funnel narrows to the spigot.
WALL = 5 * LINE        # Wall of skirt, funnel and spigot, 5 lines.
SKIRT_L = 25.0         # Skirt length over the gutter. [10:60]
SKIRT_TOP = -8.0       # The skirt stops this far below the gutter top, clearing bead and hook. [-30:0]
FUNNEL_L = 50.0        # Funnel length; about 38 degree sides print without support. [30:120]
DROP = 3.0             # The floor goes down this much along the funnel. [0:15]

# 🪠 Pipe. The downpipe slides over the spigot.
PIPE_OD = 58.0         # Outlet pipe outside diameter. [40:120]
PIPE_WALL = 1.0        # Outlet pipe wall; pipe ID = OD - 2 x wall. Measure it. [0.5:4]
PIPE_FIT = 0.3         # Clearance per side, pipe over the spigot. [0:1]
SPIGOT_L = 40.0        # Spigot length into the pipe. [15:80]
COLLAR = 2.5           # Pipe stop collar, radial size beyond the pipe OD. [1:6]

R_SK_IN = GUTTER_ID / 2 + SHEET + FIT
R_SK_OUT = R_SK_IN + WALL
R_SP_OUT = (PIPE_OD - 2 * PIPE_WALL) / 2 - PIPE_FIT
R_SP_IN = R_SP_OUT - WALL
Z_FLOOR_B = -R_SK_IN - DROP
ZC = Z_FLOOR_B + R_SP_IN                 # Spigot axis: bore bottom = funnel floor end.
R_COLLAR = PIPE_OD / 2 + COLLAR
X_B = -FUNNEL_L
X_TIP = X_B - SPIGOT_L
assert WALL >= 2 * LINE, "the wall is thinner than two lines"
assert R_SP_IN > 5, "the spigot bore is too small for the wall"
assert ZC - R_SP_IN <= -R_SK_IN + 1e-6, "the floor goes up along the flow: a lip would hold water"


def d_wire(r, ztop, x):
    """D profile at x: a half circle of radius r below z = 0 and a flat top at ztop.

    Exact arcs and lines, so the loft has a few faces and the booleans stay fast.
    With ztop at 0 the D is a half disc with two edges, otherwise four.
    """
    V = cq.Vector
    edges = [cq.Edge.makeThreePointArc(V(x, r, 0), V(x, 0, -r), V(x, -r, 0))]
    if ztop > 1e-6:
        edges += [cq.Edge.makeLine(V(x, -r, 0), V(x, -r, ztop)),
                  cq.Edge.makeLine(V(x, -r, ztop), V(x, r, ztop)),
                  cq.Edge.makeLine(V(x, r, ztop), V(x, r, 0))]
    else:
        edges.append(cq.Edge.makeLine(V(x, -r, 0), V(x, r, 0)))
    return cq.Wire.assembleEdges(edges)


def c_wire(r, zc, x, top_fractions):
    """Circle of radius r about (x, 0, zc): one bottom half arc, then top arcs.

    The top half is split in the given fractions, so each edge of d_wire pairs
    with a circle edge of matching share and the ruled loft does not twist or
    bulge. For a D with a flat top of height ztop the fractions are the three
    edge lengths over the top path: ztop, 2r, ztop.
    """
    V = cq.Vector

    def at(a):
        return V(x, r * math.cos(a), zc + r * math.sin(a))

    edges = [cq.Edge.makeThreePointArc(at(0), at(-math.pi / 2), at(math.pi))]
    total = sum(top_fractions)
    a0 = math.pi
    for f in top_fractions:
        a1 = a0 - math.pi * f / total
        edges.append(cq.Edge.makeThreePointArc(at(a0), at((a0 + a1) / 2), at(a1)))
        a0 = a1
    return cq.Wire.assembleEdges(edges)


def loft(w1, w2):
    return cq.Workplane().add(cq.Solid.makeLoft([w1, w2], ruled=True))


def build():
    # Skirt: half ring over the gutter, x = 0 .. SKIRT_L.
    skirt = cq.Workplane("YZ").circle(R_SK_OUT).circle(R_SK_IN).extrude(SKIRT_L)
    skirt = skirt.cut(cq.Workplane("XY").box(SKIRT_L + 2, 2 * R_SK_OUT + 4, 100,
                                             centered=(False, True, False)).translate((-1, 0, SKIRT_TOP)))
    # Funnel: D (gutter profile) at x = 0 -> circle (spigot) at x = X_B.
    outer = loft(d_wire(R_SK_OUT, WALL, 0.0), c_wire(R_SP_OUT, ZC, X_B, [WALL, 2 * R_SK_OUT, WALL]))
    inner = loft(d_wire(R_SK_IN, 0.0, 0.01), c_wire(R_SP_IN, ZC, X_B - 0.01, [1.0]))
    # Spigot and stop collar, with a 45 degree cone under the collar for printing.
    spigot = cq.Workplane("YZ", origin=(X_TIP, 0, ZC)).circle(R_SP_OUT).extrude(SPIGOT_L + 0.5)
    collar = cq.Workplane("YZ", origin=(X_B - 0.01, 0, ZC)).circle(R_COLLAR).extrude(3.0)
    cone_h = R_COLLAR - R_SP_OUT
    cone = cq.Solid.makeCone(R_SP_OUT, R_COLLAR, cone_h, pnt=cq.Vector(X_B - cone_h, 0, ZC),
                             dir=cq.Vector(1, 0, 0))
    # Hollow the funnel first. Cutting the inner loft out of the assembled part
    # silently fails, because its end face coincides with the collar's face.
    funnel = outer.cut(inner)
    part = funnel.union(skirt).union(spigot).union(collar).union(cq.Workplane().add(cone))
    part = part.cut(cq.Workplane("YZ", origin=(X_TIP - 1, 0, ZC)).circle(R_SP_IN).extrude(SPIGOT_L + 1.2))
    return part


def device():
    """The gutter end and the downpipe in place, for the configurator's ghost view."""
    r = GUTTER_ID / 2 + SHEET
    gutter = cq.Workplane("YZ", origin=(-1, 0, 0)).circle(r).circle(GUTTER_ID / 2).extrude(SKIRT_L + 30)
    gutter = gutter.cut(cq.Workplane("XY").box(SKIRT_L + 40, 2 * r + 4, 100, centered=(False, True, False))
                        .translate((-5, 0, 0)))
    pipe = cq.Workplane("YZ", origin=(X_TIP - 30, 0, ZC)).circle(PIPE_OD / 2) \
        .circle(PIPE_OD / 2 - PIPE_WALL).extrude(SPIGOT_L + 30)
    return gutter.union(pipe)


def features():
    """Named features: an anchor on the surface, its outward normal, and the settings behind it."""
    return {
        "Skirt": {"at": (SKIRT_L / 2, 0, -R_SK_OUT - 0.5), "normal": (0, 0, -1),
                  "params": ["SKIRT_L", "SKIRT_TOP", "FIT", "WALL"]},
        "Funnel": {"at": (X_B / 2, -(R_SK_OUT + R_SP_OUT) / 2 - 0.5, (ZC - 20) / 2), "normal": (0, -1, 0),
                   "params": ["FUNNEL_L", "DROP", "WALL"]},
        "Stop collar": {"at": (X_B + 1.5, 0, ZC + R_COLLAR + 0.5), "normal": (0, 0, 1),
                        "params": ["COLLAR", "PIPE_OD"]},
        "Spigot": {"at": (X_B - SPIGOT_L / 2, 0, ZC + R_SP_OUT + 0.5), "normal": (0, 0, 1),
                   "params": ["SPIGOT_L", "PIPE_OD", "PIPE_WALL", "PIPE_FIT"]},
        "Gutter": {"at": (SKIRT_L + 15, 0, -GUTTER_ID / 2 - SHEET - 0.5), "normal": (0, 0, -1),
                   "params": ["GUTTER_ID", "SHEET"]},
        "Pipe": {"at": (X_TIP - 15, 0, ZC + PIPE_OD / 2 + 0.5), "normal": (0, 0, 1),
                 "params": ["PIPE_OD", "PIPE_WALL"]},
    }


def labels():
    """Named anchors in the use frame, the frame of the STEP, for render_views.py."""
    out = {"_views": {"left": "Outlet end", "right": "Gutter side", "top": "Top", "bottom": "Bottom"}}
    for name, f in features().items():
        if name in ("Gutter", "Pipe"):
            continue  # Not part of the printed part.
        out[name] = {"at": list(f["at"]), "normal": list(f["normal"])}
    return out


if __name__ == "__main__":
    import json
    import sys
    if "--serve" in sys.argv:
        from printforge_configurator import serve
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
        serve(__file__, port=port, open_browser="--open" in sys.argv)
        sys.exit()

    part = build()
    solid = part.val()
    assert solid.isValid(), "invalid solid"
    assert len(part.solids().vals()) == 1, "the part is not one solid"
    bb = solid.BoundingBox()
    cq.exporters.export(part, "gutter_outlet.step")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # Print orientation: spigot tip on the bed (-X -> down).
    pr = part.rotate((0, 0, 0), (0, 1, 0), -90)   # (x, y, z) -> (-z, y, x)
    pb = pr.val().BoundingBox()
    pr = pr.translate((-pb.xmin, -pb.ymin, -pb.zmin))
    pb = pr.val().BoundingBox()

    def slab_w(z0):
        b = pr.intersect(cq.Workplane("XY").box(400, 400, 1, centered=(True, True, False))
                         .translate((0, 0, z0))).val().BoundingBox()
        return max(b.xlen, b.ylen)

    lo, hi = slab_w(0), slab_w(pb.zmax - 1)
    assert lo < hi, (lo, hi)   # Spigot on the bed, skirt on top.
    assert max(pb.xlen, pb.ylen) < 256, "the part does not fit the bed"
    cq.exporters.export(pr, "gutter_outlet.stl", tolerance=0.05, angularTolerance=0.1)

    print(f"use size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, volume {solid.Volume() / 1000:.1f} cm3")
    print(f"print size {pb.xlen:.1f} x {pb.ylen:.1f} x {pb.zlen:.1f} mm")
    print(f"skirt ID {2 * R_SK_IN:.1f}, spigot OD {2 * R_SP_OUT:.1f} / ID {2 * R_SP_IN:.1f}, collar {2 * R_COLLAR:.1f}")
    print("wrote gutter_outlet.step, gutter_outlet.stl, labels.json")
