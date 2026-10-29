"""Slide-in sleeve for the Behringer Xenyx 1002SFX, made with smlibpy.

X is the slide axis along the mixer depth, and the short side stays open.
Y is the mixer width, and Z is the height, with the base plate at the bottom.
Run `uv run mixer_sleeve.py` to write the STEP and the STL.
Add `--serve` to adjust the part in the browser.
"""
import math

from smlibpy import (Align, Box, Circle, Cylinder, Line, Locations, Part, Plane, Polygon,
                     RegularPolygon, Spline, Wire, Y, make_face, ruled, stitch)

# 🎛️ Mixer body width in mm, which is barrel shaped.
MIX_W = 190.0   # Width at the widest point of the body. [100:300].
MIX_W_BOTTOM = 188.0  # Width at the bottom edge, which rests on the end stop. [100:300].
MIX_W_TOP = 189.0     # Width where the open end of the sleeve crosses the body, 211 mm up. [100:300].
MIX_W_AT = 110.0      # Distance from the bottom edge to the widest point. [0:250].

# 📏 Mixer body depth and height in mm.
MIX_D = 215.0   # Depth, front to back, along the slide axis. [100:400].
MIX_H = 26.0    # Body thickness with feet, without knobs. [10:80].
FOOT_H = 3.0    # Height of the rubber feet, which lift the edges of the body. [0:10].
EDGE_R = 3.0    # Radius of the bottom edges of the body, which the floor fillet must clear. [0:10].

# 🖨️ Printer. The part prints flat on its back, so X and Y use lines and Z uses layers.
NOZZLE = 0.4
LINE = 0.45        # Line width, about 1.1 x the nozzle.
LAYER = 0.28

# 📐 Sleeve size in mm.
CLEAR = 0.5       # Gap on each side and at the end stop.
CLEAR_TOP = 2 * LAYER  # Gap above the body, under the lips, 2 layers.
SLEEVE_H = 213.5  # Total height with the end stop, below the mic hinge. [50:400].
WALL_H = 34.0     # Outer side wall height, from the floor to the lip top. [20:100].

# 🧱 Walls and base.
WALL = 8 * LINE   # Side wall thickness of 8 lines, because the first print broke at 6.
BASE = 11 * LAYER  # Base plate thickness, 11 layers.
FILLET = 6.0      # Fillet between the side walls and the base.
ROUND = 1.0       # Radius on the outer edges and lip tips.

# 🛑 End stop, which the mixer rests on.
END = 6 * LINE    # End stop thickness of 6 lines: 3 wall loops on each side, no infill.
END_H = 16.0      # End stop height, low for the curved mixer edge.
END_FILLET = 2.0  # Fillet at the end stop, small for the mixer corners.
END_TRI = 20.0    # Width of the corner triangles that tie the stop to the walls, zero for a plain slope. [0:60].

# 🪝 Lips that hold the mixer in, with a fill underneath so the part prints flat.
LIP = 6.8         # Lip reach over the mixer edge, of which only 2.4 mm gets the fill at a 34 mm wall.
LIP_T = 7 * LAYER  # Lip thickness, 7 layers.
LIP_FREE = 80.0   # Length at the open end without a lip.
LIP_FILL_SLACK = 4.5  # Allowed depth shortfall of the lip fill, 1.0 for near 45 degrees, 4.5 for a ramp that may sag. [0:10].
LIP_SLOPE_GAP = 3.0  # Distance between the end of the lips and the bottom slope.

# 🔺 Gussets: 45 degree ribs on the outside of each wall, against side knocks.
GUSSETS = False    # Ribs on the outside of the walls, off for smooth walls.
GUSSET = 10.0      # Gusset reach out from the wall and height up the wall.
GUSSET_T = 6 * LINE  # Gusset thickness along the slide axis, 6 lines.
GUSSET_PITCH = 40.0  # Distance between gussets.
GUSSET_FIRST = 20.0  # Position of the first gusset from the open end.

# 🔩 Mount marks: a small mark in a solid pad at each mount point on the back.
HOLE_PATTERN = (80.0, 80.0)  # Spacing in X and Y of the back mount.
MARK_D = 3.0       # Mark diameter.
MARK_DEPTH = 3 * LAYER  # Mark depth into the back face, 3 layers.
PAD_R = 17.0       # Radius of the solid pad around each mark.

# 🕳️ Back vents: hexes with their points along the print Z axis.
VENT_HEX = 11.5     # Back vent hex size across the corners.
VENT_WEB = 6 * LINE  # Material between two hexes, 6 lines.
VENT_MARGIN = 8.0   # Solid border around each vent area.

