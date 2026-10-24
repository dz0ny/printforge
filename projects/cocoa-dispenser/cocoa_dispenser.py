"""Cocoa duster for latte art: press the button on top, a toothed rack on the rod
clicks past a striker tongue in the lid, and every click is one tap on the body.
The taps shake a fine, even dust of cocoa through the sieve floor onto a slide-in
stencil (a heart by default) on the cup. No shutter: the fine holes hold the
cocoa at rest, it bridges over them. Made with CadQuery, no bought parts.

Seven printed parts (or six and a bought metal spring, PRINT_SPRING = False):
  Stand    sits on the cup rim, holds the stencil in a slot, carries a short drop
           chamber so the hole pattern mixes into a cloud, and centres the body.
  Stencil  slides into the stand from the front; a lip makes it a tray for the
           spill, with a pour spout at the back to tip it into the hopper.
  Body     the cocoa hopper. Its floor is the sieve: a hex grid of fine holes over
           the whole floor, with a 45 degree cone up to the hopper bore.
  Rod      a square rod, straight, with a rack of triangular teeth on one face
           and a small flat foot that stirs the cocoa just above the sieve.
  Lid      push-fit on the hopper, square guide hole so the rack face stays put,
           spring seat, and the striker tongue: a thin finger in the hub that the
           rack teeth deflect and let snap back, one tap per tooth.
  Button   push-fit on the rod top; its skirt hides the spring and is the end stop.
  Spring   PETG wave spring around the rod.

Use frame: Z up, z = 0 is the cup rim (the stand's underside), the stencil tab
points to -Y (the front), the rack faces +X. One press is STROKE / RACK_PITCH taps
down and as many up. The dose is set by the hole size, the number of presses and
the amount of cocoa in the hopper.
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
FLANGE_D = 104.0     # Flange diameter; it covers the stencil slot. [90:130]
FLANGE_T = 15 * LAYER  # Flange thickness. [1.6:6]
FLANGE_R = 1.5       # Round on the flange's outer edges. [0:3]
GRIP_RIBS = 12       # Vertical grip ribs around the hopper, rounded rods half sunk into the wall. [0:24]
GRIP_D = 3.0         # Rib diameter. [2:5]
GRIP_PROUD = 1.8     # How far the ribs stand out from the hopper. [0.8:2.5]
GRIP_GAP = 8.0       # Rib ends this far from the flange and from the hopper rim. [4:20]

# 🕳️ Sieve. The body floor: fine holes over the whole floor, vertical in the print.
SIEVE_D = 60.0       # Sieve diameter; a 45 degree cone leads up to the hopper bore. [30:62]
SIEVE_T = 6 * LAYER  # Floor thickness. [0.8:2]
SIEVE_HOLE = 0.8     # Hole diameter: 0.8 for cocoa, 0.6 to 0.7 for cinnamon (0.2 nozzle or a test print). [0.6:1.2]
SIEVE_PITCH = 1.7    # Hole spacing, hex grid. Web = pitch - hole = 0.9, two lines at 0.45. [1.2:3]
SIEVE_SEPARATE = False  # True: the sieve is a drop-in disc with a tab, so hole sizes can be swapped. [0:1]
SIEVE_LEDGE = 3.0    # Ring ledge the drop-in disc rests on, when separate. [2:5]

# 🦷 Rod and rack. The tapper.
ROD_SQ = 6.0         # Rod square side. [5:9]
RACK_PITCH = 2.4     # Tooth pitch along the rod: one tap per tooth. Longer is a gentler flank for the spring to climb. [1:3]
RACK_DEPTH = 0.8     # Tooth depth into the rod face. [0.5:1.5]
AGI_FOOT = True      # A flat disc at the rod's bottom that stirs the cocoa above the sieve. [0:1]
FOOT_D = 20.0        # Agitator foot diameter. [10:30]
FOOT_T = 2.0         # Agitator foot thickness. [1:4]

# 🖼️ Stencil. Slides into the stand from the front.
STENCIL_D = 90.0     # Stencil disc diameter. [70:100]
STENCIL_T = 6 * LAYER  # Stencil thickness. [0.8:2]
STENCIL_LIP = 3.0    # Lip around the disc, so the spill stays on the stencil: a tray. [0:4]
SPOUT_W = 12.0       # Pour spout: a gap in the lip at the back, to tip the spill into the hopper. [0:20]
HEART_W = 52.0       # Heart width. [15:70]
TAB_W = 30.0         # Pull tab width. [15:50]
TAB_L = 18.0         # How far the tab sticks out past the stand. [8:40]
SLOT_PLAY = 0.4      # Slot height above the stencil thickness. [0.2:1]
SLOT_SIDE = 0.3      # Slot clearance per side around the disc. [0.1:0.6]

# 🍽️ Stand. Rests on the cup rim.
STAND_D = 112.0      # Stand outside diameter. [95:140]
STAND_BASE = 17 * LAYER  # Floor under the stencil. [2:6]
WINDOW_D = 70.0      # Opening under the stencil, over the cup. [40:85]
RIM_H = 3.0          # Locating rim around the body flange. [1:8]
RIM_PLAY = 0.5       # Clearance per side between the rim and the flange. [0.2:1.5]
STAND_R = 1.5        # Round on the stand's outer edges, top and bottom. [0:3]

# 🌫️ Drop chamber. The cocoa falls DROP_H so the hole pattern mixes into an even cloud.
DROP_H = 15.0        # Height of the chamber between the stencil and the sieve. [8:40]
CHAMBER_D = 80.0     # Chamber bore; the ring around it roofs the stencil slot with a 45 degree cone. [60:95]

# 🔘 Lid and button.
STROKE = 10.0        # Button travel. [4:20]
ROD_PLAY = 0.3       # Clearance per side of the rod in the lid's square guide. [0.15:0.6]
LID_T = 16 * LAYER   # Lid plate thickness. [1.6:5]
LID_PLUG = 6.0       # Depth of the lid plug inside the hopper. [3:12]
LID_FIT = 0.2        # Clearance per side of the lid plug in the hopper. [0.05:0.5]
LID_R = 1.0          # Round on the lid's top edge. [0:2]
HUB_D = 16.0         # Lid guide hub diameter; it holds the tongue's pocket with two lines of wall left. [10:20]
HUB_DOWN = 4.0       # Hub reach below the plug, into the hopper: a longer guide and room for the tongue. [0:12]
SEAT_DEPTH = 8 * LAYER  # Spring seat depth in the lid top. [0.8:3]
SPRING_PLAY = 1.0    # Clearance per side around the spring in the seat and the button skirt. [0.3:2]
BTN_WALL = 9 * LINE  # Button skirt wall. [1.2:6]
BTN_TOP = 8.0        # Solid cap above the skirt; holds the rod socket. [5:14]
SOCKET = 6.0         # Rod depth in the button. [3:10]
ROD_PRESS = 0.05     # Socket clearance per side; tight, add a drop of glue. [0:0.2]

# 👅 Striker tongue. A cantilever finger in the lid hub that the rack clicks past.
TONGUE_T = 2 * LINE  # Tongue thickness, 2 lines: thin enough to flex 0.5 mm. [0.6:1.8]
TONGUE_L = 8.0       # Tongue length from its root to the tip. [6:14]
TONGUE_W = 4.0       # Tongue width. [2:6]
TONGUE_BITE = 0.5    # How far the tip reaches into the teeth: the deflection per tooth. [0.3:1]
TONGUE_FLEX = 1.2    # Free room behind the tongue, so it can swing out. [0.8:2]
TONGUE_ROOT = 2.0    # Solid lid above the tongue's root. [1.2:4]
TOOTH_MU = 0.3       # Friction of the tongue tip on a tooth flank, PETG on PETG, for the return rule. [0.2:0.5]
PETG_E = 2000.0      # Printed PETG modulus, MPa, for the force estimates; tongue and spring both scale with it. [1500:2500]

# 🌀 Spring. A printed PETG wave spring, or a bought metal one.
PRINT_SPRING = True  # True: print the wave spring. False: buy a metal spring.
PRELOAD = 4.0        # Spring compression at rest: no rattle, and force to climb the last tooth on the way back. [0.5:6]
WS_D = 20.0          # Wave spring mean diameter. Larger is softer. [12:30]
WS_B = 4 * LINE      # Band width, radial, 4 lines. [1.2:4]
WS_T = 3 * LAYER     # Band thickness, vertical, 3 layers: half the rate of 4. [0.6:2]
WS_H = 4.0           # Wave height, crest to trough. [2:8]
WS_WAVES = 3         # Waves per ring. Fewer is softer but the underside overhang gets flatter. [2:6]
WS_RINGS = 8         # Number of wave rings. More is softer and longer. [4:16]
WS_END = 6 * LAYER   # Flat end ring thickness. [0.8:3]
WS_JOIN = 0.3        # Overlap where the rings touch, so they print as one part. [0.1:0.6]
METAL_OD = 10.0      # Bought spring outside diameter: OD 9-10, wire 0.6-0.8 mm. [6:13]
METAL_L = 25.0       # Bought spring free length. [15:40]
METAL_SOLID = 8.0    # Bought spring fully compressed length. [4:14]

# Derived values.
if PRINT_SPRING:
    SPRING_OD = WS_D + WS_B
    WS_PITCH = WS_H + WS_T - WS_JOIN
    SPRING_L = 2 * WS_END - WS_JOIN + WS_RINGS * WS_PITCH
    SPRING_SOLID = 2 * WS_END + WS_RINGS * WS_T
else:
    SPRING_OD, SPRING_L, SPRING_SOLID = METAL_OD, METAL_L, METAL_SOLID
ROD_D = ROD_SQ * math.sqrt(2)              # The rod's diagonal: what round bores must clear.
ROD_FOOT = STROKE + 2.0                    # Rod bottom above the sieve at rest: 2 mm above it at full press.
SEAT_D = SPRING_OD + 2 * SPRING_PLAY
BTN_CAV_D = SPRING_OD + 2 * SPRING_PLAY
BTN_D = BTN_CAV_D + 2 * BTN_WALL
BTN_CAV = SPRING_L - PRELOAD - STROKE - SEAT_DEPTH   # Skirt depth: the spring at rest fits exactly.
HOP_ID = HOP_D - 2 * WALL
SLOT_H = STENCIL_T + STENCIL_LIP + SLOT_PLAY
SLOT_TOP = STAND_BASE + SLOT_H
STAND_TOP = SLOT_TOP + DROP_H
SLOT_R = STENCIL_D / 2 + SLOT_SIDE
BODY_Z = STAND_TOP                      # Body underside in the use frame.
HUB_BOT = HOP_H - LID_PLUG              # Lid hub underside, body frame.
LID_TOP = HOP_H + LID_T
HUB_TOP = LID_TOP                       # The hub is flush with the lid top, inside the spring.
HUB_LOW = HUB_BOT - HUB_DOWN            # Hub underside, body frame.
ROD_BOT = SIEVE_T + ROD_FOOT            # Rod bottom at rest, body frame.
BTN_Z = LID_TOP + STROKE                # Button skirt bottom at rest; full press lands on the lid.
CEIL_Z = BTN_Z + BTN_CAV
ROD_TOP = CEIL_Z + SOCKET
SPRING_REST = CEIL_Z - (LID_TOP - SEAT_DEPTH)
SPRING_PRESSED = SPRING_REST - STROKE
TIP_Z = LID_TOP - TONGUE_ROOT - TONGUE_L  # Tongue tip height, body frame; the root is TONGUE_ROOT under the lid top.
RACK_Z0 = TIP_Z - ROD_BOT - 3.0         # Rack start, rod frame: the tip is on the rack over the whole stroke.
RACK_TEETH = int(round((STROKE + 6.0) / RACK_PITCH))  # Whole teeth over the stroke plus 3 mm each way.
RACK_L = RACK_TEETH * RACK_PITCH
BED = 256.0

assert min(WALL, 4 * LINE) >= 2 * LINE, "a wall is thinner than two lines"


def spring_rate():
    """Printed wave spring rate, N/mm: crest-to-crest estimate. Test it, printed parts vary."""
    return PETG_E * WS_B * WS_T ** 3 * WS_WAVES ** 4 / (2.4 * WS_D ** 3) / WS_RINGS


def return_budget():
    """Forces at the last tooth before rest: what the spring has, what the tongue costs.
    The tongue is a cantilever bent TONGUE_BITE; pushing its tip up a tooth flank of angle
    `flank` from the rod axis with friction costs tip_force * tan(flank + atan(mu))."""
    tip_force = 3 * PETG_E * (TONGUE_W * TONGUE_T ** 3 / 12) * TONGUE_BITE / TONGUE_L ** 3
    flank = math.atan(RACK_DEPTH / (RACK_PITCH / 2))
    climb = tip_force * math.tan(flank + math.atan(TOOTH_MU))
    have = spring_rate() * (PRELOAD + RACK_PITCH) if PRINT_SPRING else float("nan")
    return have, climb, math.degrees(flank)


def check_design():
    assert SIEVE_HOLE >= 2 * NOZZLE, "sieve holes this small close up"
    assert SIEVE_PITCH - SIEVE_HOLE >= 2 * LINE - 0.01, "sieve webs thinner than two lines"
    assert SIEVE_D < HOP_ID, "the sieve is wider than the hopper"
    assert HEART_W < SIEVE_D - 4, "the heart is wider than the sieve area"
    assert WINDOW_D < 2 * SLOT_R - 8, "the window leaves no ledge for the stencil"
    assert CHAMBER_D / 2 < SLOT_R, "the chamber bore is wider than the stencil slot"
    assert DROP_H > SLOT_R - CHAMBER_D / 2 + 2, "the chamber is too low for the 45 degree roof over the slot"
    assert DROP_H < SLOT_R, "the tapered roof would close before the top: lower DROP_H or widen the stencil"
    assert CHAMBER_D + 4 <= STAND_D, "the chamber bore is wider than the stand"
    assert SPOUT_W < STENCIL_D / 3
    assert FLANGE_D > 2 * SLOT_R + 8, "the flange must cover the stencil slot"
    assert STAND_D / 2 - FLANGE_D / 2 - RIM_PLAY >= 2 * LINE + 1, "no room for the locating rim"
    assert WS_D - WS_B > ROD_D + 1 if PRINT_SPRING else SPRING_OD - 1.6 > ROD_D + 1, "the spring does not clear the rod's diagonal"
    assert SPRING_OD + 1 <= BTN_CAV_D and SPRING_OD <= SEAT_D, "the spring does not fit"
    assert SPRING_REST < SPRING_L, "no spring preload: shorten BTN_CAV or use a longer spring"
    assert SPRING_PRESSED > SPRING_SOLID + 0.5, "the spring goes solid before the button lands"
    assert ROD_TOP - BTN_Z + BTN_TOP - SOCKET > 0
    assert BTN_CAV_D > ROD_D + 2, "the rod's diagonal does not fit the button cavity"
    assert BTN_CAV > 3, "the spring is too short for this stroke"
    assert SEAT_D < HOP_D - 6, "the spring seat is wider than the lid"
    assert SPRING_OD - 2 * (WS_B if PRINT_SPRING else 0.8) > ROD_D + 2, "the rod does not fit inside the spring"
    assert WS_D - WS_B > HUB_D + 1, "the hub does not fit inside the spring"
    if PRINT_SPRING:
        per_ring = (SPRING_L - SPRING_PRESSED) / WS_RINGS
        assert per_ring <= 0.5 * (WS_H - WS_JOIN), "each ring bends more than half its wave: add rings"
        assert WS_B >= 2 * LINE - 0.01 and WS_T >= 3 * LAYER - 0.01, "the wave band is too thin to print"
        have, climb, flank = return_budget()
        assert have >= 1.3 * climb, (f"the spring has {have:.1f} N at the last tooth but the tongue needs {climb:.1f} N to climb "
                                     f"a {flank:.0f} degree flank: raise PRELOAD or RACK_PITCH, or lower TONGUE_BITE")
    # The rack and the tongue.
    assert TONGUE_BITE < RACK_DEPTH, "the tongue bites deeper than the teeth"
    assert TONGUE_L >= 6, "a tongue under 6 mm is too stiff to flex"
    assert TONGUE_T >= 2 * LINE - 0.01, "the tongue is thinner than two lines"
    strain = 1.5 * TONGUE_BITE * TONGUE_T / TONGUE_L ** 2  # Cantilever tip deflection: max strain = 3 d t / (2 L^2).
    assert strain < 0.02, f"the tongue would strain {strain * 100:.1f}% per tooth: lengthen TONGUE_L or thin it"
    pocket_x = ROD_SQ / 2 + ROD_PLAY + TONGUE_T + TONGUE_FLEX
    pocket_y = TONGUE_W / 2 + 0.6
    hub_x_at_pocket_corner = math.sqrt(max((HUB_D / 2) ** 2 - pocket_y ** 2, 0.0))
    assert hub_x_at_pocket_corner - pocket_x >= 2 * LINE, "the hub wall outside the tongue's pocket is thinner than two lines: raise HUB_D"
    assert TONGUE_L + TONGUE_ROOT + 1 <= LID_TOP - HUB_LOW, "the tongue is longer than the hub: raise HUB_DOWN"
    assert HUB_LOW > ROD_BOT + (FOOT_T if AGI_FOOT else 0) + 2, "the hub reaches the rod's foot at rest"
    assert RACK_Z0 > (FOOT_T if AGI_FOOT else 0) + 1, "the rack runs into the rod's foot"
    assert RACK_Z0 + RACK_L < ROD_TOP - ROD_BOT - SOCKET - 1, "the rack runs into the button socket"
    assert ROD_FOOT - STROKE >= 1.5, "the rod's foot would hit the sieve at full press"
    if AGI_FOOT:
        assert FOOT_D < SIEVE_D - 4, "the foot is wider than the sieve"
    if SIEVE_SEPARATE:
        assert SIEVE_LEDGE >= 2.0, "the ledge is too narrow to hold the disc"


def cyl(d, h, z=0.0):
    return cq.Workplane("XY").workplane(offset=z).circle(d / 2).extrude(h)


# A disk cache of built parts, so a change to one setting rebuilds only the parts that
# use it. The key is the builder's source plus the values of the settings it names.
CACHE_DIR = __import__("pathlib").Path(__file__).resolve().parent / ".cache"
USE_CACHE = True
KEYS = {}


def part_key(name, deps, builder, args=()):
    import hashlib
    import inspect
    import json
    g = globals()
    payload = json.dumps([name, inspect.getsource(builder), [g[d] for d in deps], list(args), NOZZLE, LINE, LAYER],
                         sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def rounded(wp, pick, r, what):
    """Fillet the edges `pick` selects, only when the result is a valid solid; else leave them sharp."""
    try:
        out = pick(wp).fillet(r)
        if out.val().isValid() and len(out.solids().vals()) == 1:
            return out
        print(f"{what}: round left sharp, the fillet made an invalid solid")
    except Exception as e:
        print(f"{what}: round left sharp: {e}")
    return wp


def cached(name, deps, builder, *args):
    """Build a part through the cache: a .brep per key under .cache/."""
    key = part_key(name, deps, builder, args)
    KEYS[name] = key
    f = CACHE_DIR / f"{name}-{key}.brep"
    if USE_CACHE and f.exists():
        return cq.Workplane("XY").newObject([cq.Shape.importBrep(str(f))])
    shape = builder(*args)
    if USE_CACHE:
        CACHE_DIR.mkdir(exist_ok=True)
        shape.val().exportBrep(str(f))
    return shape


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


def rack_profile():
    """Sawtooth teeth as (x, z) points in the rod frame, cut into the +X face."""
    face = ROD_SQ / 2
    n = RACK_TEETH
    pts = [(face + 1.0, RACK_Z0)]
    for k in range(n):
        z = RACK_Z0 + k * RACK_PITCH
        pts += [(face + 0.001, z), (face - RACK_DEPTH, z + RACK_PITCH / 2)]
    pts += [(face + 0.001, RACK_Z0 + n * RACK_PITCH), (face + 1.0, RACK_Z0 + n * RACK_PITCH)]
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

def stadium(wp):
    """The stencil's way out as one outline: the round slot plus the straight channel to the front."""
    rs = SLOT_R
    return wp.moveTo(rs, 0).threePointArc((0, rs), (-rs, 0)).lineTo(-rs, -STAND_D).lineTo(rs, -STAND_D).close()


