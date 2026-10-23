"""Cocoa duster for latte art: press the button on top, cocoa falls through a sieve
and a slide-in stencil (a heart by default) onto the cup. Made with CadQuery.

Six printed parts and one bought spring:
  Stand    sits on the cup rim, holds the stencil in a slot and centres the body.
  Stencil  slides into the stand from the front, with a tab to pull it out.
  Body     the cocoa hopper, with the sieve printed into its floor.
  Lid      push-fit on the hopper, guides the plunger rod, seats the spring.
  Plunger  rod with a spoked agitator just above the sieve and a stop collar.
  Button   push-fit on the rod top; its skirt hides the spring and is the end stop.

Use frame: Z up, z = 0 is the cup rim (the stand's underside), the stencil tab
points to -Y (the front). One press moves the agitator STROKE mm down through the
cocoa and pushes a dose through the sieve; the spring lifts it back.
Run `uv run cocoa_dispenser.py` to write the STEP, the STLs and labels, or
`uv run cocoa_dispenser.py --serve` to adjust it in the browser.
"""
import math

import cadquery as cq

# ☕ Cup. Only for the ghost view; the stand rests on any rim wider than its window.
CUP_D = 90.0         # Cup rim outside diameter. [60:130]
CUP_H = 70.0         # Cup height below the rim. [30:120]

# 🖨️ Printer. Every part prints flat, so X and Y use lines and Z uses layers.
NOZZLE = 0.4
LINE = 0.45          # Line width, about 1.1 x the nozzle.
LAYER = 0.2

# 🫙 Body. The cocoa hopper with its locating flange.
HOP_D = 72.0         # Hopper outside diameter. [50:100]
HOP_H = 75.0         # Body height from the sieve face to the hopper rim. [40:130]
WALL = 5 * LINE      # Hopper wall, 5 lines. [1.2:4]
FLANGE_D = 98.0      # Flange diameter; it covers the stencil slot. [90:130]
FLANGE_T = 15 * LAYER  # Flange thickness. [1.6:6]

# 🕳️ Sieve. Printed into the body floor; holes are vertical in the print.
SIEVE_D = 60.0       # Sieve diameter, the dusting area. [30:66]
SIEVE_T = 6 * LAYER  # Sieve thickness. [0.8:2]
SIEVE_HOLE = 1.0     # Hole diameter. 1.0 is the smallest that stays open with a 0.4 nozzle. [0.8:2]
SIEVE_PITCH = 2.0    # Hole spacing, hex grid. Web = pitch - hole. [1.6:4]

# 🖼️ Stencil. Slides into the stand from the front.
STENCIL_D = 82.0     # Stencil disc diameter. [70:95]
STENCIL_T = 6 * LAYER  # Stencil thickness. [0.8:2]
HEART_W = 40.0       # Heart width. Must fit in the sieve area. [15:58]
TAB_W = 30.0         # Pull tab width. [15:50]
TAB_L = 18.0         # How far the tab sticks out past the stand. [8:40]
SLOT_PLAY = 0.4      # Slot height above the stencil thickness. [0.2:1]
SLOT_SIDE = 0.3      # Slot clearance per side around the disc. [0.1:0.6]

# 🍽️ Stand. Rests on the cup rim.
STAND_D = 105.0      # Stand outside diameter. [95:140]
STAND_BASE = 17 * LAYER  # Floor under the stencil. [2:6]
WINDOW_D = 64.0      # Opening under the stencil, over the cup. [40:80]
RIM_H = 3.0          # Locating rim around the body flange. [1:8]
RIM_PLAY = 0.5       # Clearance per side between the rim and the flange. [0.2:1.5]