# 🪟 Side and end vents.
SIDE_VENTS = False  # Side vents, off because they made the walls weak.
SIDE_HEX = 9.0      # Side vent hex size.
SIDE_MARGIN = 2.0   # Border on the short side of the side and end vents.

IN_D = MIX_W + 2 * CLEAR  # The sleeve fits the widest point, and the cavity follows the body.
BOW = (MIX_W - min(MIX_W_BOTTOM, MIX_W_TOP)) / 2  # Inward bow of each cavity wall.
assert min(WALL, END, VENT_WEB) >= 2 * LINE, "a wall is thinner than two lines"
assert MARK_D >= 2.5 * NOZZLE and ROUND >= NOZZLE, "a feature is too small for the nozzle"
OUT_D = IN_D + 2 * WALL
OUT_H = WALL_H
IN_H = OUT_H - BASE - LIP_T  # Cavity height under the lips.
LEN = SLEEVE_H - END
TOTAL_LEN = LEN + END
FILL = max(0.0, min(LIP, IN_H - MIX_H - CLEAR_TOP))  # Fill depth under the lips: the room above the mixer, up to LIP.


def box(x0, y0, z0, x1, y1, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0, align=Align.MIN).translate(x0, y0, z0)


E = 0.5  # Margin of the edge boxes. It is below the first def, so the configurator does not show it.


def edges_in(part, *boxes):
    """Return the edges of part whose centre is in one of the boxes (x0, y0, z0, x1, y1, z1)."""
    def inside(p, x0, y0, z0, x1, y1, z1):
        return x0 - E <= p.x <= x1 + E and y0 - E <= p.y <= y1 + E and z0 - E <= p.z <= z1 + E
    return [e for e in part.edges() if any(inside(e.center(), *b) for b in boxes)]


def hole_points():
    cx, cy = TOTAL_LEN / 2, OUT_D / 2
    px, py = HOLE_PATTERN
    return [(cx + sx * px / 2, cy + sy * py / 2) for sx in (-1, 1) for sy in (-1, 1)]


def gusset_points(lip_end):
    """Return the X centres of the gussets, from the open end up to the end of the lips."""
    pts, x = [], GUSSET_FIRST
    while GUSSETS and x + GUSSET_T / 2 <= lip_end:
        pts.append(x)
        x += GUSSET_PITCH
    return pts


def hex_grid(x0, x1, v0, v1, keep=(), size=VENT_HEX):
    """Return hex centres that fit fully in the area and stay clear of the keep circles."""
    flat = size * math.sqrt(3) / 2
    p = flat + VENT_WEB
    dx = p * math.sqrt(3) / 2
    pts = []
    i = 0
    while x0 + size / 2 + i * dx + size / 2 <= x1:
        x = x0 + size / 2 + i * dx
        j = 0
        while True:
            v = v0 + flat / 2 + j * p + (p / 2 if i % 2 else 0)
            if v + flat / 2 > v1:
                break
            if all(math.hypot(x - kx, v - kv) > kr + size / 2 for kx, kv, kr in keep):
                pts.append((x, v))
            j += 1
        i += 1
    return pts


def hex_prisms(points, size, plane, depth):
    """Return one hex prism per point, on plane, from depth/2 below it to depth/2 above it.

    A hex has a corner on the local +X axis of the plane.
    """
    below = plane.offset(-depth / 2)
    return [RegularPolygon(size / 2, 6).translate(u, v, 0).on(below).extrude(depth) for u, v in points]


def vents():
    """Return the vent cutters as a list of prisms, and print how many there are."""
    m = VENT_MARGIN
    keep = [(x, y, PAD_R) for x, y in hole_points()]
    back = hex_grid(m, LEN - m, WALL + FILLET + m, OUT_D - WALL - FILLET - m, keep)
    cut = hex_prisms(back, VENT_HEX, Plane.XY.offset(BASE / 2), BASE + 2)
    # Side and end vents stay between the floor fillet and the lip fill.
    # Their hex points go along Z, so they print without supports on the back.
    zs = (BASE + FILLET + SIDE_MARGIN, BASE + IN_H - LIP - SIDE_MARGIN)
    side = hex_grid(*zs, m, LEN - m, size=SIDE_HEX) if SIDE_VENTS else []
    for y in (WALL / 2, OUT_D - WALL / 2):
        plane = Plane(origin=(0, y, 0), x_dir=(0, 0, 1), z_dir=(0, 1, 0))
        cut += hex_prisms(side, SIDE_HEX, plane, WALL + 2)
    ys = (WALL + END_FILLET + m, OUT_D - WALL - END_FILLET - m)
    end = hex_grid(zs[0], min(zs[1], END_H - SIDE_MARGIN), *ys, size=SIDE_HEX)
    plane = Plane(origin=(LEN + END / 2, 0, 0), x_dir=(0, 0, 1), z_dir=(1, 0, 0))
    cut += hex_prisms([(z, -y) for z, y in end], SIDE_HEX, plane, END + 2)
    print(f"vents: back {len(back)}, each side {len(side)}, end stop {len(end)}")
    return cut