STAND_DEPS = ["STAND_D", "STAND_BASE", "WINDOW_D", "RIM_H", "RIM_PLAY", "STAND_R", "DROP_H", "CHAMBER_D",
              "STENCIL_D", "STENCIL_T", "STENCIL_LIP", "SLOT_PLAY", "SLOT_SIDE", "FLANGE_D"]


def stand():
    return cached("stand", STAND_DEPS, stand_build)


def stand_build():
    """Base ring with the stencil slot, the drop chamber above it, the locating rim.

    The slot's roof is the stadium outline tapered inward at 45 degrees as it rises, so
    the ceiling over the slot, over the channel and at the front mouth is one printable
    slope, and the chamber bore is cut through it."""
    rs, ro = SLOT_R, STAND_D / 2
    s = cyl(STAND_D, STAND_TOP).cut(cyl(WINDOW_D, STAND_TOP + 2, -1))
    s = s.cut(stadium(cq.Workplane("XY").workplane(offset=STAND_BASE)).extrude(SLOT_H))
    s = s.cut(stadium(cq.Workplane("XY").workplane(offset=SLOT_TOP - 0.01)).extrude(DROP_H + 2, taper=45))
    s = s.cut(cyl(CHAMBER_D, DROP_H + 2, SLOT_TOP - 0.01))
    rim = cyl(STAND_D, RIM_H, STAND_TOP).cut(cyl(FLANGE_D + 2 * RIM_PLAY, RIM_H + 2, STAND_TOP - 1))
    gap = cq.Workplane("XY").workplane(offset=STAND_TOP - 1).center(0, -STAND_D / 2) \
        .rect(2 * SLOT_R, STAND_D).extrude(RIM_H + 2)
    s = s.union(rim.cut(gap))
    # Where the channel's straight sides leave the round stand, the outer skin thins to a
    # feather; trim both horns flat, 2 mm behind the tangent point, the full height.
    y_t = math.sqrt(ro ** 2 - rs ** 2)
    for sx in (1, -1):
        horn = cq.Workplane("XY").workplane(offset=-1).center(sx * (rs + 10), -(y_t - 2) - 30) \
            .rect(20, 60).extrude(STAND_TOP + RIM_H + 2)
        s = s.cut(horn)
    if STAND_R > 0:  # The outer bottom edge, then the rim's outer top edge.
        big = cq.selectors.RadiusNthSelector(0, directionMax=True)
        s = rounded(s, lambda w: w.edges(cq.selectors.BoxSelector((-ro - 1, -ro - 1, -0.1), (ro + 1, ro + 1, 0.1)))
                    .edges("%CIRCLE").edges(big), STAND_R, "stand bottom")
        s = rounded(s, lambda w: w.edges(cq.selectors.BoxSelector((-ro - 1, -ro - 1, STAND_TOP + RIM_H - 0.1),
                                                                    (ro + 1, ro + 1, STAND_TOP + RIM_H + 0.1)))
                    .edges("%CIRCLE").edges(big), STAND_R, "stand top")
    return s


