"""Slide-in sleeve for the Behringer Xenyx 1002SFX, made with CadQuery.

X is the slide axis along the mixer depth. The short side stays open.
Y is the mixer width. Z is the height, with the base plate at the bottom.
Run `uv run mixer_sleeve.py` to write the STEP and the STL, or
`uv run mixer_sleeve.py --serve` to adjust it in the browser.
"""
import cadquery as cq
from cadquery.selectors import BoxSelector

# 🎛️ Mixer body size in mm. Measure your mixer.
MIX_W = 190.0   # Width at the widest point of the body; the housing is barrel shaped. [100:300]
MIX_W_BOTTOM = 188.0  # Width at the bottom edge, the one that rests on the end stop. Measure it. [100:300]
MIX_W_TOP = 189.0     # Width where the sleeve's open end crosses the body, 211 mm up from the bottom edge. Measure it. [100:300]
MIX_W_AT = 110.0      # Distance from the bottom edge to the widest point. [0:250]
MIX_D = 215.0   # Depth, front to back, along the slide axis. [100:400]
MIX_H = 26.0    # Body thickness with feet, without knobs. [10:80]
FOOT_H = 3.0    # Height of the rubber feet under the body; the body's edges sit this high. [0:10]
EDGE_R = 3.0    # Radius of the body's bottom edges. Measure it: the floor fillet must clear it. [0:10]

# 🖨️ Printer. The part prints flat on its back, so X and Y use lines and Z uses layers.
NOZZLE = 0.4
LINE = 0.45        # Line width, about 1.1 x the nozzle.
LAYER = 0.28

# 📐 Sleeve. Sizes in mm.
CLEAR = 0.5       # Gap on each side and at the end stop.
CLEAR_TOP = 2 * LAYER  # Gap above the body, under the lips, 2 layers.
SLEEVE_H = 213.5  # Total height with the end stop, below the mic hinge. [50:400]
WALL_H = 34.0     # Outer side wall height, floor to lip top. The 45 degree fill under the lips needs LIP mm above the mixer. [20:100]
WALL = 8 * LINE   # Side wall thickness, 8 lines. The first print broke at 6.
BASE = 11 * LAYER  # Base plate thickness, 11 layers.
FILLET = 6.0      # Fillet between the side walls and the base.
ROUND = 1.0       # Radius on the outer edges and lip tips.

# 🛑 End stop. The mixer rests on it.
END = 6 * LINE    # End stop thickness, 6 lines: 3 wall loops on each side, no infill.
END_H = 16.0      # End stop height, low for the curved mixer edge.
END_FILLET = 2.0  # Fillet at the end stop. Keep it small for the mixer corners.
END_TRI = 20.0    # Corner triangles: the end stop rises from END_H to the wall top over this width at each wall, so the stop and the walls brace each other. 0 for the plain bottom slope. [0:60]

# 🪝 Lips. They hold the mixer in, with a 45 degree fill underneath so the part prints flat.
LIP = 3.4         # Lip reach over the mixer edge. At a 36 mm wall this is the room for a 45 degree fill.
LIP_T = 7 * LAYER  # Lip thickness, 7 layers.
LIP_FREE = 80.0   # No lip on this length at the open end.
LIP_SLOPE_GAP = 3.0  # The lips stop this far before the bottom slope.

# 🧱 Gussets. Ribs on the outside of each wall. The part prints flat, so the wall to
# floor joint is only layer adhesion. A 45 degree rib spreads a side knock
# over many layers and still prints without supports.
GUSSETS = False    # Ribs on the outside of the walls. Off: the walls are smooth.
GUSSET = 10.0      # Gusset reach out from the wall and height up the wall.
GUSSET_T = 6 * LINE  # Gusset thickness along the slide axis, 6 lines.
GUSSET_PITCH = 40.0  # Distance between gussets.
GUSSET_FIRST = 20.0  # First gusset, measured from the open end.