# 🔘 Plunger, lid and button.
STROKE = 10.0        # Button travel. [4:20]
ROD_D = 6.0          # Rod diameter. [4:10]
ROD_PLAY = 0.3       # Clearance per side in the lid guide. [0.15:0.6]
AGI_D = 58.0         # Agitator diameter. [30:60]
AGI_T = 3.0          # Agitator thickness. [2:6]
AGI_GAP = 0.8        # Gap between the agitator and the sieve at full press. [0.4:3]
SPOKES = 4           # Agitator spokes. [3:8]
SPOKE_W = 3.0        # Spoke width. [1.5:6]
COLLAR_D = 11.0      # Stop collar under the lid hub. [8:16]
COLLAR_T = 3.0       # Collar height. [2:6]
LID_T = 12 * LAYER   # Lid plate thickness. [1.6:4]
LID_PLUG = 6.0       # Depth of the lid plug inside the hopper. [3:12]
LID_FIT = 0.2        # Clearance per side of the lid plug in the hopper. [0.05:0.5]
HUB_D = 13.0         # Lid guide hub diameter. [10:20]
SEAT_D = 11.0        # Spring seat in the lid top. [6:16]
SEAT_DEPTH = 8 * LAYER  # Spring seat depth. [0.8:3]
BTN_D = 26.0         # Button diameter. [16:40]
BTN_CAV_D = 14.0     # Button skirt inside, around the spring. [10:24]
BTN_CAV = 10.0       # Skirt depth. [5:20]
BTN_TOP = 8.0        # Solid cap above the skirt; holds the rod socket. [5:14]
SOCKET = 6.0         # Rod depth in the button. [3:10]
ROD_PRESS = 0.05     # Socket clearance per side; tight, add a drop of glue. [0:0.2]

# 🌀 Spring. Buy one: OD 9-10 mm, wire 0.6-0.8 mm, free length about 25 mm.
SPRING_OD = 10.0     # Spring outside diameter. [6:13]
SPRING_L = 25.0      # Spring free length. [15:40]
SPRING_SOLID = 8.0   # Spring fully compressed length. [4:14]

# Derived values.
HOP_ID = HOP_D - 2 * WALL
SLOT_H = STENCIL_T + SLOT_PLAY
STAND_TOP = STAND_BASE + SLOT_H
SLOT_R = STENCIL_D / 2 + SLOT_SIDE
BODY_Z = STAND_TOP                      # Body underside in the use frame.
HUB_BOT = HOP_H - LID_PLUG              # Lid hub underside, body frame.
LID_TOP = HOP_H + LID_T
AGI_Z = SIEVE_T + AGI_GAP + STROKE      # Agitator underside at rest, body frame.
BTN_Z = LID_TOP + STROKE                # Button skirt bottom at rest; full press lands on the lid.
CEIL_Z = BTN_Z + BTN_CAV
ROD_TOP = CEIL_Z + SOCKET
SPRING_REST = CEIL_Z - (LID_TOP - SEAT_DEPTH)
SPRING_PRESSED = SPRING_REST - STROKE
BED = 256.0

assert min(WALL, 4 * LINE) >= 2 * LINE, "a wall is thinner than two lines"


def check_design():
    assert SIEVE_HOLE >= 2 * NOZZLE, "sieve holes this small close up"
    assert SIEVE_PITCH - SIEVE_HOLE >= 2 * LINE, "sieve webs thinner than two lines"
    assert SIEVE_D < HOP_ID, "the sieve is wider than the hopper"
    assert HEART_W < SIEVE_D - 4, "the heart is wider than the sieve area"
    assert WINDOW_D < 2 * SLOT_R - 8, "the window leaves no ledge for the stencil"
    assert FLANGE_D > 2 * SLOT_R + 8, "the flange must cover the stencil slot"
    assert STAND_D / 2 - FLANGE_D / 2 - RIM_PLAY >= 2 * LINE + 1, "no room for the locating rim"
    assert AGI_D / 2 < SIEVE_D / 2 + AGI_GAP - 0.5, "the agitator hits the cone at full press"
    assert COLLAR_D < HOP_ID - 4 and COLLAR_D > ROD_D + 2 * ROD_PLAY + 2, "collar size"
    assert SPRING_OD + 1 <= BTN_CAV_D and SPRING_OD <= SEAT_D, "the spring does not fit"
    assert SPRING_REST < SPRING_L, "no spring preload: shorten BTN_CAV or use a longer spring"
    assert SPRING_PRESSED > SPRING_SOLID + 0.5, "the spring goes solid before the button lands"
    assert ROD_TOP - BTN_Z + BTN_TOP - SOCKET > 0


def cyl(d, h, z=0.0):
    return cq.Workplane("XY").workplane(offset=z).circle(d / 2).extrude(h)


def hex_points(r_max, pitch):
    pts = []
    rows = int(r_max / (pitch * math.sqrt(3) / 2)) + 1
    for j in range(-rows, rows + 1):
        y = j * pitch * math.sqrt(3) / 2
        off = pitch / 2 if j % 2 else 0.0
        for i in range(-int(r_max / pitch) - 2, int(r_max / pitch) + 3):
            x = i * pitch + off
            if math.hypot(x, y) <= r_max:
                pts.append((x, y))
    return pts