STENCIL_DEPS = ["STENCIL_D", "STENCIL_T", "STENCIL_LIP", "SPOUT_W", "HEART_W", "TAB_W", "TAB_L", "STAND_D", "STAND_BASE"]


def stencil():
    return cached("stencil", STENCIL_DEPS, stencil_build)


def stencil_build():
    reach = STAND_D / 2 + TAB_L
    st = cq.Workplane("XY").circle(STENCIL_D / 2).extrude(STENCIL_T).union(
        cq.Workplane("XY").center(0, -reach / 2).rect(TAB_W, reach).extrude(STENCIL_T))
    st = st.edges("|Z").edges(cq.selectors.BoxSelector((-TAB_W, -reach - 1, -1), (TAB_W, -reach + 1, 5))).fillet(4)
    if STENCIL_LIP > 0:
        lip = cq.Workplane("XY").workplane(offset=STENCIL_T).circle(STENCIL_D / 2).circle(STENCIL_D / 2 - 3 * LINE).extrude(STENCIL_LIP)
        if SPOUT_W > 0:  # Pour spout: a gap in the lip at the back (+Y).
            lip = lip.cut(cq.Workplane("XY").workplane(offset=STENCIL_T - 1).center(0, STENCIL_D / 2).rect(SPOUT_W, 10).extrude(STENCIL_LIP + 2))
        st = st.union(lip)
    st = st.cut(cyl(12, STENCIL_T + 2, -1).translate((0, -reach + 9, 0)))
    st = st.cut(cq.Workplane("XY").workplane(offset=-1).polyline(heart_points(HEART_W)).close().extrude(STENCIL_T + 2))
    return st.translate((0, 0, STAND_BASE))