def on(v, x=None, z=None, tol=0.05):
    return (x is None or abs(v.x - x) < tol) and (z is None or abs(v.z - z) < tol)


def check_design():
    """Check the design rules. The configurator shows a failed rule in its build log."""
    assert IN_H >= MIX_H + CLEAR_TOP, "the wall is too low for the mixer"
    assert LIP - FILL <= LIP_FILL_SLACK, (
        f"the fill under the lips would be {LIP - FILL:.1f} mm shallower than the lip and too steep to print: "
        f"raise WALL_H to at least {BASE + MIX_H + CLEAR_TOP + LIP - LIP_FILL_SLACK + LIP_T:.1f}, lower LIP to "
        f"{FILL + LIP_FILL_SLACK:.1f}, or raise LIP_FILL_SLACK")
    assert LEN <= MIX_D + CLEAR, "sleeve is longer than the mixer"
    assert max(MIX_W_BOTTOM, MIX_W_TOP) <= MIX_W, "MIX_W must be the widest point of the body"
    assert 0 < MIX_W_AT < LEN, "MIX_W_AT must lie inside the sleeve"


def outline_edges(extra, x_open=-1.0, x_bottom=None, z=0.0):
    """Return the plan outline of the body, grown by extra on each side, as four edges at height z.

    The body has MIX_W_BOTTOM at the bottom edge and MIX_W at MIX_W_AT from it.
    It has MIX_W_TOP where the open end of the sleeve crosses it.
    A spline through the three half widths makes each side.
    """
    yc = WALL + IN_D / 2
    x_bottom = LEN - CLEAR if x_bottom is None else x_bottom
    x_wide = x_bottom - MIX_W_AT
    hb, hw, ht = MIX_W_BOTTOM / 2 + extra, MIX_W / 2 + extra, MIX_W_TOP / 2 + extra
    return [Spline((x_open, yc - ht, z), (x_wide, yc - hw, z), (x_bottom, yc - hb, z)),
            Line((x_bottom, yc - hb, z), (x_bottom, yc + hb, z)),
            Spline((x_bottom, yc + hb, z), (x_wide, yc + hw, z), (x_open, yc + ht, z)),
            Line((x_open, yc + ht, z), (x_open, yc - ht, z))]


def outline(extra, **kw):
    """Return the plan outline of the body, grown by extra on each side, as a face."""
    return make_face(Wire(outline_edges(extra, **kw)))


def round_edges(part, lip_end):
    """Round the outer edges and the wall tops, then each lip end and open end edge that rounds.

    The first group always rounds in one call.
    The kernel test for the small edges near the lip ends does not always give the same answer.
    Thus each of these edges gets its own fillet call on the current part.
    """
    zt = BASE + IN_H

    def outer(p):
        return p.z < 0.05 or p.y < 0.05 or p.y > OUT_D - 0.05 or p.x > TOTAL_LEN - 0.05

    def wall_top(p):
        return abs(p.z - OUT_H) < 0.05

    def slope(p):
        return abs(p.z - (END_H + TOTAL_LEN - p.x)) < 0.05

    def lip_ends(p):
        return (on(p, x=LIP_FREE) or on(p, x=lip_end)) and p.z > zt - LIP - 0.1

    def open_end(p):
        return on(p, x=0)

    def lines(p_, *tests):
        out = []
        for e in p_.edges():
            if e.geom_type != "line":
                continue
            q = (e.point_at(0), e.point_at(1), e.center())
            if any(all(t(p) for p in q) for t in tests):
                out.append(e)
        return out

    first = lines(part, outer, wall_top)
    try:
        part = part.fillet(first, ROUND)
        n = len(first)
    except Exception as e:  # A failed round leaves these edges sharp, and the part stays whole.
        print(f"outer edges stay sharp: {e}")
        n = 0
    sharp = set()
    while True:
        done = False
        for e in lines(part, open_end, lip_ends, slope):
            key = tuple(round(c, 2) for c in e.center())
            if key in sharp:
                continue
            try:
                nxt = part.fillet([e], ROUND)
            except Exception:
                nxt = None
            if nxt is not None and nxt.is_valid():
                part, done, n = nxt, True, n + 1
                break  # The edges change after each fillet, so look at the part again.
            sharp.add(key)
        if not done:
            break
    print(f"rounded {n} edges, {len(sharp)} edges stay sharp or are already smooth")
    return part