# 🔩 Mount marks. Each mount point on the back gets a small mark in a solid pad.
HOLE_PATTERN = (80.0, 80.0)  # Spacing in X and Y of the back mount.
MARK_D = 3.0       # Mark diameter.
MARK_DEPTH = 3 * LAYER  # Mark depth into the back face, 3 layers.
PAD_R = 17.0       # Radius of the solid pad around each mark.

# 🕳️ Vents. Hexes with their points along the print Z axis.
VENT_HEX = 11.5     # Back vent hex size across the corners.
SIDE_HEX = 9.0      # Side vent hex size.
SIDE_VENTS = False  # The side vents weakened the walls. The back vents are enough.
VENT_WEB = 6 * LINE  # Material between two hexes, 6 lines.
VENT_MARGIN = 8.0   # Solid border around each vent area.
SIDE_MARGIN = 2.0   # Border on the short side of the side and end vents.

IN_D = MIX_W + 2 * CLEAR  # The sleeve is sized for the widest point; the cavity narrows to follow the body.
BOW = (MIX_W - min(MIX_W_BOTTOM, MIX_W_TOP)) / 2  # How far the cavity walls bow inward, per side.
assert min(WALL, END, VENT_WEB) >= 2 * LINE, "a wall is thinner than two lines"
assert MARK_D >= 2.5 * NOZZLE and ROUND >= NOZZLE, "a feature is too small for the nozzle"
OUT_D = IN_D + 2 * WALL
OUT_H = WALL_H
IN_H = OUT_H - BASE - LIP_T  # Cavity height under the lips.
LEN = SLEEVE_H - END
TOTAL_LEN = LEN + END
# The fill under each lip is as deep as the room above the mixer allows, up to
# LIP. It always spans the whole lip, so a shallower fill is a little steeper
# than 45 degrees; up to 1 mm less depth prints fine.
FILL = max(0.0, min(LIP, IN_H - MIX_H - CLEAR_TOP))


def box(x0, y0, z0, x1, y1, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False) \
        .translate((x0, y0, z0))


E = 0.5  # Selector box margin. Below the first def, so the configurator hides it.


def sel(x0, y0, z0, x1, y1, z1):
    return BoxSelector((x0 - E, y0 - E, z0 - E), (x1 + E, y1 + E, z1 + E))


def hole_points():
    cx, cy = TOTAL_LEN / 2, OUT_D / 2
    px, py = HOLE_PATTERN
    return [(cx + sx * px / 2, cy + sy * py / 2) for sx in (-1, 1) for sy in (-1, 1)]


def gusset_points(lip_end):
    """Return the X centres of the gussets, from the open end up to the lips' end."""
    pts, x = [], GUSSET_FIRST
    while GUSSETS and x + GUSSET_T / 2 <= lip_end:
        pts.append(x)
        x += GUSSET_PITCH
    return pts


def hex_grid(x0, x1, v0, v1, keep=(), size=VENT_HEX):
    """Return hex centres that fit fully in the area and stay clear of the keep circles."""
    import math
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


