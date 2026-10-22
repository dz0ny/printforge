"""Slide-in sleeve for the Behringer Xenyx 1002SFX, made with CadQuery.

X is the slide axis along the mixer depth. The short side stays open.
Y is the mixer width. Z is the height, with the base plate at the bottom.
Run `uv run mixer_sleeve.py` to write the STEP and the STL, or
`uv run mixer_sleeve.py --serve` to adjust it in the browser.
"""
import cadquery as cq
from cadquery.selectors import BoxSelector

# 🎛️ Mixer body size in mm. Measure your mixer.
MIX_W = 189.0   # Width, left to right, on the open short side. The first print at 191 had 2 mm of play. [100:300]
MIX_D = 248.0   # Depth, front to back, along the slide axis. [100:400]
MIX_H = 31.0    # Body thickness with feet, without knobs. [10:80]
FOOT_H = 4.0    # Height of the rubber feet under the body; the body's edges sit this high. [0:10]
EDGE_R = 3.0    # Radius of the body's bottom edges. Measure it: the floor fillet must clear it. [0:10]

# 🖨️ Printer. The part prints flat on its back, so X and Y use lines and Z uses layers.
NOZZLE = 0.4
LINE = 0.45        # Line width, about 1.1 x the nozzle.
LAYER = 0.28

# 📐 Sleeve. Sizes in mm.
CLEAR = 0.5       # Gap on each side and at the end stop.
CLEAR_TOP = 2 * LAYER  # Gap above the body, under the lips, 2 layers.
SLEEVE_H = 213.5  # Total height with the end stop, below the mic hinge. [50:400]
WALL_H = 45.0     # Outer side wall height, floor to lip top. The 45 degree fill under the lips needs LIP mm above the mixer. [20:100]
WALL = 8 * LINE   # Side wall thickness, 8 lines. The first print broke at 6.
BASE = 11 * LAYER  # Base plate thickness, 11 layers.
FILLET = 6.0      # Fillet between the side walls and the base.
ROUND = 1.0       # Radius on the outer edges and lip tips.

# 🛑 End stop. The mixer rests on it.
END = 6 * LINE    # End stop thickness, 6 lines: 3 wall loops on each side, no infill.
END_H = 16.0      # End stop height, low for the curved mixer edge.
END_FILLET = 2.0  # Fillet at the end stop. Keep it small for the mixer corners.

# 🪝 Lips. They hold the mixer in, with a 45 degree fill underneath so the part prints flat.
LIP = 8.0         # Lip reach over the mixer edge.
LIP_T = 7 * LAYER  # Lip thickness, 7 layers.
LIP_FREE = 60.0   # No lip on this length at the open end.
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

IN_D = MIX_W + 2 * CLEAR
assert min(WALL, END, VENT_WEB) >= 2 * LINE, "a wall is thinner than two lines"
assert MARK_D >= 2.5 * NOZZLE and ROUND >= NOZZLE, "a feature is too small for the nozzle"
OUT_D = IN_D + 2 * WALL
OUT_H = WALL_H
IN_H = OUT_H - BASE - LIP_T  # Cavity height under the lips.
assert IN_H >= MIX_H + CLEAR_TOP, "the wall is too low for the mixer"
assert IN_H - LIP >= MIX_H + CLEAR_TOP, "the 45 degree fill under the lips would hit the mixer: raise WALL_H or lower LIP"
LEN = SLEEVE_H - END
assert LEN <= MIX_D + CLEAR, "sleeve is longer than the mixer"
TOTAL_LEN = LEN + END


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


def build():
    y0, y1 = WALL, WALL + IN_D
    zf, zt = BASE, BASE + IN_H

    part = box(0, 0, 0, TOTAL_LEN, OUT_D, OUT_H)
    part = part.cut(box(-1, y0, zf, LEN, y1, zt))
    part = part.cut(box(-1, y0 + LIP, zt - 1, LEN, y1 - LIP, OUT_H + 1))

    # Remove the lips near the open end and before the bottom slope.
    lip_end = TOTAL_LEN - (OUT_H - END_H) - LIP_SLOPE_GAP
    part = part.cut(box(-1, y0, zt, LIP_FREE, y1, OUT_H + 1))
    part = part.cut(box(lip_end, y0, zt, LEN, y1, OUT_H + 1))

    # Fill under each lip at 45 degrees.
    for y, s in ((y0, 1), (y1, -1)):
        tri = [(y, zt), (y + s * LIP, zt), (y, zt - LIP)]
        fill = cq.Workplane("YZ", origin=(LIP_FREE, 0, 0)).polyline(tri).close() \
            .extrude(lip_end - LIP_FREE)
        part = part.union(fill)

    # Lower the end stop. The walls and lips run down to it at 45 degrees.
    top = OUT_H + 10
    wedge = [(TOTAL_LEN + 1, END_H - 1), (TOTAL_LEN + 1, top), (TOTAL_LEN - (top - END_H), top)]
    cutter = cq.Workplane("XZ", origin=(0, OUT_D / 2, 0)).polyline(wedge).close() \
        .extrude(OUT_D / 2 + 1, both=True)
    part = part.cut(cutter)

    # Inner fillets: long floor edges, then the end stop edges.
    part = part.edges(sel(0, y0, zf, LEN, y0, zf) + sel(0, y1, zf, LEN, y1, zf)) \
        .fillet(FILLET)
    part = part.edges(sel(LEN, y0, zf, LEN, y0, zf + 5) + sel(LEN, y1, zf, LEN, y1, zf + 5)
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

    base = [e for e in edges if e.geomType() == "LINE"
            and any(all_pts(e, t) for t in (outer, wall_top, lip_ends, open_end))]
    base_ids = {e.hashCode() for e in base}
    extra = [e for e in edges if e.hashCode() not in base_ids and all_pts(e, slope)]
    # Try the whole set in one fillet. Only when that fails, add the slope
    # edges one by one and keep those that still work.
    keep, skipped = base + sorted(extra, key=lambda e: -e.Length()), 0
    try:
        part = part.newObject(keep).fillet(ROUND)
    except Exception:
        keep = list(base)
        for e in sorted(extra, key=lambda e: -e.Length()):
            try:
                part.newObject(keep + [e]).fillet(ROUND)
                keep.append(e)
            except Exception:
                skipped += 1
        part = part.newObject(keep).fillet(ROUND)
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
    body = box(x0, y0, BASE + FOOT_H, x1, y0 + MIX_W, BASE + MIX_H)
    if EDGE_R > 0:
        body = body.edges("|X").edges("<Z").fillet(EDGE_R)
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
                      ["WALL", "WALL_H", "FILLET", "SIDE_VENTS", "SIDE_HEX"]),
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
        "Floor": ((TOTAL_LEN * 0.3, OUT_D / 2, BASE + 0.5), (0, 0, 1),
                  ["BASE", "CLEAR", "MIX_W", "MIX_H"]),
        "Mixer": ((LEN - MIX_D / 2, OUT_D / 2, BASE + MIX_H + 0.5), (0, 0, 1),
                  ["MIX_W", "MIX_D", "MIX_H", "FOOT_H", "EDGE_R", "CLEAR", "CLEAR_TOP"]),
    }
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
        serve(__file__, port=port, open_browser="--open" in sys.argv)
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