def heart_points(w, n=120):
    s = w / 32.0
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * s, y * s))
    ys = [p[1] for p in pts]
    mid = (max(ys) + min(ys)) / 2
    return [(x, y - mid) for x, y in pts]


# Parts, each in the use frame.

def stand():
    s = cyl(STAND_D, STAND_TOP).cut(cyl(WINDOW_D, STAND_TOP + 2, -1))
    slot = cyl(2 * SLOT_R, SLOT_H + 1, STAND_BASE).union(
        cq.Workplane("XY").workplane(offset=STAND_BASE)
        .center(0, -STAND_D / 2).rect(2 * SLOT_R, STAND_D).extrude(SLOT_H + 1))
    s = s.cut(slot)
    rim = cyl(STAND_D, RIM_H, STAND_TOP).cut(cyl(FLANGE_D + 2 * RIM_PLAY, RIM_H + 2, STAND_TOP - 1))
    gap = cq.Workplane("XY").workplane(offset=STAND_TOP - 1).center(0, -STAND_D / 2) \
        .rect(2 * SLOT_R, STAND_D).extrude(RIM_H + 2)
    return s.union(rim.cut(gap))


def stencil():
    reach = STAND_D / 2 + TAB_L
    st = cq.Workplane("XY").circle(STENCIL_D / 2).extrude(STENCIL_T).union(
        cq.Workplane("XY").center(0, -reach / 2).rect(TAB_W, reach).extrude(STENCIL_T))
    st = st.edges("|Z").edges(cq.selectors.BoxSelector((-TAB_W, -reach - 1, -1), (TAB_W, -reach + 1, 5))).fillet(4)
    st = st.cut(cyl(12, STENCIL_T + 2, -1).translate((0, -reach + 9, 0)))
    st = st.cut(cq.Workplane("XY").workplane(offset=-1).polyline(heart_points(HEART_W)).close().extrude(STENCIL_T + 2))
    return st.translate((0, 0, STAND_BASE))


def body():
    b = cyl(FLANGE_D, FLANGE_T).union(cyl(HOP_D, HOP_H))
    r0, r1 = SIEVE_D / 2, HOP_ID / 2
    cavity = cq.Workplane("XZ").polyline(
        [(0, SIEVE_T), (r0, SIEVE_T), (r1, SIEVE_T + (r1 - r0)), (r1, HOP_H + 1), (0, HOP_H + 1)]
    ).close().revolve(360, (0, 0, 0), (0, 1, 0))
    b = b.cut(cavity)
    pts = hex_points(r0 - SIEVE_HOLE, SIEVE_PITCH)
    if pts:
        holes = cq.Workplane("XY").workplane(offset=-1).pushPoints(pts).circle(SIEVE_HOLE / 2).extrude(SIEVE_T + 2)
        b = b.cut(holes)
    return b.translate((0, 0, BODY_Z))


def lid():
    plate = cyl(HOP_D, LID_T, HOP_H)
    plug_od = HOP_ID - 2 * LID_FIT
    plug = cyl(plug_od, LID_PLUG, HUB_BOT).cut(cyl(plug_od - 2 * 4 * LINE, LID_PLUG + 2, HUB_BOT - 1))
    hub = cyl(HUB_D, LID_PLUG, HUB_BOT)
    l = plate.union(plug).union(hub)
    l = l.cut(cyl(SEAT_D, SEAT_DEPTH + 1, LID_TOP - SEAT_DEPTH))
    l = l.cut(cyl(ROD_D + 2 * ROD_PLAY, LID_PLUG + LID_T + 2, HUB_BOT - 1))
    return l.translate((0, 0, BODY_Z))


def plunger(press=0.0):
    hub_d = ROD_D + 6
    agi = cyl(AGI_D, AGI_T).cut(cyl(AGI_D - 2 * 5 * LINE, AGI_T + 2, -1)).union(cyl(hub_d, AGI_T))
    for k in range(SPOKES):
        a = 180.0 * k / SPOKES
        agi = agi.union(cq.Workplane("XY").rect(AGI_D - 2, SPOKE_W).extrude(AGI_T).rotate((0, 0, 0), (0, 0, 1), a))
    rod = cyl(ROD_D, ROD_TOP - AGI_Z - AGI_T, AGI_T)
    # Collar with a 45 degree underside, so it prints without support.
    c0 = HUB_BOT - AGI_Z - COLLAR_T
    cone = (COLLAR_D - ROD_D) / 2
    collar = cq.Workplane("XZ").polyline(
        [(0, c0 - cone), (ROD_D / 2, c0 - cone), (COLLAR_D / 2, c0), (COLLAR_D / 2, c0 + COLLAR_T), (0, c0 + COLLAR_T)]
    ).close().revolve(360, (0, 0, 0), (0, 1, 0))
    p = agi.union(rod).union(collar)
    return p.translate((0, 0, BODY_Z + AGI_Z - press))


