"""Cocoa duster for latte art, made with smlibpy.

Each press moves a rack past a striker tongue in the lid: one tap on the body per tooth.
The taps shake cocoa through the fine sieve floor onto a slide-in stencil on the cup.
Parts: stand, stencil, body with sieve, rod with rack, lid with tongue, button and a printed wave spring.
Z is up from the cup rim, the stencil tab points to -Y and the rack faces +X.
Run `uv run cocoa_dispenser.py` for the STEPs, STLs and labels, or add `--serve` for the configurator.
"""
import math

from smlibpy import (Align, Box, Circle, Cylinder, Line, Plane, Polygon, Polyline, Sphere, ThreePointArc, Wire, X, Z,
                     loft, make_face)

# ☕ Cup, only for the ghost view: the stand rests on any rim wider than its window.
CUP_D = 90.0         # Cup rim outside diameter. [60:130].
CUP_H = 70.0         # Cup height below the rim. [30:120].

# 🖨️ Printer. Every part prints flat, so X and Y use lines and Z uses layers.
NOZZLE = 0.4
LINE = 0.45          # Line width, about 1.1 x the nozzle.
LAYER = 0.2

# 🫙 Body: the cocoa hopper with its locating flange.
HOP_D = 72.0         # Hopper outside diameter. [50:100].
HOP_H = 75.0         # Body height from the sieve face to the hopper rim. [40:130].
WALL = 5 * LINE      # Hopper wall, 5 lines. [1.2:4].
FLANGE_D = 104.0     # Flange diameter, which covers the stencil slot. [90:130].
FLANGE_T = 15 * LAYER  # Flange thickness. [1.6:6].

# ✋ Grip and joint.
FLANGE_R = 1.5       # Fillet where the hopper meets the flange. [0:3].
GRIP_RIBS = 12       # Number of vertical grip ribs: round rods half sunk into the hopper wall. [0:24].
GRIP_D = 3.0         # Rib diameter. [2:5].
GRIP_PROUD = 1.8     # Rib height out of the hopper wall. [0.8:2.5].
GRIP_GAP = 8.0       # Distance between the rib ends and the flange and the hopper rim. [4:20].

# 🕳️ Sieve: the body floor, with fine holes that are vertical in the print.
SIEVE_D = 60.0       # Sieve diameter, with a 45 degree cone up to the hopper bore. [30:62].
SIEVE_T = 6 * LAYER  # Floor thickness. [0.8:2].
SIEVE_HOLE = 0.8     # Hole diameter, 0.8 for cocoa and 0.6 to 0.7 for cinnamon. [0.6:1.2].
SIEVE_PITCH = 1.7    # Hole spacing on a hex grid, so the web is two lines at 0.45. [1.2:3].

# 🧩 Drop-in sieve.
SIEVE_SEPARATE = False  # A drop-in sieve disc with a peg, so you can change the hole size. [0:1].
SIEVE_LEDGE = 3.0    # Width of the ring ledge under the drop-in disc. [2:5].

# 🦷 Rod and rack: the tapper.
ROD_SQ = 6.0         # Rod square side. [5:9].
RACK_PITCH = 2.4     # Tooth pitch along the rod, one tap per tooth, longer for a gentler flank. [1:3].
RACK_DEPTH = 0.8     # Tooth depth into the rod face. [0.5:1.5].

# 🥄 Agitator foot.
AGI_FOOT = True      # A flat disc at the rod bottom that stirs the cocoa above the sieve. [0:1].
FOOT_D = 20.0        # Agitator foot diameter. [10:30].
FOOT_T = 2.0         # Agitator foot thickness. [1:4].

# 🖼️ Stencil, which slides into the stand from the front.
STENCIL_D = 90.0     # Stencil disc diameter. [70:100].
STENCIL_T = 6 * LAYER  # Stencil thickness. [0.8:2].
STENCIL_LIP = 3.0    # Lip around the disc that keeps the spill on the stencil. [0:4].
SPOUT_W = 12.0       # Width of the pour spout, a gap in the lip at the back. [0:20].
HEART_W = 52.0       # Heart width. [15:70].

# 🏷️ Stencil tab and slot.
TAB_W = 30.0         # Pull tab width. [15:50].
TAB_L = 18.0         # Tab length out of the stand. [8:40].
SLOT_PLAY = 0.4      # Slot height above the stencil thickness. [0.2:1].
SLOT_SIDE = 0.3      # Slot clearance per side around the disc. [0.1:0.6].

# 🍽️ Stand, which rests on the cup rim.
STAND_D = 112.0      # Stand outside diameter. [95:140].
STAND_BASE = 17 * LAYER  # Floor under the stencil. [2:6].
WINDOW_D = 70.0      # Opening under the stencil, over the cup. [40:85].
RIM_H = 3.0          # Locating rim around the body flange. [1:8].
RIM_PLAY = 0.5       # Clearance per side between the rim and the flange. [0.2:1.5].