def build():
    check_design()
    y0, y1 = WALL, WALL + IN_D
    zf, zt = BASE, BASE + IN_H

    part = box(0, 0, 0, TOTAL_LEN, OUT_D, OUT_H)
    # The cavity follows the barrel shape of the body, CLEAR outside it, up to the end stop.
    part -= outline(CLEAR, x_bottom=LEN).extrude(zt - zf).translate(0, 0, zf)
    # The lip opening is the cavity outline LIP further in, so the lips follow the body too.
    part -= outline(CLEAR - LIP, x_bottom=LEN).extrude(OUT_H - zt + 2).translate(0, 0, zt - 1)

    # Remove the lips near the open end and before the bottom slope.
    lip_end = TOTAL_LEN - (OUT_H - END_H) - LIP_SLOPE_GAP
    part -= box(-1, y0, zt, LIP_FREE, y1, OUT_H + 1)
    part -= box(lip_end, y0, zt, LEN, y1, OUT_H + 1)

    # The fill under the lips is a slab of the cavity outline, FILL deep, minus a core.
    # The core goes from the lip edge at the top to the cavity wall at the bottom.
    # One ruled face per pair of outline edges makes the core, so it cannot twist.
    if FILL > 0:
        slab = outline(CLEAR, x_bottom=LEN).extrude(FILL).translate(0, 0, zt - FILL)
        low = outline_edges(CLEAR - LIP + FILL, x_bottom=LEN, z=zt - FILL)
        high = outline_edges(CLEAR - LIP, x_bottom=LEN, z=zt)
        core = stitch([ruled(a, b) for a, b in zip(low, high)], make_face(Wire(low)), make_face(Wire(high)))
        assert isinstance(core, Part), "the core under the lips did not close"
        part += (slab - core) & box(LIP_FREE, -1, zt - FILL - 1, lip_end, OUT_D + 1, zt + 1)

    top = OUT_H + 10
    if END_TRI > 0:
        # Lower the end stop in the middle only.
        # At each wall the stop keeps the full wall height and goes down to END_H over END_TRI.
        yb0, yb1 = y0 + BOW, y1 - BOW  # The inner face of the stop meets the walls here.
        prof = [(yb0, OUT_H), (yb0 + END_TRI, END_H), (yb1 - END_TRI, END_H), (yb1, OUT_H), (yb1, top), (yb0, top)]
        part -= Polygon(prof).on(Plane.YZ).extrude(END + 2).translate(LEN - 1, 0, 0)
    else:
        # Lower the end stop, and let the walls and lips go down to it at 45 degrees.
        wedge = [(TOTAL_LEN + 1, END_H - 1), (TOTAL_LEN + 1, top), (TOTAL_LEN - (top - END_H), top)]
        part -= Polygon(wedge).on(Plane.XZ).extrude(-(OUT_D + 2)).translate(0, -1, 0)

    # Inner fillets: the long floor edges, then the end stop edges.
    b = BOW + 0.5
    part = part.fillet(edges_in(part, (0, y0, zf, LEN, y0 + b, zf), (0, y1 - b, zf, LEN, y1, zf)), FILLET)
    part = part.fillet(edges_in(part, (LEN, y0, zf, LEN, y0 + b, zf + 5), (LEN, y1 - b, zf, LEN, y1, zf + 5),
                                (LEN, y0, zf, LEN, y1, zf)), END_FILLET)
    part = round_edges(part, lip_end)

    part -= Locations(*hole_points()) * Circle(MARK_D / 2).extrude(MARK_DEPTH)
    part -= vents()

    # Gussets go on last, after the rounding.
    # They go 1.5 mm into the wall, so the rounded outer edge leaves no gap behind them.
    t = 1.5
    for y, s in ((0, -1), (OUT_D, 1)):
        tri = [(y + s * GUSSET, 0), (y - s * t, 0), (y - s * t, GUSSET + t)]
        for x in gusset_points(lip_end):
            part += Polygon(tri).on(Plane.YZ).extrude(GUSSET_T).translate(x - GUSSET_T / 2, 0, 0)
    print(f"gussets: {len(gusset_points(lip_end))} per side")
    return part