def button(press=0.0):
    b = cyl(BTN_D, BTN_CAV + BTN_TOP).cut(cyl(BTN_CAV_D, BTN_CAV + 1, -1))
    b = b.cut(cyl(ROD_D + 2 * ROD_PRESS, SOCKET + 0.5, BTN_CAV - 0.5))
    b = b.faces(">Z").edges().fillet(2.0)
    # A shallow finger dimple.
    b = b.cut(cq.Workplane("XY").sphere(30).translate((0, 0, BTN_CAV + BTN_TOP + 30 - 1.0)))
    return b.translate((0, 0, BODY_Z + BTN_Z - press))


def parts(press=0.0):
    return {"stand": stand(), "stencil": stencil(), "body": body(), "lid": lid(),
            "plunger": plunger(press), "button": button(press)}


def build():
    check_design()
    ps = parts()
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound([p.val() for p in ps.values()])])


def device():
    """The cup and the bought spring, for the ghost view."""
    cup = cyl(CUP_D, CUP_H, -CUP_H).cut(cyl(CUP_D - 6, CUP_H, -CUP_H + 4))
    spring = cyl(SPRING_OD, SPRING_REST, BODY_Z + LID_TOP - SEAT_DEPTH).cut(
        cyl(SPRING_OD - 1.6, SPRING_REST + 2, BODY_Z + LID_TOP - SEAT_DEPTH - 1))
    return cup.union(spring)


def features():
    reach = STAND_D / 2 + TAB_L
    zb = BODY_Z
    return {
        "Stand": {"at": (STAND_D / 2 + 0.5, 0, STAND_TOP / 2), "normal": (1, 0, 0),
                  "params": ["STAND_D", "STAND_BASE", "WINDOW_D"]},
        "Stencil slot": {"at": (0, -STAND_D / 2 - 0.5, STAND_BASE + SLOT_H / 2), "normal": (0, -1, 0),
                         "params": ["SLOT_PLAY", "SLOT_SIDE", "STENCIL_D"]},
        "Locating rim": {"at": (STAND_D / 2 - 1, 0, STAND_TOP + RIM_H + 0.5), "normal": (0, 0, 1),
                         "params": ["RIM_H", "RIM_PLAY"]},
        "Stencil tab": {"at": (0, -reach + 4, STAND_BASE + STENCIL_T + 0.5), "normal": (0, 0, 1),
                        "params": ["TAB_W", "TAB_L"]},
        "Heart": {"at": (0, 0, STAND_BASE - 0.5), "normal": (0, 0, -1), "params": ["HEART_W"]},
        "Flange": {"at": (FLANGE_D / 2 - 1, 0, zb + FLANGE_T + 0.5), "normal": (0, 0, 1),
                   "params": ["FLANGE_D", "FLANGE_T"]},
        "Hopper": {"at": (HOP_D / 2 + 0.5, 0, zb + HOP_H / 2), "normal": (1, 0, 0),
                   "params": ["HOP_D", "HOP_H", "WALL"]},
        "Lid": {"at": (HOP_D / 2 - 4, 0, zb + LID_TOP + 0.5), "normal": (0, 0, 1),
                "params": ["LID_T", "LID_PLUG", "LID_FIT"]},
        "Button": {"at": (0, 0, zb + BTN_Z + BTN_CAV + BTN_TOP + 0.5), "normal": (0, 0, 1),
                   "params": ["STROKE", "BTN_D", "BTN_CAV", "BTN_TOP"]},
        "Sieve": {"at": (SIEVE_D / 2 - 6, 0, zb - 0.5), "normal": (0, 0, -1),
                  "params": ["SIEVE_D", "SIEVE_HOLE", "SIEVE_PITCH"]},
    }


def labels():
    out = {"_views": {"front": "Front (tab side)", "top": "Button side", "bottom": "Cup side"}}
    for name, f in features().items():
        out[name] = {"at": list(f["at"]), "normal": list(f["normal"])}
    return out