def vents():
    m = VENT_MARGIN
    keep = [(x, y, PAD_R) for x, y in hole_points()]
    back = hex_grid(m, LEN - m, WALL + FILLET + m, OUT_D - WALL - FILLET - m, keep)
    cut = cq.Workplane("XY").workplane(offset=-1).pushPoints(back) \
        .polygon(6, VENT_HEX).extrude(BASE + 2)
    # Side and end vents stay between the floor fillet and the lip fill.
    # Their hex points go along Z, so they print without supports on the back.
    zs = (BASE + FILLET + SIDE_MARGIN, BASE + IN_H - LIP - SIDE_MARGIN)
    side = hex_grid(*zs, m, LEN - m, size=SIDE_HEX) if SIDE_VENTS else []
    # An empty pushPoints() list puts one shape at the origin, so skip empty grids.
    for y in (WALL / 2, OUT_D - WALL / 2) if side else ():
        plane = cq.Plane(origin=(0, y, 0), xDir=(0, 0, 1), normal=(0, 1, 0))
        wp = cq.Workplane(plane).pushPoints(side)
        cut = cut.union(wp.polygon(6, SIDE_HEX).extrude(WALL / 2 + 1, both=True))
    ys = (WALL + END_FILLET + m, OUT_D - WALL - END_FILLET - m)
    end = hex_grid(zs[0], min(zs[1], END_H - SIDE_MARGIN), *ys, size=SIDE_HEX)
    if end:
        plane = cq.Plane(origin=(LEN + END / 2, 0, 0), xDir=(0, 0, 1), normal=(1, 0, 0))
        wp = cq.Workplane(plane).pushPoints([(z, -y) for z, y in end])
        cut = cut.union(wp.polygon(6, SIDE_HEX).extrude(END / 2 + 1, both=True))
    print(f"vents: back {len(back)}, each side {len(side)}, end stop {len(end)}")
    return cut


def on(v, x=None, z=None, tol=0.05):
    return (x is None or abs(v.x - x) < tol) and (z is None or abs(v.z - z) < tol)


def check_design():
    """Design rules. They run inside build(), so a bad value saved from the
    configurator shows up in its build log instead of stopping the script from starting."""
    assert IN_H >= MIX_H + CLEAR_TOP, "the wall is too low for the mixer"
    assert LIP - FILL <= 1.0, (
        f"the fill under the lips would be {LIP - FILL:.1f} mm shallower than the lip and too steep to print: "
        f"raise WALL_H to at least {BASE + MIX_H + CLEAR_TOP + LIP - 1.0 + LIP_T:.1f} or lower LIP to {FILL + 1.0:.1f}")
    assert LEN <= MIX_D + CLEAR, "sleeve is longer than the mixer"
    assert max(MIX_W_BOTTOM, MIX_W_TOP) <= MIX_W, "MIX_W must be the widest point of the body"
    assert 0 < MIX_W_AT < LEN, "MIX_W_AT must lie inside the sleeve"


def outline(extra, x_open=-1.0, x_bottom=None):
    """The body's plan outline grown by `extra` on each side, as a closed 2D wire in XY.

    The body is barrel shaped: MIX_W_BOTTOM at the bottom edge (end stop side),
    MIX_W at MIX_W_AT from it, MIX_W_TOP where the sleeve's open end crosses it.
    A spline through the three half widths on each side gives the sides.
    """
    yc = WALL + IN_D / 2
    x_bottom = LEN - CLEAR if x_bottom is None else x_bottom
    x_wide = x_bottom - MIX_W_AT
    hb, hw, ht = MIX_W_BOTTOM / 2 + extra, MIX_W / 2 + extra, MIX_W_TOP / 2 + extra
    wp = (cq.Workplane("XY").moveTo(x_open, yc - ht)
          .spline([(x_wide, yc - hw), (x_bottom, yc - hb)], includeCurrent=True)
          .lineTo(x_bottom, yc + hb)
          .spline([(x_wide, yc + hw), (x_open, yc + ht)], includeCurrent=True)
          .close())
    return wp