def device():
    """Return the mixer as it sits in the sleeve: the body on its feet, with round bottom edges.

    The configurator draws it as a ghost.
    The checker makes sure that the floor fillets of the sleeve stay out of it.
    """
    y0, x1 = WALL + CLEAR, LEN - CLEAR  # The mixer rests CLEAR before the end stop.
    x0 = x1 - MIX_D
    z0 = BASE + FOOT_H
    body = outline(0.0, x_open=x0).extrude(MIX_H - FOOT_H).translate(0, 0, z0)
    if EDGE_R > 0:
        try:
            body = body.fillet([e for e in body.edges() if abs(e.center().z - z0) < 0.01], EDGE_R)
        except Exception:
            pass  # A fillet along the splines can fail, and the ghost then has square bottom edges.
    for fx in (x0 + 15, x1 - 15):
        for fy in (y0 + 15, y0 + MIX_W - 15):
            body += Cylinder(6, max(FOOT_H, 0.01), align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(fx, fy, BASE)
    return body


def features():
    """Return the named features with an anchor, an outward normal and the settings behind each.

    The configurator highlights these settings when you click the feature.
    The labels() function turns the anchors into the tags on the rendered views.
    """
    pts = hole_points()
    lip_end = TOTAL_LEN - (OUT_H - END_H) - LIP_SLOPE_GAP
    f = {
        "Back plate": ((TOTAL_LEN / 2, OUT_D / 2, -0.5), (0, 0, -1),
                       ["BASE", "VENT_HEX", "VENT_WEB", "VENT_MARGIN"]),
        "Mount mark M1": ((pts[0][0], pts[0][1], -0.5), (0, 0, -1),
                          ["MARK_D", "MARK_DEPTH", "PAD_R"]),
        "Left wall": ((TOTAL_LEN / 2, -0.5, OUT_H / 2), (0, -1, 0),
                      ["WALL", "WALL_H", "FILLET", "MIX_W", "MIX_W_BOTTOM", "MIX_W_TOP", "SIDE_VENTS", "SIDE_HEX"]),
        "Right wall": ((TOTAL_LEN / 2, OUT_D + 0.5, OUT_H / 2), (0, 1, 0),
                       ["WALL", "WALL_H", "FILLET", "SIDE_VENTS", "SIDE_HEX"]),
        "Open end": ((-0.5, WALL / 2, OUT_H / 2), (-1, 0, 0), ["SLEEVE_H", "LIP_FREE"]),
        "End stop": ((TOTAL_LEN + 0.5, OUT_D / 2, END_H / 2), (1, 0, 0),
                     ["END", "END_H", "END_FILLET", "CLEAR"]),
        "Left lip": (((LIP_FREE + lip_end) / 2, WALL + LIP / 2, OUT_H + 0.5), (0, 0, 1),
                     ["LIP", "LIP_T", "LIP_SLOPE_GAP", "CLEAR_TOP", "LIP_FILL_SLACK"]),
        "Right lip": (((LIP_FREE + lip_end) / 2, OUT_D - WALL - LIP / 2, OUT_H + 0.5), (0, 0, 1),
                      ["LIP", "LIP_T", "LIP_SLOPE_GAP", "CLEAR_TOP", "LIP_FILL_SLACK"]),
        "Lip-free zone": ((LIP_FREE / 2, WALL / 2, OUT_H + 0.5), (0, 0, 1), ["LIP_FREE"]),
        "Bottom slope": ((TOTAL_LEN - (OUT_H - END_H) / 2, WALL / 2, (OUT_H + END_H) / 2),
                         (0.7, 0, 0.7), ["END_H", "WALL_H", "LIP_SLOPE_GAP"]),
        "Corner triangle": ((TOTAL_LEN + 0.5, WALL + BOW + END_TRI / 3, END_H + (OUT_H - END_H) / 3),
                            (1, 0, 0), ["END_TRI", "END_H", "WALL_H"]),
        "Floor": ((TOTAL_LEN * 0.3, OUT_D / 2, BASE + 0.5), (0, 0, 1),
                  ["BASE", "CLEAR", "MIX_W", "MIX_H"]),
        "Mixer": ((LEN - MIX_D / 2, OUT_D / 2, BASE + MIX_H + 0.5), (0, 0, 1),
                  ["MIX_W", "MIX_W_BOTTOM", "MIX_W_TOP", "MIX_W_AT", "MIX_D", "MIX_H", "FOOT_H", "EDGE_R", "CLEAR", "CLEAR_TOP"]),
    }
    del f["Corner triangle" if END_TRI <= 0 else "Bottom slope"]
    if GUSSETS:
        f["Gusset"] = ((GUSSET_FIRST, -GUSSET / 2 - 0.3, GUSSET / 2 - 0.3), (0, -0.7, 0.7),
                       ["GUSSETS", "GUSSET", "GUSSET_T", "GUSSET_PITCH", "GUSSET_FIRST"])
    return {name: {"at": at, "normal": n, "params": params} for name, (at, n, params) in f.items()}


def labels(low):
    """Return the named anchors in the upright frame for render_views.py.

    The upright export turns (x, y, z) into (z, y, -x), then moves the corner low to the origin.
    """
    out = {"_views": {"left": "Mount face", "right": "Knob side", "top": "Open end",
                      "bottom": "End stop", "front": "Left wall", "back": "Right wall"}}
    for name, f in features().items():
        if name == "Mixer":
            continue  # The mixer is not part of the print.
        (x, y, z), (nx, ny, nz) = f["at"], f["normal"]
        out[name] = {"at": [z - low.x, y - low.y, -x - low.z], "normal": [nz, ny, -nx]}
    return out


def plot_sections(part, path):
    """Write four section views of the part to one PNG.

    They show the lip profile, a zoom on it, the plan and the end stop.
    """
    import io

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from smlibpy import render

    x = (LIP_FREE + LEN) / 2
    panels = [
        (f"Cross-section at x={x:.0f}", dict(view="right", section={"origin": (x, 0, 0), "normal": (1, 0, 0)})),
        ("Zoom: wall fillet, lip with its fill", dict(view="right", section={"origin": (x, 0, 0), "normal": (1, 0, 0)},
                                                      zoom=4, look_at=(x, 14, OUT_H / 2))),
        ("Plan at z=2: back vents and pads", dict(view="top", section={"origin": (0, 0, 2), "normal": (0, 0, 1)})),
        ("Zoom: end stop fillet", dict(view="front", section={"origin": (0, OUT_D / 2, 0), "normal": (0, -1, 0)},
                                       zoom=4, look_at=(TOTAL_LEN - 20, OUT_D / 2, OUT_H / 2))),
    ]
    fig, axs = plt.subplots(2, 2, figsize=(16, 10))
    for ax, (title, opts) in zip(axs.flat, panels):
        pic = render(part, size=(1000, 620), **opts)
        ax.imshow(plt.imread(io.BytesIO(bytes(pic)), format="png"))
        ax.set_title(title)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=80)