# Print orientation per part: True = flip it upside down.
PRINT_FLIP = {"stand": False, "stencil": False, "body": False, "lid": True, "plunger": False, "button": True}


def for_print(p, flip):
    if flip:
        p = p.rotate((0, 0, 0), (1, 0, 0), 180)
    bb = p.val().BoundingBox()
    return p.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def slab_test(p, name, want_bottom_heavy=True):
    bb = p.val().BoundingBox()
    lo = p.intersect(cq.Workplane("XY").box(BED, BED, 1.0, centered=(False, False, False))).val().Volume()
    hi = p.intersect(cq.Workplane("XY").box(BED, BED, 1.0, centered=(False, False, False))
                     .translate((0, 0, bb.zmax - 1.0))).val().Volume()
    assert lo >= hi, f"{name}: more material at the top than on the bed, check the flip"
    assert bb.xlen <= BED and bb.ylen <= BED, f"{name}: does not fit the bed"


def merge_stls(items, out):
    """Join binary STLs into one, each moved by (dx, dy). Keeps the parts as separate shells."""
    import struct
    tris = []
    for path, (dx, dy) in items:
        data = open(path, "rb").read()
        n = struct.unpack("<I", data[80:84])[0]
        for i in range(n):
            o = 84 + i * 50
            v = list(struct.unpack("<12f", data[o:o + 48]))
            for k in (3, 6, 9):
                v[k] += dx
                v[k + 1] += dy
            tris.append(struct.pack("<12fH", *v, 0))
    with open(out, "wb") as f:
        f.write(b"cocoa dispenser plate".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        f.writelines(tris)


if __name__ == "__main__":
    import gc
    import json
    import sys
    if "--serve" in sys.argv:
        from printforge_configurator import serve
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8768
        host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"  # --lan: reachable from a phone.
        serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
        sys.exit()

    check_design()
    ps = parts()
    asm = build()
    cq.exporters.export(asm, "cocoa_dispenser.step")
    pressed = parts(press=STROKE)
    cq.exporters.export(cq.Workplane("XY").newObject([cq.Compound.makeCompound(
        [p.val() for p in pressed.values()])]), "cocoa_dispenser_pressed.step")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # Interference in the use frame, at rest and at full press.
    for state, pp in (("rest", ps), ("pressed", pressed)):
        names = list(pp)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                v = pp[a].intersect(pp[b]).val().Volume() if pp[a].intersect(pp[b]).vals() else 0.0
                assert v < 0.5, f"{state}: {a} and {b} overlap by {v:.2f} mm3"

    # Each part on its own, then one plate STL from those meshes, so the sieve
    # (about 700 holes) is tessellated only once: it needs ~2.7 GB as it is.
    layout = {"stand": (2, 2), "body": (112, 2), "stencil": (2, 112), "lid": (92, 112),
              "plunger": (170, 112), "button": (170, 176)}
    boxes = []
    for name, p in ps.items():
        solid = p.val()
        assert solid.isValid(), f"{name}: invalid solid"
        assert len(p.solids().vals()) == 1, f"{name}: not one solid"
        pr = for_print(p, PRINT_FLIP[name])
        slab_test(pr, name)
        cq.exporters.export(pr, f"{name}.stl", tolerance=0.05, angularTolerance=0.2)
        pb = pr.val().BoundingBox()
        x, y = layout[name]
        boxes.append((x, y, x + pb.xlen, y + pb.ylen))
        print(f"{name:8s} print {pb.xlen:6.1f} x {pb.ylen:6.1f} x {pb.zlen:6.1f} mm, {solid.Volume() / 1000:5.1f} cm3")
        gc.collect()
    for i, a in enumerate(boxes):
        assert a[2] <= BED and a[3] <= BED, "a part sticks off the bed"
        for b in boxes[i + 1:]:
            assert a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1], "parts overlap on the plate"
    merge_stls([(f"{n}.stl", layout[n]) for n in ps], "cocoa_dispenser_plate.stl")
    pmax = (max(b[2] for b in boxes), max(b[3] for b in boxes))
    bb = asm.val().BoundingBox()
    print(f"assembled {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm; plate {pmax[0]:.0f} x {pmax[1]:.0f} mm")
    print(f"spring {SPRING_REST:.1f} mm at rest, {SPRING_PRESSED:.1f} mm pressed (free {SPRING_L})")
    print("wrote cocoa_dispenser.step, cocoa_dispenser_pressed.step, 6 part STLs, cocoa_dispenser_plate.stl, labels.json")