def sieve_holes(r_max):
    """Hex grid of holes over the floor, each hole wholly inside r_max."""
    return [(x, y) for x, y in hex_points(r_max, SIEVE_PITCH) if math.hypot(x, y) <= r_max - SIEVE_HOLE / 2 - LINE]


FLOOR_DEPS = ["SIEVE_D", "SIEVE_T", "SIEVE_HOLE", "SIEVE_PITCH"]
SHELL_DEPS = ["HOP_D", "HOP_H", "WALL", "FLANGE_D", "FLANGE_T", "FLANGE_R", "GRIP_RIBS", "GRIP_D", "GRIP_PROUD", "GRIP_GAP",
              "SIEVE_D", "SIEVE_T", "SIEVE_SEPARATE", "SIEVE_LEDGE"]


def floor_build():
    """The sieve floor alone: a disc with the hex grid of holes, one radius of overlap into the shell."""
    r0 = SIEVE_D / 2
    f = cyl(SIEVE_D + 2.0, SIEVE_T)
    pts = sieve_holes(r0)
    return f.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints(pts).circle(SIEVE_HOLE / 2).extrude(SIEVE_T + 2))


def shell_build():
    """Hopper, flange, grip ribs and the cone, with the floor left open for the sieve disc."""
    b = cyl(FLANGE_D, FLANGE_T).union(cyl(HOP_D, HOP_H))
    if FLANGE_R > 0:
        b = rounded(b, lambda w: w.edges(cq.selectors.BoxSelector((-FLANGE_D, -FLANGE_D, -0.1), (FLANGE_D, FLANGE_D, FLANGE_T + 0.1)))
                    .edges("%CIRCLE").edges(cq.selectors.RadiusNthSelector(0, directionMax=True)), FLANGE_R, "flange")
    if GRIP_RIBS > 0:
        # Rounded vertical rods half sunk into the hopper wall: easy to hold, nothing to support.
        rc = HOP_D / 2 - GRIP_D / 2 + GRIP_PROUD
        z0, z1 = FLANGE_T + GRIP_GAP, HOP_H - GRIP_GAP
        for k in range(GRIP_RIBS):
            a = 2 * math.pi * k / GRIP_RIBS
            b = b.union(cyl(GRIP_D, z1 - z0, z0).translate((rc * math.cos(a), rc * math.sin(a), 0)))
    r0, r1 = SIEVE_D / 2, HOP_ID / 2
    cavity = cq.Workplane("XZ").polyline(
        [(0, SIEVE_T), (r0, SIEVE_T), (r1, SIEVE_T + (r1 - r0)), (r1, HOP_H + 1), (0, HOP_H + 1)]
    ).close().revolve(360, (0, 0, 0), (0, 1, 0))
    b = b.cut(cavity)
    if SIEVE_SEPARATE:
        # A ring ledge: the drop-in sieve disc rests on it, flush with the floor's top.
        b = b.cut(cyl(SIEVE_D - 2 * SIEVE_LEDGE, SIEVE_T + 2, -1))
        b = b.cut(cyl(SIEVE_D + 0.6, SIEVE_T, 0.001).cut(cyl(SIEVE_D - 2 * SIEVE_LEDGE - 1, SIEVE_T + 2, -1)))
    else:
        b = b.cut(cyl(SIEVE_D, SIEVE_T + 2, -1))  # The floor opening the sieve disc fills.
    return b


