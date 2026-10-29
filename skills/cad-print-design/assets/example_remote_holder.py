"""Wall pocket for a TV remote, made with smlibpy.

Frame: X runs left to right, Y comes off the wall, Z points up.
The back plate is at y = 0.
The part prints standing, as it hangs, so the STL has the same orientation as the STEP.
Run `uv run remote_holder.py` for STEP, STL and labels.json.
Run `uv run remote_holder.py --serve` for the configurator.
"""
import json
import sys
from pathlib import Path

from smlibpy import (Align, Box, CounterSinkHole, Cylinder, Rectangle, X, export_step,
                     export_stl)

# 🎛️ Remote size in mm. Measure your remote.
REM_W = 50.0    # Width of the remote, across the buttons. [30:90].
REM_D = 22.0    # Thickness of the remote at its thickest point. [10:40].
REM_H = 180.0   # Length of the remote. [100:260].
REM_R = 6.0     # Corner radius of the remote, seen from above. [0:12].

# 🖨️ Printer. The part prints standing, so X and Y use lines and Z uses layers.
NOZZLE = 0.4    # Nozzle diameter.
LINE = 0.45     # Line width, about 1.1 x the nozzle.
LAYER = 0.2     # Layer height.

# 🧱 Shell around the remote.
FIT = 0.8       # Gap between the remote and the walls, per side. [0.2:2].
WALL_LINES = 6  # Wall thickness in lines. [3:12].
POCKET_H = 90.0 # Height of the pocket, with the floor. [40:200].
FLOOR_LAYERS = 15  # Floor thickness in layers. [8:30].

# 🪟 Front wall and thumb notch.
FRONT_H = 55.0  # Height of the front wall. [20:180].
NOTCH_W = 28.0  # Width of the thumb notch in the front wall. [10:60].

# 🔩 Mount tab with two countersunk screws.
TAB_H = 22.0    # Height of the mount tab above the pocket. [12:40].
SCREW_D = 4.0   # Diameter of the screw shank. [2.5:6].
HEAD_D = 8.0    # Diameter of the screw head. [5:12].
SCREW_GAP = 0.0 # Distance between the screws. Zero puts them near the edges. [0:120].

# 💧 Drain hole in the floor.
DRAIN_D = 8.0   # Diameter of the drain hole. Zero removes the hole. [0:20].

# Derived sizes. The configurator does not show these lines.
WALL = WALL_LINES * LINE
FLOOR = FLOOR_LAYERS * LAYER
IN_W = REM_W + 2 * FIT
IN_D = REM_D + 2 * FIT
OUT_W = IN_W + 2 * WALL
OUT_D = IN_D + 2 * WALL
R_IN = REM_R + FIT
R_OUT = R_IN + WALL
CY = OUT_D / 2  # Pocket centre along Y.
TOP = POCKET_H + TAB_H
SCREW_Z = POCKET_H + TAB_H / 2
SCREW_X = (SCREW_GAP / 2) if SCREW_GAP > 0 else (OUT_W / 2 - HEAD_D / 2 - 2 * WALL)


def check_rules():
    """Stop with a clear message when a value cannot work."""
    assert WALL >= 2 * LINE, f"raise WALL_LINES to at least 2, the wall is {WALL:.2f} mm"
    assert FRONT_H <= POCKET_H, f"lower FRONT_H to at most {POCKET_H:.1f} or raise POCKET_H"
    assert NOTCH_W < IN_W - 2, f"lower NOTCH_W to under {IN_W - 2:.1f}, the notch cuts the side walls"
    assert NOTCH_W / 2 < FRONT_H - FLOOR, f"lower NOTCH_W to under {2 * (FRONT_H - FLOOR):.1f}"
    assert HEAD_D < TAB_H - 2, f"raise TAB_H to at least {HEAD_D + 2:.1f} or use a smaller screw head"
    assert SCREW_X + HEAD_D / 2 < OUT_W / 2, f"lower SCREW_GAP to under {OUT_W - HEAD_D:.1f}"
    assert DRAIN_D == 0 or DRAIN_D < IN_W - 4, "lower DRAIN_D, the hole is wider than the floor"


def rounded_block(w, d, h, r):
    """Make a block with round vertical edges, centred on X and on the pocket along Y, from z = 0."""
    return Rectangle(w, d, fillet=r).extrude(h).translate(0, CY, 0)