def build():
    check_design()
    y0, y1 = WALL, WALL + IN_D
    zf, zt = BASE, BASE + IN_H

    part = box(0, 0, 0, TOTAL_LEN, OUT_D, OUT_H)
    # The cavity follows the body's barrel shape, CLEAR outside it, up to the end stop.
    cavity = outline(CLEAR, x_bottom=LEN).extrude(zt - zf).translate((0, 0, zf))
    part = part.cut(cavity)
    # The lip opening is the cavity outline LIP further in, so the lips follow the body too.
    lip_cut = outline(CLEAR - LIP, x_bottom=LEN).extrude(OUT_H - zt + 2).translate((0, 0, zt - 1))
    part = part.cut(lip_cut)

    # Remove the lips near the open end and before the bottom slope.
    lip_end = TOTAL_LEN - (OUT_H - END_H) - LIP_SLOPE_GAP
    part = part.cut(box(-1, y0, zt, LIP_FREE, y1, OUT_H + 1))
    part = part.cut(box(lip_end, y0, zt, LEN, y1, OUT_H + 1))

    # Fill under the lips, following the body: a slab of the cavity's outline,
    # FILL deep under the lips, minus a loft from the lip edge at the top to the
    # cavity wall at the bottom. What is left is a 45 degree slope from the
    # lip edge down to the wall on both sides, only where the lips are.
    if FILL > 0:
        slab = outline(CLEAR, x_bottom=LEN).extrude(FILL).translate((0, 0, zt - FILL))
        w_top = outline(CLEAR - LIP, x_bottom=LEN).translate((0, 0, zt)).val()
        w_bot = outline(CLEAR - LIP + FILL, x_bottom=LEN).translate((0, 0, zt - FILL)).val()
        core = cq.Workplane().add(cq.Solid.makeLoft([w_bot, w_top], ruled=True))
        fill = slab.cut(core).intersect(box(LIP_FREE, -1, zt - FILL - 1, lip_end, OUT_D + 1, zt + 1))
        part = part.union(fill)

    top = OUT_H + 10
    if END_TRI > 0:
        # Lower the end stop in the middle only. At each wall it keeps the wall's full
        # height and runs down to END_H over END_TRI: a triangle tying stop and wall.
        yb0, yb1 = y0 + BOW, y1 - BOW  # The stop's inner face meets the walls here.
        prof = [(yb0, OUT_H), (yb0 + END_TRI, END_H), (yb1 - END_TRI, END_H), (yb1, OUT_H), (yb1, top), (yb0, top)]
        cutter = cq.Workplane("YZ", origin=(LEN - 1, 0, 0)).polyline(prof).close().extrude(END + 2)
        part = part.cut(cutter)
    else:
        # Lower the end stop. The walls and lips run down to it at 45 degrees.
        wedge = [(TOTAL_LEN + 1, END_H - 1), (TOTAL_LEN + 1, top), (TOTAL_LEN - (top - END_H), top)]
        cutter = cq.Workplane("XZ", origin=(0, OUT_D / 2, 0)).polyline(wedge).close() \
            .extrude(OUT_D / 2 + 1, both=True)
        part = part.cut(cutter)

    # Inner fillets: long floor edges, then the end stop edges.
    b = BOW + 0.5
    part = part.edges(sel(0, y0, zf, LEN, y0 + b, zf) + sel(0, y1 - b, zf, LEN, y1, zf)) \
        .fillet(FILLET)
    part = part.edges(sel(LEN, y0, zf, LEN, y0 + b, zf + 5) + sel(LEN, y1 - b, zf, LEN, y1, zf + 5)
                      + sel(LEN, y0, zf, LEN, y1, zf)).fillet(END_FILLET)

    # Round every other sharp edge in one fillet.
    def outer(p):
        return p.z < 0.05 or p.y < 0.05 or p.y > OUT_D - 0.05 or p.x > TOTAL_LEN - 0.05

    def slope(p):
        return abs(p.z - (END_H + TOTAL_LEN - p.x)) < 0.05

    def wall_top(p):
        return abs(p.z - OUT_H) < 0.05

    def lip_ends(p):
        return (on(p, x=LIP_FREE) or on(p, x=lip_end)) and p.z > zt - LIP - 0.1

    def open_end(p):
        return on(p, x=0)

    # Classify every edge once. The three points per edge are the only
    # geometry calls, and the hash set replaces pairwise isSame checks.
    edges = part.edges().vals()
    pts = {e.hashCode(): (e.startPoint(), e.endPoint(), e.Center()) for e in edges}

    def all_pts(e, test):
        return all(test(p) for p in pts[e.hashCode()])

    groups = {"outer": outer, "open end": open_end, "wall top": wall_top, "lip ends": lip_ends}
    picked = {name: [e for e in edges if e.geomType() == "LINE" and all_pts(e, t)]
              for name, t in groups.items()}
    seen = set()
    for name in picked:  # An edge belongs to the first group that claims it.
        picked[name] = [e for e in picked[name] if not (e.hashCode() in seen or seen.add(e.hashCode()))]
    extra = [e for e in edges if e.hashCode() not in seen and all_pts(e, slope)]

    def works(edge_list):
        try:
            part.newObject(edge_list).fillet(ROUND)
            return True
        except Exception:
            return False

    # Try everything in one fillet. Only when that fails, add the groups one
    # by one, then the slope edges one by one, and keep what still works.
    keep = [e for g in picked.values() for e in g] + sorted(extra, key=lambda e: -e.Length())
    skipped, sharp_groups = 0, []
    if not works(keep):
        keep = []
        for name, g in picked.items():
            if g and works(keep + g):
                keep += g
            elif g:
                sharp_groups.append(name)
        for e in sorted(extra, key=lambda e: -e.Length()):
            if works(keep + [e]):
                keep.append(e)
            else:
                skipped += 1
    if keep:
        part = part.newObject(keep).fillet(ROUND)
    if sharp_groups:
        print(f"edges stay sharp: {', '.join(sharp_groups)}")
    print(f"rounded {len(keep)} edges, {skipped} slope edges stay sharp")

    marks = cq.Workplane("XY").pushPoints(hole_points()).circle(MARK_D / 2).extrude(MARK_DEPTH)
    part = part.cut(marks).cut(vents())

    # Gussets go on last, after the rounding, and reach 1.5 mm into the wall
    # so the rounded outer edge leaves no gap behind them.
    t = 1.5
    for y, s in ((0, -1), (OUT_D, 1)):
        tri = [(y + s * GUSSET, 0), (y - s * t, 0), (y - s * t, GUSSET + t)]
        for x in gusset_points(lip_end):
            rib = cq.Workplane("YZ", origin=(x - GUSSET_T / 2, 0, 0)).polyline(tri).close() \
                .extrude(GUSSET_T)
            part = part.union(rib)
    print(f"gussets: {len(gusset_points(lip_end))} per side")
    return part