if __name__ == "__main__":
    import json
    import sys
    if "--serve" in sys.argv:
        from printforge_configurator import serve
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
        host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"  # Use --lan to open the page from a phone.
        serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
        sys.exit()

    from smlibpy import drawing_views, export_step, export_stl, export_svg

    part = build()
    assert part.is_valid(), "invalid solid"
    assert len(part.solids()) == 1, "the part is not one solid"
    size = part.bbox().size
    print(f"design size {size.x:.1f} x {size.y:.1f} x {size.z:.1f} mm, volume {part.volume / 1000:.0f} cm3")
    # The STEP stands upright, as mounted, with the open end up.
    upright = part.rotate(Y, 90)
    low = upright.bbox().min
    with open("labels.json", "w") as f:
        json.dump(labels(low), f, indent=1)
    upright = upright.translate(-low.x, -low.y, -low.z)
    usize = upright.bbox().size

    def slab(z):
        return (upright & Box(400, 400, 1, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(0, 0, z)).volume

    assert slab(1) > 3 * slab(usize.z - 2), "the end stop must be at the bottom"
    export_step(upright, "mixer_sleeve.step")
    # The STL lies flat on its back, which is the print orientation.
    plow = part.bbox().min
    export_stl(part.translate(-plow.x, -plow.y, -plow.z), "mixer_sleeve.stl", tolerance=0.02)
    print(f"upright size {usize.x:.1f} x {usize.y:.1f} x {usize.z:.1f} mm")
    export_svg(drawing_views(upright), "view.svg")
    plot_sections(part, "sections.png")
    print("wrote mixer_sleeve.step, mixer_sleeve.stl, view.svg, sections.png")