def build():
    check_rules()
    shell = rounded_block(OUT_W, OUT_D, POCKET_H, R_OUT)
    shell -= rounded_block(IN_W, IN_D, POCKET_H + 10, R_IN).translate(0, 0, FLOOR)

    # 🪟 Cut the front wall down to FRONT_H, then cut the thumb notch from its top.
    # The cut starts where the corners start to curve, so the side walls end at full thickness.
    corner_y = OUT_D - R_OUT
    shell -= Box(OUT_W + 2, R_OUT + 1, POCKET_H, align=(Align.CENTER, Align.MIN, Align.MIN)).translate(
        0, corner_y, FRONT_H)
    shell -= Cylinder(NOTCH_W / 2, WALL + 2).rotate(X, 90).translate(0, OUT_D - WALL / 2, FRONT_H)

    # 🔩 The back plate continues above the pocket as the mount tab, with round top corners.
    tab = Box(OUT_W, WALL, TAB_H + R_OUT, align=(Align.CENTER, Align.MIN, Align.MIN))
    tab = tab.translate(0, 0, POCKET_H - R_OUT)
    top_corners = [e for e in tab.edges().parallel_to((0, 1, 0)) if e.center().z > TOP - 1]
    tab = tab.fillet(top_corners, 6)
    shell += tab
    for x in (-SCREW_X, SCREW_X):
        hole = CounterSinkHole(SCREW_D / 2 + 0.2, HEAD_D / 2 + 0.3, WALL + 2).rotate(X, -90)
        shell -= hole.translate(x, WALL, SCREW_Z)

    # 💧 Drain hole in the floor.
    if DRAIN_D > 0:
        shell -= Cylinder(DRAIN_D / 2, 3 * FLOOR).translate(0, CY, FLOOR / 2)
    return shell


def device():
    """Return the remote, on the floor of the pocket."""
    return rounded_block(REM_W, REM_D, REM_H, REM_R).translate(0, 0, FLOOR)


def keep_clear():
    """Return the volumes the part must not fill: a screwdriver path in front of each screw head."""
    return [Cylinder(HEAD_D / 2 + 1, 60).rotate(X, -90).translate(x, WALL + 30.5, SCREW_Z)
            for x in (-SCREW_X, SCREW_X)]


def features():
    """Return the named features with their anchor, outward normal and settings.

    Each anchor is 0.5 mm outside the surface.
    """
    return {
        "Back plate": {"at": (0, -0.5, POCKET_H / 2), "normal": (0, -1, 0), "params": ["WALL_LINES"]},
        "Left wall": {"at": (-OUT_W / 2 - 0.5, CY, POCKET_H / 2), "normal": (-1, 0, 0),
                      "params": ["WALL_LINES", "FIT", "REM_W"]},
        "Right wall": {"at": (OUT_W / 2 + 0.5, CY, POCKET_H / 2), "normal": (1, 0, 0),
                       "params": ["WALL_LINES", "FIT", "REM_W"]},
        "Front wall": {"at": (IN_W / 2 - 4, OUT_D + 0.5, FRONT_H / 2), "normal": (0, 1, 0),
                       "params": ["FRONT_H"]},
        "Thumb notch": {"at": (0, OUT_D + 0.5, FRONT_H - NOTCH_W / 2 - 0.5), "normal": (0, 1, 0),
                        "params": ["NOTCH_W"]},
        "Mount tab": {"at": (0, WALL + 0.5, TOP - 3), "normal": (0, 1, 0), "params": ["TAB_H"]},
        "Screw S1": {"at": (-SCREW_X, WALL + 0.5, SCREW_Z + HEAD_D / 2 + 1), "normal": (0, 1, 0),
                     "params": ["SCREW_D", "HEAD_D", "SCREW_GAP"]},
        "Screw S2": {"at": (SCREW_X, WALL + 0.5, SCREW_Z + HEAD_D / 2 + 1), "normal": (0, 1, 0),
                     "params": ["SCREW_D", "HEAD_D", "SCREW_GAP"]},
        "Floor drain": {"at": (0, CY, -0.5), "normal": (0, 0, -1), "params": ["DRAIN_D"]},
    }


def labels():
    out = {"_views": {"front": "Wall side", "back": "Open front", "top": "Open top"}}
    out.update({k: {"at": list(v["at"]), "normal": list(v["normal"])} for k, v in features().items()})
    return out


if __name__ == "__main__":
    if "--serve" in sys.argv:
        from printforge_configurator import serve
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
        host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"
        serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
        sys.exit()

    part = build()
    size = part.bbox().size
    print(f"valid {part.is_valid()}, solids {len(part.solids())}, "
          f"size {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm, volume {part.volume / 1000:.1f} cm3")
    assert part.is_valid() and len(part.solids()) == 1, "the part must be one valid solid"
    # Orientation test: the floor is on the bed, so more material is near z = 0 than near the top.
    slab = Box(400, 400, 5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    low = (part & slab).volume
    high = (part & slab.translate(0, 0, TOP - 5)).volume
    assert low > high, "the floor is not on the bed"
    assert max(size[0], size[1], size[2]) <= 256, "the part is larger than a 256 mm bed"

    stem = Path(__file__).with_suffix("")
    export_step(part, f"{stem}.step")
    export_stl(part, f"{stem}.stl", tolerance=0.02)
    Path("labels.json").write_text(json.dumps(labels(), indent=2))
    print(f"wrote {stem.name}.step, {stem.name}.stl, labels.json")