def body():
    """Hopper, flange and the sieve floor with the 45 degree cone up to the bore."""
    b = cached("shell", SHELL_DEPS, shell_build)
    if not SIEVE_SEPARATE:
        b = b.union(cached("floor", FLOOR_DEPS, floor_build))
    return b.translate((0, 0, BODY_Z))


def sieve():
    """The drop-in sieve disc, when SIEVE_SEPARATE: it rests on the ledge, a peg at the edge lifts it out."""
    d = SIEVE_D - 0.6
    s = cyl(d, SIEVE_T)
    pts = sieve_holes(d / 2 - SIEVE_LEDGE)
    s = s.cut(cq.Workplane("XY").workplane(offset=-1).pushPoints(pts).circle(SIEVE_HOLE / 2).extrude(SIEVE_T + 2))
    s = s.union(cyl(4.0, 8.0, SIEVE_T).translate((d / 2 - 3.0, 0, 0)))  # The lifting peg.
    return s.translate((0, 0, BODY_Z))


def tongue_solid():
    """The striker tongue in the body frame: a finger hanging from the hub top on the +X side,
    its body just outside the guide hole, and a 45 degree nub at the free end that reaches
    ROD_PLAY + TONGUE_BITE inward, so only the nub rides the teeth."""
    x_body = ROD_SQ / 2 + ROD_PLAY
    reach = ROD_PLAY + TONGUE_BITE
    finger = cq.Workplane("XY").workplane(offset=TIP_Z).center(x_body + TONGUE_T / 2, 0) \
        .rect(TONGUE_T, TONGUE_W).extrude(TONGUE_L + 0.5)
    nub = cq.Workplane("XZ", origin=(0, TONGUE_W / 2, 0)).polyline(
        [(x_body + 0.01, TIP_Z), (x_body - reach, TIP_Z + reach), (x_body + 0.01, TIP_Z + 2 * reach)]).close().extrude(TONGUE_W)
    return finger.union(nub)