def device():
    """The mixer as it sits in the sleeve: the body on its feet, with rounded bottom edges.

    The configurator draws it as a ghost, and check_part.py makes sure the
    sleeve's floor fillets stay out of it.
    """
    y0, x1 = WALL + CLEAR, LEN - CLEAR  # The mixer rests CLEAR before the end stop.
    x0 = x1 - MIX_D
    body = outline(0.0, x_open=x0).extrude(MIX_H - FOOT_H).translate((0, 0, BASE + FOOT_H))
    if EDGE_R > 0:
        try:
            body = body.edges("<Z").fillet(EDGE_R)
        except Exception:
            pass  # A fillet along the splines can fail; the ghost then has square bottom edges.
    for fx in (x0 + 15, x1 - 15):
        for fy in (y0 + 15, y0 + MIX_W - 15):
            body = body.union(cq.Workplane("XY", origin=(fx, fy, BASE)).circle(6).extrude(max(FOOT_H, 0.01)))
    return body


def features():
    """Named features: an anchor on the surface, its outward normal, and the settings behind it.

    The configurator highlights these settings when the feature is clicked, and
    `labels()` turns the anchors into the tags on the rendered views.
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
                     ["LIP", "LIP_T", "LIP_SLOPE_GAP", "CLEAR_TOP"]),
        "Right lip": (((LIP_FREE + lip_end) / 2, OUT_D - WALL - LIP / 2, OUT_H + 0.5), (0, 0, 1),
                      ["LIP", "LIP_T", "LIP_SLOPE_GAP", "CLEAR_TOP"]),
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


def labels(rb):
    """Return named anchors in the upright frame for render_views.py."""
    # The upright export turns (x, y, z) into (z, y, -x) and then moves it to the origin.
    out = {"_views": {"left": "Mount face", "right": "Knob side", "top": "Open end",
                      "bottom": "End stop", "front": "Left wall", "back": "Right wall"}}
    for name, f in features().items():
        if name == "Mixer":
            continue  # The mixer is not part of the printed part.
        (x, y, z), (nx, ny, nz) = f["at"], f["normal"]
        out[name] = {"at": [z - rb.xmin, y - rb.ymin, -x - rb.zmin], "normal": [nz, ny, -nx]}
    return out


def plot_sections(part, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    def draw(ax, shape, ix, iy, title, lim=None):
        for e in shape.Edges():
            p = np.array([tuple(v) for v in e.positions(np.linspace(0, 1, 40))])
            ax.plot(p[:, ix], p[:, iy], "k", lw=0.8)
        ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.set_title(title)
        if lim:
            ax.set_xlim(*lim[:2]); ax.set_ylim(*lim[2:])

    x = (LIP_FREE + LEN) / 2
    solid = part.val()
    yz = solid.intersect(cq.Solid.makeBox(0.01, 400, 200, cq.Vector(x, -50, -50)))
    xy = solid.intersect(cq.Solid.makeBox(400, 400, 0.01, cq.Vector(-50, -50, 2)))
    xz = solid.intersect(cq.Solid.makeBox(400, 0.01, 200, cq.Vector(-50, OUT_D / 2, -50)))
    fig, axs = plt.subplots(2, 2, figsize=(16, 10))
    draw(axs[0, 0], yz, 1, 2, f"Cross-section at x={x:.0f}")
    draw(axs[0, 1], yz, 1, 2, "Zoom: wall fillet, lip with 45 degree fill", (-2, 40, -8, 62))
    draw(axs[1, 0], xy, 0, 1, "Plan at z=2 (back vents and pads)")
    draw(axs[1, 1], xz, 0, 2, "Zoom: end stop fillet", (TOTAL_LEN - 45, TOTAL_LEN + 2, -2, 62))
    plt.tight_layout()
    plt.savefig(path, dpi=80)


if __name__ == "__main__":
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
    bb = solid.BoundingBox()
    print(f"design size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, "
          f"volume {solid.Volume() / 1000:.0f} cm3")
    # The STEP stands upright, as mounted, with the open end up.
    upright = part.rotate((0, 0, 0), (0, 1, 0), 90)
    ub = upright.val().BoundingBox()
    import json
    with open("labels.json", "w") as f:
        json.dump(labels(ub), f, indent=1)
    upright = upright.translate((-ub.xmin, -ub.ymin, -ub.zmin))
    ub = upright.val().BoundingBox()
    slab = lambda z: upright.val().intersect(cq.Solid.makeBox(400, 400, 1, cq.Vector(-50, -50, z))).Volume()
    assert slab(1) > 3 * slab(ub.zmax - 2), "the end stop must be at the bottom"
    cq.exporters.export(upright, "mixer_sleeve.step")
    # The STL lies flat on its back, which is the print orientation.
    flat = part.translate((-bb.xmin, -bb.ymin, -bb.zmin))
    cq.exporters.export(flat, "mixer_sleeve.stl", tolerance=0.02, angularTolerance=0.1)
    print(f"upright size {ub.xlen:.1f} x {ub.ylen:.1f} x {ub.zlen:.1f} mm")
    cq.exporters.export(upright, "view.svg", opt={
        "projectionDir": (1.2, -1.0, 0.9), "showHidden": False, "width": 900, "height": 700})
    plot_sections(part, "sections.png")
    print("wrote mixer_sleeve.step, mixer_sleeve.stl, view.svg, sections.png")