# 🌫️ Drop chamber, so the hole pattern mixes into an even cloud of cocoa.
STAND_R = 1.5        # Round on the window edge at the bottom and the rim edge at the top. [0:3].
DROP_H = 15.0        # Height of the chamber between the stencil and the sieve. [8:40].
CHAMBER_D = 80.0     # Chamber bore, with a 45 degree cone over the stencil slot around it. [60:95].

# 🔘 Lid and button travel.
STROKE = 10.0        # Button travel. [4:20].
ROD_PLAY = 0.3       # Clearance per side of the rod in the square guide of the lid. [0.15:0.6].
LID_T = 16 * LAYER   # Lid plate thickness. [1.6:5].
LID_PLUG = 6.0       # Depth of the lid plug in the hopper. [3:12].
LID_FIT = 0.2        # Clearance per side of the lid plug in the hopper. [0.05:0.5].

# 🧲 Lid hub and spring seat.
LID_R = 1.0          # Round on the top edge of the guide hub. [0:2].
HUB_D = 16.0         # Guide hub diameter, with two lines of wall outside the tongue pocket. [10:20].
HUB_DOWN = 4.0       # Hub reach below the plug, for a longer guide and room for the tongue. [0:12].
SEAT_DEPTH = 8 * LAYER  # Spring seat depth in the lid top. [0.8:3].
SPRING_PLAY = 1.0    # Clearance per side around the spring in the seat and the button skirt. [0.3:2].

# 🔲 Button.
BTN_WALL = 9 * LINE  # Button skirt wall. [1.2:6].
BTN_TOP = 8.0        # Solid cap above the skirt, which holds the rod socket. [5:14].
SOCKET = 6.0         # Rod depth in the button. [3:10].
ROD_PRESS = 0.05     # Tight socket clearance per side, for a drop of glue. [0:0.2].

# 👅 Striker tongue: a finger in the lid hub that the rack clicks past.
TONGUE_T = 2 * LINE  # Tongue thickness of 2 lines, thin enough to flex 0.5 mm. [0.6:1.8].
TONGUE_L = 8.0       # Tongue length from its root to the tip. [6:14].
TONGUE_W = 4.0       # Tongue width. [2:6].
TONGUE_BITE = 0.5    # Reach of the tip into the teeth, which is the bend per tooth. [0.3:1].
TONGUE_FLEX = 1.2    # Free room behind the tongue, so it can swing out. [0.8:2].

# 🧮 Tongue root and force estimates.
TONGUE_ROOT = 2.0    # Solid lid above the tongue root. [1.2:4].
TOOTH_MU = 0.3       # Friction of the tongue tip on a tooth flank, PETG on PETG. [0.2:0.5].
PETG_E = 2000.0      # Printed PETG modulus in MPa, for the tongue and spring force estimates. [1500:2500].
PRINT_SPRING = True  # Print the wave spring, or use a bought metal spring.
PRELOAD = 4.0        # Spring compression at rest, against rattle and for the return over the last tooth. [0.5:6].

# 🌀 Printed wave spring.
WS_D = 20.0          # Wave spring mean diameter, softer when larger. [12:30].
WS_B = 4 * LINE      # Radial band width, 4 lines. [1.2:4].
WS_T = 3 * LAYER     # Vertical band thickness, 3 layers, with half the rate of 4. [0.6:2].
WS_H = 4.0           # Wave height, crest to trough. [2:8].
WS_WAVES = 3         # Waves per ring, softer when fewer but with a flatter underside. [2:6].

# 🔁 Wave spring rings.
WS_RINGS = 8         # Number of wave rings, softer and longer when more. [4:16].
WS_END = 6 * LAYER   # Flat end ring thickness. [0.8:3].
WS_JOIN = 0.3        # Overlap where the rings touch, so they print as one part. [0.1:0.6].

# 🔩 Bought metal spring, when PRINT_SPRING is off.
METAL_OD = 10.0      # Outside diameter, for wire of 0.6 to 0.8 mm. [6:13].
METAL_L = 25.0       # Free length. [15:40].
METAL_SOLID = 8.0    # Fully compressed length. [4:14].

# Derived values.
if PRINT_SPRING:
    SPRING_OD = WS_D + WS_B
    WS_PITCH = WS_H + WS_T - WS_JOIN
    SPRING_L = 2 * WS_END - WS_JOIN + WS_RINGS * WS_PITCH
    SPRING_SOLID = 2 * WS_END + WS_RINGS * WS_T
else:
    SPRING_OD, SPRING_L, SPRING_SOLID = METAL_OD, METAL_L, METAL_SOLID