def lid(with_tongue=True):
    plate = cyl(HOP_D, LID_T, HOP_H)
    plug_od = HOP_ID - 2 * LID_FIT
    plug = cyl(plug_od, LID_PLUG, HUB_BOT).cut(cyl(plug_od - 2 * 4 * LINE, LID_PLUG + 2, HUB_BOT - 1))
    hub = cyl(HUB_D, HUB_TOP - HUB_LOW, HUB_LOW)
    l = plate.union(plug).union(hub)
    l = l.cut(cyl(SEAT_D, SEAT_DEPTH + 1, LID_TOP - SEAT_DEPTH).cut(cyl(HUB_D, SEAT_DEPTH + 3, LID_TOP - SEAT_DEPTH - 1)))
    sq = ROD_SQ + 2 * ROD_PLAY
    l = l.cut(cq.Workplane("XY").workplane(offset=HUB_LOW - 1).rect(sq, sq).extrude(HUB_TOP - HUB_LOW + 2))
    # The pocket the tongue swings in: from the guide hole out through the tongue and its flex room,
    # a little wider than the tongue, from below the tip up to the root at the hub top.
    x_in, x_out = ROD_SQ / 2 + ROD_PLAY - 0.01, ROD_SQ / 2 + ROD_PLAY + TONGUE_T + TONGUE_FLEX
    pocket = cq.Workplane("XY").workplane(offset=TIP_Z - 1.0).center((x_in + x_out) / 2, 0) \
        .rect(x_out - x_in, TONGUE_W + 1.2).extrude(TONGUE_L + 1.0)  # Up to the root, TONGUE_ROOT under the top.
    l = l.cut(pocket)
    if with_tongue:
        l = l.union(tongue_solid())
    if LID_R > 0:
        l = rounded(l, lambda w: w.edges(cq.selectors.BoxSelector((-HOP_D, -HOP_D, LID_TOP - 0.1), (HOP_D, HOP_D, LID_TOP + 0.1)))
                    .edges("%CIRCLE").edges(cq.selectors.RadiusNthSelector(0, directionMax=True)), LID_R, "lid")
    return l.translate((0, 0, BODY_Z))


def rod(press=0.0):
    """Square rod, straight, with the rack on its +X face and the foot at the bottom."""
    r = cq.Workplane("XY").rect(ROD_SQ, ROD_SQ).extrude(ROD_TOP - ROD_BOT)
    teeth = cq.Workplane("XZ", origin=(0, ROD_SQ / 2 + 1, 0)).polyline(rack_profile()).close().extrude(ROD_SQ + 2)
    r = r.cut(teeth)
    if AGI_FOOT:
        r = r.union(cyl(FOOT_D, FOOT_T))
    return r.translate((0, 0, BODY_Z + ROD_BOT - press))


def button(press=0.0):
    b = cyl(BTN_D, BTN_CAV + BTN_TOP).cut(cyl(BTN_CAV_D, BTN_CAV + 1, -1))
    sq = ROD_SQ + 2 * ROD_PRESS
    b = b.cut(cq.Workplane("XY").workplane(offset=BTN_CAV - 0.5).rect(sq, sq).extrude(SOCKET + 0.5))
    b = b.faces(">Z").edges().fillet(2.0)
    # A shallow finger dimple.
    b = b.cut(cq.Workplane("XY").sphere(30).translate((0, 0, BTN_CAV + BTN_TOP + 30 - 1.0)))
    return b.translate((0, 0, BODY_Z + BTN_Z - press))


def wave_ring(base, sign, h=WS_H, n=72):
    """One wave ring: a band WS_B wide and WS_T thick whose height follows a cosine.
    Made as a ruled loft through radial rectangles; spline sweeps gave invalid booleans."""
    r0, r1 = WS_D / 2 - WS_B / 2, WS_D / 2 + WS_B / 2
    wires = []
    for k in range(n + 1):
        th = 2 * math.pi * (k % n) / n
        z = base + h / 2 * (1 + sign * math.cos(WS_WAVES * th))
        c, s = math.cos(th), math.sin(th)
        wires.append(cq.Wire.makePolygon(
            [cq.Vector(r * c, r * s, zz) for r, zz in ((r0, z), (r1, z), (r1, z + WS_T), (r0, z + WS_T))], close=True))
    return cq.Solid.makeLoft(wires, ruled=True)


def wave_spring(length=None):
    """The wave spring standing on z = 0. With length, the pitch shrinks to show it compressed."""
    length = SPRING_L if length is None else length
    pitch = (length - 2 * WS_END + WS_JOIN) / WS_RINGS
    h = pitch - WS_T + WS_JOIN  # A compressed spring has flatter waves.
    end = lambda z: cq.Workplane("XY").workplane(offset=z).circle(SPRING_OD / 2).circle(WS_D / 2 - WS_B / 2).extrude(WS_END).val()
    s = end(0.0)
    for i in range(WS_RINGS):
        s = s.fuse(wave_ring(WS_END - WS_JOIN + i * pitch, -1 if i % 2 == 0 else 1, h)).clean()
    s = s.fuse(end(length - WS_END)).clean()
    return cq.Workplane("XY").newObject([s])


SPRING_DEPS = ["WS_D", "WS_B", "WS_T", "WS_H", "WS_WAVES", "WS_RINGS", "WS_END", "WS_JOIN", "SPRING_OD"]