WS_END_LAP = 0.1                           # The end rings are this much wider per side than the band, so the fuse works.
ROD_D = ROD_SQ * math.sqrt(2)              # The rod diagonal, which round bores must clear.
ROD_FOOT = STROKE + 2.0                    # Rod bottom above the sieve at rest, 2 mm above it at full press.
SEAT_D = SPRING_OD + 2 * SPRING_PLAY
BTN_CAV_D = SPRING_OD + 2 * SPRING_PLAY
BTN_D = BTN_CAV_D + 2 * BTN_WALL
BTN_CAV = SPRING_L - PRELOAD - STROKE - SEAT_DEPTH   # Skirt depth, so the spring at rest fits exactly.
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
BTN_Z = LID_TOP + STROKE                # Button skirt bottom at rest, which lands on the lid at full press.
CEIL_Z = BTN_Z + BTN_CAV
ROD_TOP = CEIL_Z + SOCKET
SPRING_REST = CEIL_Z - (LID_TOP - SEAT_DEPTH)
SPRING_PRESSED = SPRING_REST - STROKE
TIP_Z = LID_TOP - TONGUE_ROOT - TONGUE_L  # Tongue tip height, body frame, with the root TONGUE_ROOT under the lid top.
RACK_Z0 = TIP_Z - ROD_BOT - 3.0         # Rack start, rod frame, so the tip is on the rack over the full stroke.
RACK_TEETH = int(round((STROKE + 6.0) / RACK_PITCH))  # Whole teeth over the stroke plus 3 mm each way.
RACK_L = RACK_TEETH * RACK_PITCH
BED = 256.0

assert min(WALL, 4 * LINE) >= 2 * LINE, "a wall is thinner than two lines"


def spring_rate():
    """Return the rate of the printed wave spring in N/mm, a crest-to-crest estimate. Printed parts vary, so test it."""
    return PETG_E * WS_B * WS_T ** 3 * WS_WAVES ** 4 / (2.4 * WS_D ** 3) / WS_RINGS


def return_budget():
    """Return the spring force at the last tooth before rest, the force the tongue costs, and the flank angle.

    The tongue is a cantilever bent by TONGUE_BITE.
    To push its tip up a flank at angle `flank` from the rod axis costs tip_force * tan(flank + atan(mu)).
    """
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
    assert SPRING_OD + 1 <= BTN_CAV_D and SPRING_OD + 2 * WS_END_LAP <= SEAT_D, "the spring does not fit"
    assert SPRING_REST < SPRING_L, "no spring preload: shorten BTN_CAV or use a longer spring"
    assert SPRING_PRESSED > SPRING_SOLID + 0.5, "the spring goes solid before the button lands"
    assert ROD_TOP - BTN_Z + BTN_TOP - SOCKET > 0
    assert BTN_CAV_D > ROD_D + 2, "the rod's diagonal does not fit the button cavity"
    assert BTN_CAV > 3, "the spring is too short for this stroke"
    assert SEAT_D < HOP_D - 6, "the spring seat is wider than the lid"
    assert SPRING_OD - 2 * (WS_B if PRINT_SPRING else 0.8) > ROD_D + 2, "the rod does not fit inside the spring"
    assert WS_D - WS_B - 2 * WS_END_LAP > HUB_D + 1, "the hub does not fit inside the spring"
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
    strain = 1.5 * TONGUE_BITE * TONGUE_T / TONGUE_L ** 2  # Cantilever tip bend: the maximum strain is 3 d t / (2 L^2).
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
    return Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(0, 0, z)


def rect(w, d, h, cx=0.0, cy=0.0, z=0.0):
    return Box(w, d, h, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(cx, cy, z)


# A disk cache of built parts in the native smlibpy format.
# A change to one setting rebuilds only the parts that use it.
# The key is the source of the builder plus the values of the settings it names.
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


def cached(name, deps, builder, *args):
    """Build a part through the cache, with one .smb file per key under .cache/."""
    from smlibpy import load, save
    key = part_key(name, deps, builder, args)
    KEYS[name] = key
    f = CACHE_DIR / f"{name}-{key}.smb"
    if USE_CACHE and f.exists():
        return load(str(f))
    shape = builder(*args)
    if USE_CACHE:
        CACHE_DIR.mkdir(exist_ok=True)
        save(shape, str(f), ascii=False)
    return shape


def rounded(p, edges, r, what):
    """Fillet the edges only when the result is one valid solid, and leave them sharp if not."""
    if not edges:
        return p
    try:
        out = p.fillet(edges, r)
        if out.is_valid() and len(out.solids()) == 1:
            return out
        print(f"{what}: round left sharp, the fillet made an invalid solid")
    except Exception as e:
        print(f"{what}: round left sharp: {e}")
    return p


def smallest_circles(p, z0, z1):
    """Return the circle edges with the smallest radius among those with their centre between z0 and z1.

    The CadQuery version of this model chose these edges, so the port keeps the same printed geometry.
    """
    cs = [e for e in p.edges() if e.geom_type == "circle" and z0 - 0.1 <= e.center().z <= z1 + 0.1]
    if not cs:
        return []
    r = min(e.radius for e in cs)
    return [e for e in cs if abs(e.radius - r) < 1e-6]


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
    """Return the sawtooth teeth as (x, z) points in the rod frame, cut into the +X face."""
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

def stadium(z):
    """Return the way out of the stencil at height z: the round slot and the channel to the front."""
    rs = SLOT_R
    return make_face(Wire([ThreePointArc((rs, 0, z), (0, rs, z), (-rs, 0, z)), Line((-rs, 0, z), (-rs, -STAND_D, z)),
                           Line((-rs, -STAND_D, z), (rs, -STAND_D, z)), Line((rs, -STAND_D, z), (rs, 0, z))]))


STAND_DEPS = ["STAND_D", "STAND_BASE", "WINDOW_D", "RIM_H", "RIM_PLAY", "STAND_R", "DROP_H", "CHAMBER_D",
              "STENCIL_D", "STENCIL_T", "STENCIL_LIP", "SLOT_PLAY", "SLOT_SIDE", "FLANGE_D"]


def stand():
    return cached("stand", STAND_DEPS, stand_build)


def stand_build():
    """Return the base ring with the stencil slot, the drop chamber above it and the locating rim.

    The roof of the slot is the stadium outline, tapered inward at 45 degrees as it rises.
    The ceiling over the slot, over the channel and at the front mouth is thus one slope that prints.
    The chamber bore goes through it.
    """
    rs, ro = SLOT_R, STAND_D / 2
    s = cyl(STAND_D, STAND_TOP) - cyl(WINDOW_D, STAND_TOP + 2, -1)
    s -= stadium(STAND_BASE).extrude(SLOT_H)
    s -= stadium(SLOT_TOP - 0.01).extrude(DROP_H + 2, taper=45)
    s -= cyl(CHAMBER_D, DROP_H + 2, SLOT_TOP - 0.01)
    rim = cyl(STAND_D, RIM_H, STAND_TOP) - cyl(FLANGE_D + 2 * RIM_PLAY, RIM_H + 2, STAND_TOP - 1)
    s += rim - rect(2 * SLOT_R, STAND_D, RIM_H + 2, 0, -STAND_D / 2, STAND_TOP - 1)
    # Where the straight sides of the channel leave the round stand, the outer skin thins to a feather.
    # Cut both horns flat, 2 mm behind the tangent point, over the full height.
    y_t = math.sqrt(ro ** 2 - rs ** 2)
    for sx in (1, -1):
        s -= rect(20, 60, STAND_TOP + RIM_H + 2, sx * (rs + 10), -(y_t - 2) - 30, -1)
    if STAND_R > 0:  # The window edge at the bottom, then the rim edge at the top.
        s = rounded(s, smallest_circles(s, 0.0, 0.0), STAND_R, "stand bottom")
        s = rounded(s, smallest_circles(s, STAND_TOP + RIM_H, STAND_TOP + RIM_H), STAND_R, "stand top")
    return s


STENCIL_DEPS = ["STENCIL_D", "STENCIL_T", "STENCIL_LIP", "SPOUT_W", "HEART_W", "TAB_W", "TAB_L", "STAND_D", "STAND_BASE"]


def stencil():
    return cached("stencil", STENCIL_DEPS, stencil_build)


def stencil_build():
    reach = STAND_D / 2 + TAB_L
    st = cyl(STENCIL_D, STENCIL_T) + rect(TAB_W, reach, STENCIL_T, 0, -reach / 2)
    st = st.fillet([e for e in st.edges().parallel_to(Z) if abs(e.center().y + reach) < 1 and abs(e.center().x) <= TAB_W], 4)
    if STENCIL_LIP > 0:
        lip = cyl(STENCIL_D, STENCIL_LIP, STENCIL_T) - cyl(STENCIL_D - 2 * 3 * LINE, STENCIL_LIP + 2, STENCIL_T - 1)
        if SPOUT_W > 0:  # The pour spout is a gap in the lip at the back (+Y).
            lip -= rect(SPOUT_W, 10, STENCIL_LIP + 2, 0, STENCIL_D / 2, STENCIL_T - 1)
        st += lip
    st -= cyl(12, STENCIL_T + 2, -1).translate(0, -reach + 9, 0)
    st -= Polygon(heart_points(HEART_W)).translate(0, 0, -1).extrude(STENCIL_T + 2)
    return st.translate(0, 0, STAND_BASE)


def sieve_holes(r_max):
    """Return a hex grid of holes over the floor, each hole fully inside r_max."""
    return [(x, y) for x, y in hex_points(r_max, SIEVE_PITCH) if math.hypot(x, y) <= r_max - SIEVE_HOLE / 2 - LINE]


def holed_disc(d, pts):
    """Return a disc of diameter d and thickness SIEVE_T with a hole at each point.

    The holes go out of the 2D outline before the extrusion, which is two times faster than solid cuts.
    """
    sk = Circle(d / 2) - [Circle(SIEVE_HOLE / 2).translate(x, y, 0) for x, y in pts]
    return sk.extrude(SIEVE_T)


FLOOR_DEPS = ["SIEVE_D", "SIEVE_T", "SIEVE_HOLE", "SIEVE_PITCH"]
SHELL_DEPS = ["HOP_D", "HOP_H", "WALL", "FLANGE_D", "FLANGE_T", "FLANGE_R", "GRIP_RIBS", "GRIP_D", "GRIP_PROUD", "GRIP_GAP",
              "SIEVE_D", "SIEVE_T", "SIEVE_SEPARATE", "SIEVE_LEDGE"]


def floor_build():
    """Return the sieve floor alone: a disc with the hex grid of holes, 1 mm of radius into the shell."""
    return holed_disc(SIEVE_D + 2.0, sieve_holes(SIEVE_D / 2))


def shell_build():
    """Return the hopper, the flange, the grip ribs and the cone, with the floor open for the sieve disc."""
    b = cyl(FLANGE_D, FLANGE_T) + cyl(HOP_D, HOP_H)
    if FLANGE_R > 0:
        b = rounded(b, smallest_circles(b, 0.0, FLANGE_T), FLANGE_R, "flange")
    if GRIP_RIBS > 0:
        # Round vertical rods half sunk into the hopper wall: easy to hold, nothing to support.
        rc = HOP_D / 2 - GRIP_D / 2 + GRIP_PROUD
        z0, z1 = FLANGE_T + GRIP_GAP, HOP_H - GRIP_GAP
        for k in range(GRIP_RIBS):
            a = 2 * math.pi * k / GRIP_RIBS
            b += cyl(GRIP_D, z1 - z0, z0).translate(rc * math.cos(a), rc * math.sin(a), 0)
    r0, r1 = SIEVE_D / 2, HOP_ID / 2
    cavity = Polygon((0, SIEVE_T), (r0, SIEVE_T), (r1, SIEVE_T + (r1 - r0)), (r1, HOP_H + 1), (0, HOP_H + 1))
    b -= cavity.on(Plane.XZ).revolve(Z)
    if SIEVE_SEPARATE:
        # A ring ledge: the drop-in sieve disc rests on it, flush with the top of the floor.
        b -= cyl(SIEVE_D - 2 * SIEVE_LEDGE, SIEVE_T + 2, -1)
        b -= cyl(SIEVE_D + 0.6, SIEVE_T, 0.001) - cyl(SIEVE_D - 2 * SIEVE_LEDGE - 1, SIEVE_T + 2, -1)
    else:
        b -= cyl(SIEVE_D, SIEVE_T + 2, -1)  # The floor opening that the sieve disc fills.
    return b


def body():
    """Return the hopper, the flange and the sieve floor with the 45 degree cone up to the bore."""
    b = cached("shell", SHELL_DEPS, shell_build)
    if not SIEVE_SEPARATE:
        b += cached("floor", FLOOR_DEPS, floor_build)
    return b.translate(0, 0, BODY_Z)


def body_plain():
    """Return the body with a plain floor disc instead of the sieve holes, for the checks.

    An intersection meshes both parts, and the 1,000 holes made each check of the body take seconds.
    """
    b = cached("shell", SHELL_DEPS, shell_build)
    if not SIEVE_SEPARATE:
        b += cyl(SIEVE_D + 2.0, SIEVE_T)
    return b.translate(0, 0, BODY_Z)


def sieve():
    """Return the drop-in sieve disc that rests on the ledge, with a peg at the edge to lift it."""
    d = SIEVE_D - 0.6
    s = holed_disc(d, sieve_holes(d / 2 - SIEVE_LEDGE))
    s += cyl(4.0, 8.0, SIEVE_T).translate(d / 2 - 3.0, 0, 0)  # The lifting peg.
    return s.translate(0, 0, BODY_Z)


def tongue_solid():
    """Return the striker tongue in the body frame: a finger that hangs from the hub top on the +X side.

    Its body is just outside the guide hole.
    A 45 degree nub at the free end reaches ROD_PLAY + TONGUE_BITE inward, so only the nub rides the teeth.
    """
    x_body = ROD_SQ / 2 + ROD_PLAY
    reach = ROD_PLAY + TONGUE_BITE
    finger = rect(TONGUE_T, TONGUE_W, TONGUE_L + 0.5, x_body + TONGUE_T / 2, 0, TIP_Z)
    nub = Polygon((x_body + 0.01, TIP_Z), (x_body - reach, TIP_Z + reach), (x_body + 0.01, TIP_Z + 2 * reach))
    return finger + nub.on(Plane.XZ.offset(-TONGUE_W / 2)).extrude(TONGUE_W)


def lid(with_tongue=True):
    plate = cyl(HOP_D, LID_T, HOP_H)
    plug_od = HOP_ID - 2 * LID_FIT
    plug = cyl(plug_od, LID_PLUG, HUB_BOT) - cyl(plug_od - 2 * 4 * LINE, LID_PLUG + 2, HUB_BOT - 1)
    hub = cyl(HUB_D, HUB_TOP - HUB_LOW, HUB_LOW)
    l = plate + plug + hub
    l -= cyl(SEAT_D, SEAT_DEPTH + 1, LID_TOP - SEAT_DEPTH) - cyl(HUB_D, SEAT_DEPTH + 3, LID_TOP - SEAT_DEPTH - 1)
    sq = ROD_SQ + 2 * ROD_PLAY
    l -= rect(sq, sq, HUB_TOP - HUB_LOW + 2, 0, 0, HUB_LOW - 1)
    # The pocket the tongue swings in goes from the guide hole out through the tongue and its flex room.
    # It is a little wider than the tongue, and it goes from below the tip up to the root.
    x_in, x_out = ROD_SQ / 2 + ROD_PLAY - 0.01, ROD_SQ / 2 + ROD_PLAY + TONGUE_T + TONGUE_FLEX
    l -= rect(x_out - x_in, TONGUE_W + 1.2, TONGUE_L + 1.0, (x_in + x_out) / 2, 0, TIP_Z - 1.0)
    if with_tongue:
        l += tongue_solid()
    if LID_R > 0:
        l = rounded(l, smallest_circles(l, LID_TOP, LID_TOP), LID_R, "lid")
    return l.translate(0, 0, BODY_Z)


def rod(press=0.0):
    """Return the square rod, straight, with the rack on its +X face and the foot at the bottom."""
    r = rect(ROD_SQ, ROD_SQ, ROD_TOP - ROD_BOT)
    r -= Polygon(rack_profile()).on(Plane.XZ.offset(-(ROD_SQ / 2 + 1))).extrude(ROD_SQ + 2)
    if AGI_FOOT:
        r += cyl(FOOT_D, FOOT_T)
    return r.translate(0, 0, BODY_Z + ROD_BOT - press)


def button(press=0.0):
    b = cyl(BTN_D, BTN_CAV + BTN_TOP) - cyl(BTN_CAV_D, BTN_CAV + 1, -1)
    sq = ROD_SQ + 2 * ROD_PRESS
    b -= rect(sq, sq, SOCKET + 0.5, 0, 0, BTN_CAV - 0.5)
    top = BTN_CAV + BTN_TOP
    b = b.fillet([e for e in b.edges() if e.geom_type == "circle" and abs(e.center().z - top) < 0.01], 2.0)
    b -= Sphere(30).translate(0, 0, top + 30 - 1.0)  # A shallow finger dimple.
    return b.translate(0, 0, BODY_Z + BTN_Z - press)


def ring_sections(base, sign, h, n):
    """Return n radial rectangles round the axis whose height follows a cosine with WS_WAVES waves."""
    r0, r1 = WS_D / 2 - WS_B / 2, WS_D / 2 + WS_B / 2
    secs = []
    for k in range(n):
        th = 2 * math.pi * k / n
        z = base + h / 2 * (1 + sign * math.cos(WS_WAVES * th))
        c, s = math.cos(th), math.sin(th)
        secs.append(Polyline(*[(r * c, r * s, zz) for r, zz in ((r0, z), (r1, z), (r1, z + WS_T), (r0, z + WS_T))],
                             close=True))
    return secs


def wave_ring(base, sign, h=WS_H, n=36):
    """Return one wave ring: a band WS_B wide and WS_T thick whose height follows a cosine.

    A closed smooth loft through 36 radial rectangles makes it.
    """
    return loft(ring_sections(base, sign, h, n), closed=True)


def wave_spring(length=None):
    """Return the wave spring on z = 0. With a length, the pitch gets shorter to show it compressed.

    The end rings are WS_END_LAP wider per side than the band.
    With faces on the same cylinders, the fuse of the end rings and the wave rings fails.
    """
    length = SPRING_L if length is None else length
    pitch = (length - 2 * WS_END + WS_JOIN) / WS_RINGS
    h = pitch - WS_T + WS_JOIN  # A compressed spring has flatter waves.

    def end(z):
        return cyl(SPRING_OD + 2 * WS_END_LAP, WS_END, z) - cyl(WS_D - WS_B - 2 * WS_END_LAP, WS_END + 2, z - 1)

    s = wave_ring(WS_END - WS_JOIN, -1, h)
    for i in range(1, WS_RINGS):
        s += wave_ring(WS_END - WS_JOIN + i * pitch, -1 if i % 2 == 0 else 1, h)
    return s + end(0.0) + end(length - WS_END)


SPRING_DEPS = ["WS_D", "WS_B", "WS_T", "WS_H", "WS_WAVES", "WS_RINGS", "WS_END", "WS_JOIN", "SPRING_OD", "WS_END_LAP"]


def spring(press=0.0):
    length = SPRING_REST - press
    return cached("spring", SPRING_DEPS, wave_spring, length).translate(0, 0, BODY_Z + LID_TOP - SEAT_DEPTH)


FIXED = {}


def parts(press=0.0):
    """Return all parts in the use frame. The parts that the press does not move build once per run."""
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
    """Return the assembly at rest as a list of separate parts."""
    check_design()
    return list(parts().values())


def drawing_shapes():
    """Return the assembly for the Drawing view of the configurator, with the body on a plain floor.

    The hidden-line step over the 1,000 sieve holes took minutes a view.
    """
    ps = parts()
    ps["body"] = body_plain()
    return list(ps.values())


def device():
    """Return the cup, and the bought spring when there is one, for the ghost view."""
    cup = cyl(CUP_D, CUP_H, -CUP_H) - cyl(CUP_D - 6, CUP_H, -CUP_H + 4)
    if PRINT_SPRING:
        return cup
    z = BODY_Z + LID_TOP - SEAT_DEPTH
    return cup + (cyl(SPRING_OD, SPRING_REST, z) - cyl(SPRING_OD - 1.6, SPRING_REST + 2, z - 1))


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


# Print orientation per part: True turns it upside down.
PRINT_FLIP = {"stand": False, "stencil": False, "body": False, "sieve": False, "lid": True,
              "rod": False, "button": True, "spring": False}


def for_print(p, flip):
    if flip:
        p = p.rotate(X, 180)
    low = p.bbox().min
    return p.translate(-low.x, -low.y, -low.z)


def shared(a, b):
    """Return the volume that two parts share, and 0 when they do not touch."""
    try:
        return float((a & b).volume or 0.0)
    except Exception:
        return 0.0


def slab_test(p, name):
    size = p.bbox().size
    # Each slab reaches 0.5 mm past the part, because a slab face on a part face makes the intersection fail.
    slab = Box(BED + 2, BED + 2, 1.5, align=Align.MIN).translate(-1, -1, 0)
    lo, hi = shared(p, slab.translate(0, 0, -0.5)), shared(p, slab.translate(0, 0, size.z - 1.0))
    assert lo >= hi, f"{name}: more material at the top than on the bed, check the flip"
    assert size.x <= BED and size.y <= BED, f"{name}: does not fit the bed"


def merge_stls(items, out):
    """Join binary STLs into one, each moved by (dx, dy). The parts stay separate shells."""
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
    import json
    import shutil
    import sys
    import time
    if "--serve" in sys.argv:
        from printforge_configurator import serve
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8768
        host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"  # Use --lan to open the page from a phone.
        serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
        sys.exit()

    from smlibpy import export_step, export_stl, load

    if "--no-cache" in sys.argv:
        USE_CACHE = False
    t_run = time.monotonic()
    check_design()
    ps = parts()
    export_step(list(ps.values()), "cocoa_dispenser.step")
    pressed = parts(press=STROKE)
    export_step(list(pressed.values()), "cocoa_dispenser_pressed.step")
    taps = STROKE / RACK_PITCH
    print(f"one press: about {taps:.0f} taps down and {taps:.0f} up; rack {RACK_L:.1f} mm, {RACK_TEETH} teeth")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # The tongue must be on the rack at rest and at full press, and bite by TONGUE_BITE and no more.
    tongue = tongue_solid().translate(0, 0, BODY_Z)
    for state, press in (("rest", 0.0), ("pressed", STROKE)):
        tip_rod_z = TIP_Z - (ROD_BOT - press)  # Tip height in the rod frame.
        assert RACK_Z0 + 1 < tip_rod_z < RACK_Z0 + RACK_L - 1, f"{state}: the tongue tip is off the rack"
        # Against the plain square of the rod the nub must reach in by the bite, and no more.
        # Against the toothed rod it overlaps less, because it sits in a tooth valley.
        env = rect(ROD_SQ, ROD_SQ, ROD_TOP - ROD_BOT, 0, 0, BODY_Z + ROD_BOT - press)
        v_env, v_rod = shared(tongue, env), shared(tongue, rod(press))
        assert v_env > 0.05, f"{state}: the tongue does not reach the rod"
        assert v_env < TONGUE_BITE ** 2 * TONGUE_W * 2, f"{state}: the tongue is buried in the rod"
        assert v_rod < v_env + 0.01, f"{state}: the tongue is not over the teeth"
        print(f"tongue {state}: nub reaches {v_env:.2f} mm3 into the rod's square, {v_rod:.2f} mm3 into the teeth")
    # Interference in the use frame, at rest and at full press.
    # The check uses the lid without its tongue, because the design wants the bite of the tongue.
    for state, pp in (("rest", ps), ("pressed", pressed)):
        pp = dict(pp)
        pp["lid"] = lid(with_tongue=False)
        pp["body"] = body_plain()
        names = list(pp)
        bbs = {k: v.bbox() for k, v in pp.items()}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                A, B = bbs[a], bbs[b]
                if any(A.max[k] < B.min[k] or B.max[k] < A.min[k] for k in range(3)):
                    continue  # The boxes are apart, so no boolean is necessary.
                v = shared(pp[a], pp[b])
                assert v < 0.5, f"{state}: {a} and {b} overlap by {v:.2f} mm3"

    # Each part on its own, then one plate STL from those meshes, so the sieve holes get one mesh.
    layout = {"stand": (2, 2), "body": (118, 2), "spring": (226, 2), "stencil": (2, 120),
              "lid": (96, 120), "button": (172, 120), "rod": (210, 120), "sieve": (172, 160)}
    boxes = []
    if PRINT_SPRING:
        ps["spring"] = wave_spring()  # The spring prints at its free length.
    for name, p in ps.items():
        assert p.is_valid(), f"{name}: invalid solid"
        assert len(p.solids()) == 1, f"{name}: not one solid"
        pr = for_print(p, PRINT_FLIP[name])
        # The STL goes in the cache with the part: the 1,000 holes of the body take a long time to mesh.
        stl_key = KEYS.get(name)
        if name == "body":
            stl_key = (KEYS.get("shell", "") + KEYS.get("floor", "")) or None
        if name == "spring":
            stl_key = part_key("spring-free", SPRING_DEPS, wave_spring)
        cached_stl = CACHE_DIR / f"{name}-{stl_key}-{int(PRINT_FLIP[name])}.stl" if (USE_CACHE and stl_key) else None
        if cached_stl and cached_stl.exists():
            shutil.copyfile(cached_stl, f"{name}.stl")
        elif name == "body" and not SIEVE_SEPARATE and USE_CACHE:
            # The body mesh is its shell and its sieve floor, meshed apart and joined as two shells that overlap.
            # Slicers join them, and a grip change thus costs only the shell.
            slab_test(for_print(body_plain(), PRINT_FLIP[name]), name)
            low = p.bbox().min
            pieces = []
            for piece in ("shell", "floor"):
                f = CACHE_DIR / f"{piece}-{KEYS[piece]}.stl"
                if not f.exists():
                    shape = load(str(CACHE_DIR / f"{piece}-{KEYS[piece]}.smb"))
                    export_stl(shape.translate(-low.x, -low.y, BODY_Z - low.z), str(f), tolerance=0.05,
                               angle=30.0 if piece == "floor" else 12.0)
                pieces.append((str(f), (0, 0)))
            merge_stls(pieces, f"{name}.stl")
            if cached_stl:
                shutil.copyfile(f"{name}.stl", cached_stl)
        else:
            slab_test(pr, name)
            export_stl(pr, f"{name}.stl", tolerance=0.05, angle=12.0)
            if cached_stl:
                shutil.copyfile(f"{name}.stl", cached_stl)
        ps_ = pr.bbox().size
        x, y = layout[name]
        boxes.append((x, y, x + ps_.x, y + ps_.y))
        print(f"{name:8s} print {ps_.x:6.1f} x {ps_.y:6.1f} x {ps_.z:6.1f} mm, {p.volume / 1000:5.1f} cm3")
    for i, a in enumerate(boxes):
        assert a[2] <= BED and a[3] <= BED, "a part sticks off the bed"
        for b in boxes[i + 1:]:
            assert a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1], "parts overlap on the plate"
    merge_stls([(f"{n}.stl", layout[n]) for n in ps], "cocoa_dispenser_plate.stl")
    pmax = (max(b[2] for b in boxes), max(b[3] for b in boxes))
    asm = list(parts().values())
    lo = [min(p.bbox().min[i] for p in asm) for i in range(3)]
    hi = [max(p.bbox().max[i] for p in asm) for i in range(3)]
    print(f"assembled {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm; plate {pmax[0]:.0f} x {pmax[1]:.0f} mm")
    print(f"spring {SPRING_REST:.1f} mm at rest, {SPRING_PRESSED:.1f} mm pressed (free {SPRING_L:.1f}, solid {SPRING_SOLID:.1f})")
    if PRINT_SPRING:
        # A crest-to-crest wave spring estimate with a PETG modulus of about 2000 MPa. Printed parts vary, so test it.
        k = spring_rate()
        have, climb, flank = return_budget()
        print(f"spring rate about {k:.1f} N/mm: {k * PRELOAD:.1f} N at rest, {k * (PRELOAD + STROKE):.1f} N pressed")
        print(f"return: {have:.1f} N at the last tooth against {climb:.1f} N to climb its {flank:.0f} degree flank "
              f"({have / climb:.1f}x); press peak about {k * (PRELOAD + STROKE) + climb:.0f} N")
    print(f"wrote cocoa_dispenser.step, cocoa_dispenser_pressed.step, {len(ps)} part STLs, cocoa_dispenser_plate.stl, labels.json "
          f"in {time.monotonic() - t_run:.0f} s" + ("" if USE_CACHE else " without the cache"))