def spring(press=0.0):
    length = SPRING_REST - press
    return cached("spring", SPRING_DEPS, wave_spring, length).translate((0, 0, BODY_Z + LID_TOP - SEAT_DEPTH))


FIXED = {}


def parts(press=0.0):
    """All parts in the use frame. The parts the press does not move are built once per run."""
    for name, fn in (("stand", stand), ("stencil", stencil), ("body", body), ("lid", lid)):
        if name not in FIXED:
            FIXED[name] = fn()
    ps = {"stand": FIXED["stand"], "stencil": FIXED["stencil"], "body": FIXED["body"], "lid": FIXED["lid"],
          "rod": rod(press), "button": button(press)}
    if SIEVE_SEPARATE:
        ps["sieve"] = sieve()
    if PRINT_SPRING:
        ps["spring"] = spring(press)
    return ps


def build():
    check_design()
    ps = parts()
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound([p.val() for p in ps.values()])])


def device():
    """The cup, and the bought spring when there is one, for the ghost view."""
    cup = cyl(CUP_D, CUP_H, -CUP_H).cut(cyl(CUP_D - 6, CUP_H, -CUP_H + 4))
    if PRINT_SPRING:
        return cup
    spring = cyl(SPRING_OD, SPRING_REST, BODY_Z + LID_TOP - SEAT_DEPTH).cut(
        cyl(SPRING_OD - 1.6, SPRING_REST + 2, BODY_Z + LID_TOP - SEAT_DEPTH - 1))
    return cup.union(spring)


def features():
    reach = STAND_D / 2 + TAB_L
    zb = BODY_Z
    f = {
        "Stand": {"at": (STAND_D / 2 + 0.5, 0, SLOT_TOP / 2), "normal": (1, 0, 0),
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
                "params": ["LID_T", "LID_PLUG", "LID_FIT", "HUB_D", "HUB_DOWN"]},
        "Button": {"at": (0, 0, zb + BTN_Z + BTN_CAV + BTN_TOP + 0.5), "normal": (0, 0, 1),
                   "params": ["STROKE", "BTN_D", "BTN_CAV", "BTN_TOP"]},
        "Sieve": {"at": (SIEVE_D / 2 - 6, 0, zb - 0.5), "normal": (0, 0, -1),
                  "params": ["SIEVE_D", "SIEVE_HOLE", "SIEVE_PITCH", "SIEVE_SEPARATE"]},
        "Rack": {"at": (ROD_SQ / 2 + 0.5, 0, zb + ROD_BOT + RACK_Z0 + RACK_L / 2), "normal": (1, 0, 0),
                 "params": ["RACK_PITCH", "RACK_DEPTH", "STROKE"]},
        "Rod": {"at": (-ROD_SQ / 2 - 0.5, 0, zb + HUB_BOT - 8), "normal": (-1, 0, 0),
                "params": ["ROD_SQ", "STROKE", "ROD_PLAY"]},
        "Striker tongue": {"at": (ROD_SQ / 2 + ROD_PLAY + TONGUE_T + 0.3, 0, zb + TIP_Z + TONGUE_L / 2), "normal": (1, 0, 0),
                           "params": ["TONGUE_T", "TONGUE_L", "TONGUE_W", "TONGUE_BITE", "TONGUE_FLEX", "TONGUE_ROOT"]},
        "Stencil lip": {"at": (STENCIL_D / 2 - 1, 0, STAND_BASE + STENCIL_T + STENCIL_LIP + 0.5), "normal": (0, 0, 1),
                        "params": ["STENCIL_LIP", "SPOUT_W"]},
        "Drop chamber": {"at": (CHAMBER_D / 2 - 0.5, 0, STAND_TOP - 3), "normal": (-1, 0, 0),
                         "params": ["DROP_H", "CHAMBER_D"]},
        "Spring": {"at": (SPRING_OD / 2 + 0.5, 0, zb + LID_TOP + STROKE / 2), "normal": (1, 0, 0),
                   "params": ["PRINT_SPRING", "WS_D", "WS_T", "WS_H", "WS_WAVES", "WS_RINGS"]},
    }
    if AGI_FOOT:
        f["Agitator foot"] = {"at": (FOOT_D / 2 + 0.5, 0, zb + ROD_BOT + FOOT_T / 2), "normal": (1, 0, 0),
                              "params": ["AGI_FOOT", "FOOT_D", "FOOT_T"]}
    return f


def labels():
    out = {"_views": {"front": "Front (tab side)", "top": "Button side", "bottom": "Cup side"}}
    for name, f in features().items():
        out[name] = {"at": list(f["at"]), "normal": list(f["normal"])}
    return out


# Print orientation per part: True = flip it upside down.
PRINT_FLIP = {"stand": False, "stencil": False, "body": False, "sieve": False, "lid": True,
              "rod": False, "button": True, "spring": False}


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

    if "--no-cache" in sys.argv:
        USE_CACHE = False
    t_run = __import__("time").monotonic()
    check_design()
    ps = parts()
    asm = build()
    cq.exporters.export(asm, "cocoa_dispenser.step")
    pressed = parts(press=STROKE)
    cq.exporters.export(cq.Workplane("XY").newObject([cq.Compound.makeCompound(
        [p.val() for p in pressed.values()])]), "cocoa_dispenser_pressed.step")
    taps = STROKE / RACK_PITCH
    print(f"one press: about {taps:.0f} taps down and {taps:.0f} up; rack {RACK_L:.1f} mm, {RACK_TEETH} teeth")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # The tongue: on the rack at rest and at full press, biting by TONGUE_BITE and no more.
    tongue = tongue_solid().translate((0, 0, BODY_Z))
    for state, press in (("rest", 0.0), ("pressed", STROKE)):
        tip_rod_z = TIP_Z - (ROD_BOT - press)  # Tip height in the rod frame.
        assert RACK_Z0 + 1 < tip_rod_z < RACK_Z0 + RACK_L - 1, f"{state}: the tongue tip is off the rack"
        # Against the rod's plain square the nub must reach in by the bite, and no more;
        # against the toothed rod it overlaps less, because it sits in a tooth valley.
        env = cq.Workplane("XY").rect(ROD_SQ, ROD_SQ).extrude(ROD_TOP - ROD_BOT).translate((0, 0, BODY_Z + ROD_BOT - press))
        v_env = tongue.intersect(env).val().Volume() if tongue.intersect(env).vals() else 0.0
        v_rod = tongue.intersect(rod(press)).val().Volume() if tongue.intersect(rod(press)).vals() else 0.0
        assert v_env > 0.05, f"{state}: the tongue does not reach the rod"
        assert v_env < TONGUE_BITE ** 2 * TONGUE_W * 2, f"{state}: the tongue is buried in the rod"
        assert v_rod < v_env + 0.01, f"{state}: the tongue is not over the teeth"
        print(f"tongue {state}: nub reaches {v_env:.2f} mm3 into the rod's square, {v_rod:.2f} mm3 into the teeth")
    # Interference in the use frame, at rest and at full press. The lid is checked
    # without its tongue: the tongue's bite is the one overlap that is meant to be.
    for state, pp in (("rest", ps), ("pressed", pressed)):
        pp = dict(pp)
        pp["lid"] = lid(with_tongue=False)
        names = list(pp)
        bbs = {k: v.val().BoundingBox() for k, v in pp.items()}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                A, B = bbs[a], bbs[b]
                if (A.xmax < B.xmin or B.xmax < A.xmin or A.ymax < B.ymin or B.ymax < A.ymin
                        or A.zmax < B.zmin or B.zmax < A.zmin):
                    continue  # Boxes apart: no boolean needed.
                v = pp[a].intersect(pp[b]).val().Volume() if pp[a].intersect(pp[b]).vals() else 0.0
                assert v < 0.5, f"{state}: {a} and {b} overlap by {v:.2f} mm3"
        gc.collect()

    # Each part on its own, then one plate STL from those meshes, so the sieve
    # (about 1300 holes) is tessellated only once.
    layout = {"stand": (2, 2), "body": (118, 2), "spring": (226, 2), "stencil": (2, 120),
              "lid": (96, 120), "button": (172, 120), "rod": (210, 120), "sieve": (172, 160)}
    boxes = []
    if PRINT_SPRING:
        ps["spring"] = wave_spring()  # Printed at its free length.
    for name, p in ps.items():
        solid = p.val()
        assert solid.isValid(), f"{name}: invalid solid"
        assert len(p.solids().vals()) == 1, f"{name}: not one solid"
        pr = for_print(p, PRINT_FLIP[name])
        # The STL and the slab test are cached with the part: the body's 1,000 holes
        # take ten seconds to mesh, and nothing changed when the key is the same.
        stl_key = KEYS.get(name)
        if name == "body":
            stl_key = (KEYS.get("shell", "") + KEYS.get("floor", "")) or None
        if name == "spring":
            stl_key = part_key("spring-free", SPRING_DEPS, wave_spring)
        cached_stl = CACHE_DIR / f"{name}-{stl_key}-{int(PRINT_FLIP[name])}.stl" if (USE_CACHE and stl_key) else None
        if cached_stl and cached_stl.exists():
            __import__("shutil").copyfile(cached_stl, f"{name}.stl")
        elif name == "body" and not SIEVE_SEPARATE and USE_CACHE:
            # The body's mesh is its shell and its sieve floor meshed apart and joined as
            # two overlapping shells (slicers union them): the floor's thousand holes are
            # meshed once and a grip change costs only the shell.
            slab_test(pr, name)
            bb = p.val().BoundingBox()
            move = (-bb.xmin, -bb.ymin, -bb.zmin)
            pieces = []
            for piece, pkey in (("shell", KEYS["shell"]), ("floor", KEYS["floor"])):
                f = CACHE_DIR / f"{piece}-{pkey}.stl"
                if not f.exists():
                    shape = cq.Workplane("XY").newObject([cq.Shape.importBrep(str(CACHE_DIR / f"{piece}-{pkey}.brep"))])
                    # Twelve facets per 0.8 mm hole are plenty; 0.2 rad would give thirty and a 14 MB mesh.
                    ang = 0.5 if piece == "floor" else 0.2
                    cq.exporters.export(shape.translate((0, 0, BODY_Z)).translate(move), str(f), tolerance=0.05, angularTolerance=ang)
                pieces.append((str(f), (0, 0)))
            merge_stls(pieces, f"{name}.stl")
            if cached_stl:
                __import__("shutil").copyfile(f"{name}.stl", cached_stl)
        else:
            slab_test(pr, name)
            cq.exporters.export(pr, f"{name}.stl", tolerance=0.05, angularTolerance=0.2)
            if cached_stl:
                __import__("shutil").copyfile(f"{name}.stl", cached_stl)
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
    print(f"spring {SPRING_REST:.1f} mm at rest, {SPRING_PRESSED:.1f} mm pressed (free {SPRING_L:.1f}, solid {SPRING_SOLID:.1f})")
    if PRINT_SPRING:
        # Crest-to-crest wave spring estimate, PETG E about 2000 MPa. Test it: printed parts vary.
        k = spring_rate()
        have, climb, flank = return_budget()
        print(f"spring rate about {k:.1f} N/mm: {k * PRELOAD:.1f} N at rest, {k * (PRELOAD + STROKE):.1f} N pressed")
        print(f"return: {have:.1f} N at the last tooth against {climb:.1f} N to climb its {flank:.0f} degree flank "
              f"({have / climb:.1f}x); press peak about {k * (PRELOAD + STROKE) + climb:.0f} N")
    print(f"wrote cocoa_dispenser.step, cocoa_dispenser_pressed.step, {len(ps)} part STLs, cocoa_dispenser_plate.stl, labels.json "
          f"in {__import__('time').monotonic() - t_run:.0f} s" + ("" if USE_CACHE else " without the cache"))
