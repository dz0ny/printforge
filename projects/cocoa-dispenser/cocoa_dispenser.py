"""Cocoa duster for latte art, made with smlibpy.

Each press moves the cocoa cup down and the spring lifts it again.
On the way the rack clicks past a striker tongue in the lid: one tap per tooth, which shakes the cup.
The cocoa falls through the fine sieve onto a stencil that locks into the body bottom with a bayonet.
Three ribs in a triangle hold the cup on the rod, so nothing covers the middle of the sieve.
Parts: body, stencil, cocoa cup with the sieve and the rack rod, lid with tongue, button and a printed wave spring.
Z is up from the body underside and the rack faces +X.
Run `uv run cocoa_dispenser.py` for the STEPs, STLs and labels, or add `--serve` for the configurator.
"""
import math

from smlibpy import (Align, Box, Circle, Cylinder, Line, Plane, Polygon, Polyline, Sphere, ThreePointArc, Wire, X, Z,
                     loft, make_face)

# ☕ Coffee cup, only for the ghost view: the dispenser is held just above it.
CUP_D = 90.0         # Cup rim outside diameter.
CUP_H = 70.0         # Cup height below the rim.

# 🖨️ Printer. Every part prints flat, so X and Y use lines and Z uses layers.
NOZZLE = 0.4
LINE = 0.45          # Line width, about 1.1 x the nozzle.
LAYER = 0.16

# 🫙 Body: one tube with the stencil at the bottom, then the drop chamber and the cocoa cup.
HOP_H = 80.0         # Tube height above the cup's lowest point. [40:130].
WALL = 4 * LINE      # Tube wall, 4 lines. [1.2:4].

# ✋ Grip.
GRIP_RIBS = 12       # Number of vertical grip ribs: round rods half sunk into the tube wall. [0:24].
GRIP_D = 3.0         # Rib diameter.
GRIP_PROUD = 1.8     # Rib height out of the tube wall.

# 🕳️ Sieve: the floor of the cocoa cup, with fine holes that are vertical in the print.
SIEVE_D = 60.0       # Cocoa cup outside diameter, which slides in the body bore. [30:62].
SIEVE_T = 6 * LAYER  # Sieve floor thickness. [0.8:2].
SIEVE_HOLE = 0.8     # Hole diameter, 0.8 for cocoa and 0.6 to 0.7 for cinnamon. [0.6:1.2].
SIEVE_PITCH = 1.7    # Hole spacing on a hex grid, so the web is two lines at 0.45.

# 🧺 Cocoa cup wall and its play in the body bore.
SKIRT_H = 30.0       # Cup wall above the sieve floor, for a fill of 20 to 25 mm. [10:32].
SKIRT_W = 4 * LINE   # Cup wall, 4 lines. [1.2:3].
SIEVE_PLAY = 0.3     # Clearance per side of the cup in the body bore. [0.15:0.6].

# 🔺 Carrier: three ribs in a triangle from the cup rim up to the block that carries the rod.
RIB_W = 3.0          # Rib width across.
RIB_D = 3.0          # Rib depth along the radius.

# 🦷 Rod and rack: the tapper.
ROD_SQ = 6.0         # Rod square side.
RACK_PITCH = 3.0     # Tooth pitch along the rod, one tap per tooth, longer for a gentler flank. [1:4].
RACK_DEPTH = 1.3     # Tooth depth into the rod face.

# 🖼️ Stencil: a disc with a grip flange and a collar that goes up into the body bore from below.
STENCIL_T = 6 * LAYER  # Stencil disc thickness, which is also the grip flange. [0.8:2].
STENCIL_PLAY = 0.3   # Clearance per side of the collar in the bore. [0.15:0.6].
COLLAR_W = 3 * LINE  # Collar wall, 3 lines. [1.2:3].
HEART_W = 46.0       # Heart width; its lobes reach 26 mm from the centre. [15:50].
EAR_L = 10.0         # Reach of the two grip ears past the flange, to turn the stencil.
EAR_W = 14.0         # Ear width.
EAR_H = 5.0          # Height of each ear outside the bayonet band, a solid tab for the fingers.

# 🔒 Bayonet: three lugs on the collar, in L grooves in the body bottom.
LUG_H = 2.4          # Lug height.
LUG_D = 1.0          # Lug reach into the body wall.
LUG_A = 20.0         # Lug width in degrees.
LOCK_Z = 3.0         # Lug underside above the flange, which leaves body wall under the groove.
TWIST = 35.0         # Twist from the entry slot to the locked place, in degrees.
BAY_WALL = 4.0       # Body wall at the bayonet ring, from the bore out.
DETENT = 0.3         # Bump on the groove floor that the lug clicks over, so taps do not twist it loose.

# 🌫️ Drop chamber, so the hole pattern mixes into an even cloud of cocoa.
DROP_H = 20.0        # Height between the stencil lip and the sieve at full press. [8:40].

# 🔘 Lid and button travel.
STROKE = 10.0        # Button travel. [4:20].
ROD_PLAY = 0.3       # Clearance per side of the rod in the square guide of the lid. [0.15:0.6].
LID_T = 16 * LAYER   # Lid plate thickness. [1.6:5].
LID_PLUG = 6.0       # Depth of the lid plug in the tube.
LID_FIT = 0.2        # Clearance per side of the lid plug in the tube. [0.05:0.5].
POUR_ANGLE = 140.0   # Pour opening in the lid: an arc between the button and the plug, on the -X side. [0:220].

# 🧲 Lid hub and spring seat.
LID_R = 1.0          # Round on the top edge of the guide hub.
HUB_D = 14.0         # Guide hub diameter, with two lines of wall outside the tongue pocket.
HUB_DOWN = 9.0       # Hub reach below the plug, for a longer guide and room for the tongue.
SEAT_DEPTH = 8 * LAYER  # Spring seat depth in the lid top. [0.8:3].
SPRING_PLAY = 1.0    # Clearance per side around the spring in the seat and the button skirt. [0.3:2].

# 🔲 Button.
BTN_WALL = 4 * LINE  # Button skirt wall, 4 lines. [1.2:6].
BTN_TOP = 6.5        # Solid cap above the skirt, which holds the rod socket under the finger dimple.
SOCKET = 4.0         # Rod depth in the button socket.
ROD_PRESS = 0.05     # Tight socket clearance per side, for a drop of glue.

# 👅 Striker tongue: a finger in the lid hub that the rack clicks past.
TONGUE_T = 2 * LINE  # Tongue thickness of 2 lines, thin enough to flex 1 mm.
TONGUE_L = 12.0      # Tongue length from its root to the tip, long so the root bends little. [6:16].
TONGUE_W = 4.5       # Tongue width.
TONGUE_BITE = 1.0    # Reach of the tip into the teeth, which is the bend per tooth. [0.3:1.2].
TONGUE_FLEX = 1.2    # Free room behind the tongue, so it can swing out.

# 🧮 Tongue root and force estimates.
TONGUE_ROOT = 2.0    # Solid lid above the tongue root.
ROOT_R = 1.0         # Gusset at the tongue root on the flex side.
TOOTH_MU = 0.3       # Friction of the tongue tip on a tooth flank, PETG on PETG.
PETG_E = 2000.0      # Printed PETG modulus in MPa, for the tongue and spring force estimates.
SIEVE_LOAD = 1.0     # Weight in N that the spring lifts: the basket and the cocoa on it.

# 🌀 Spring: a printed wave spring or a bought metal spring.
PRINT_SPRING = True  # Print the wave spring, or use a bought metal spring. [0:1].
PRELOAD = 2.5        # Spring compression at rest, against rattle and for the return over the last tooth. [0.5:6].
WS_RINGS = 7         # Number of wave rings, softer and longer when more. [4:16].

# 〰️ Printed wave spring shape.
WS_D = 18.0          # Wave spring mean diameter, softer when larger.
WS_B = 4 * LINE      # Radial band width, 4 lines.
WS_T = 4 * LAYER     # Vertical band thickness: 4 layers of 0.16, 0.64 mm.
WS_H = 4.0           # Wave height, crest to trough.
WS_WAVES = 3         # Waves per ring, softer when fewer but with a flatter underside.
WS_END = 6 * LAYER   # Flat end ring thickness.
WS_JOIN = 0.3        # Overlap where the rings touch, so they print as one part.

# 🔩 Bought metal spring, when PRINT_SPRING is off.
METAL_OD = 19.0      # Outside diameter, for wire of 0.8 to 1 mm, so it goes over the lid hub. [18:22].
METAL_L = 32.0       # Free length. [24:40].
METAL_SOLID = 10.0   # Fully compressed length. [4:16].

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
SEAT_D = SPRING_OD + 2 * SPRING_PLAY
BTN_CAV_D = SPRING_OD + 2 * SPRING_PLAY
BTN_D = BTN_CAV_D + 2 * BTN_WALL
BTN_CAV = SPRING_L - PRELOAD - STROKE - SEAT_DEPTH   # Skirt depth, so the spring at rest fits exactly.
HOP_ID = SIEVE_D + 2 * SIEVE_PLAY      # Tube bore, which guides the cup.
HOP_D = HOP_ID + 2 * WALL
COLLAR_OD = HOP_ID - 2 * STENCIL_PLAY
COLLAR_ID = COLLAR_OD - 2 * COLLAR_W    # The window under the cocoa, over the coffee cup.
CAP_DROP = 0.5                          # Gap under the body bottom: the locked lugs hang on the groove floor.
GROOVE_FLOOR = LOCK_Z - CAP_DROP        # Groove floor above the body underside.
GROOVE_H = LUG_H + CAP_DROP + DETENT + 0.2  # Groove height, so the lug can lift over the bump.
COLLAR_H = LOCK_Z + LUG_H + 2.0         # Collar height above the flange.
BAY_H = GROOVE_FLOOR + GROOVE_H + 2.0   # Height of the thick bayonet ring in the body.
STENCIL_TOP = COLLAR_H - CAP_DROP       # Collar top in the use frame.
BODY_Z = STENCIL_TOP + DROP_H           # Body frame origin: the sieve underside at full press.
BAY_ANGLES = [90.0 + 120.0 * k for k in range(3)]  # Entry slot centres.
HUB_BOT = HOP_H - LID_PLUG              # Lid hub underside, body frame.
LID_TOP = HOP_H + LID_T
HUB_TOP = LID_TOP                       # The hub is flush with the lid top, inside the spring.
HUB_LOW = HUB_BOT - HUB_DOWN            # Hub underside, body frame.
TRAVEL = STROKE                         # Cup travel: the button lands on the lid at full press.
SIEVE_REST = TRAVEL                     # Cup underside at rest, body frame.
CARRIER_D = ROD_D + 2 * ROD_PRESS + 2 * 4 * LINE  # Round carrier block, with 4 lines outside the socket corners.
CARRIER_H = 8.0                         # Carrier block height, which the rod grows out of.
CARRIER_TOP = HUB_LOW - 0.05            # Carrier top at rest, 0.05 mm under the hub, which is the up stop.
ROD_BOT = CARRIER_TOP - SOCKET          # Rod bottom at rest, body frame, in the carrier socket.
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
    # The spring also lifts the basket and the cocoa on it.
    have = spring_rate() * (PRELOAD + RACK_PITCH) - SIEVE_LOAD if PRINT_SPRING else float("nan")
    return have, climb, math.degrees(flank)


def check_design():
    assert SIEVE_HOLE >= 2 * NOZZLE, "sieve holes this small close up"
    assert SIEVE_PITCH - SIEVE_HOLE >= 2 * LINE - 0.01, "sieve webs thinner than two lines"
    assert HEART_W < SIEVE_D - 4, "the heart is wider than the sieve area"
    heart_r = max(math.hypot(x, y) for x, y in heart_points(HEART_W))
    assert heart_r < COLLAR_ID / 2 - 0.5, f"the heart reaches {heart_r:.1f} mm, past the collar"
    assert GROOVE_FLOOR >= 1.5, "too little body wall under the bayonet grooves"
    assert BAY_WALL - LUG_D - 0.2 >= 2 * LINE, "the body wall behind the grooves is thinner than two lines"
    assert HOP_D / 2 + GRIP_PROUD <= HOP_ID / 2 + BAY_WALL, "the grip ribs stick out past the bayonet band they stand on"
    if EAR_L > 0:
        assert HOP_D / 2 + EAR_L > HOP_ID / 2 + BAY_WALL + 4, "the ears end under the bayonet band: lengthen EAR_L"
    assert TWIST > LUG_A + 4, "the twist is too short to move the lug past the entry slot"
    assert DROP_H >= 8, "the drop chamber is too low for an even cloud"
    assert WS_D - WS_B > ROD_D + 1 if PRINT_SPRING else SPRING_OD - 1.6 > ROD_D + 1, "the spring does not clear the rod's diagonal"
    assert SPRING_OD + 1 <= BTN_CAV_D and SPRING_OD + 2 * WS_END_LAP <= SEAT_D, "the spring does not fit"
    assert SPRING_REST < SPRING_L, "no spring preload: shorten BTN_CAV or use a longer spring"
    assert SPRING_PRESSED > SPRING_SOLID + 0.5, "the spring goes solid before the button lands"
    assert ROD_TOP - BTN_Z + BTN_TOP - SOCKET > 0
    assert BTN_CAV_D > ROD_D + 2, "the rod's diagonal does not fit the button cavity"
    assert BTN_CAV > 3, "the spring is too short for this stroke"
    assert SEAT_D < HOP_D - 6, "the spring seat is wider than the lid"
    assert SPRING_OD - 2 * (WS_B if PRINT_SPRING else 0.8) > ROD_D + 2, "the rod does not fit inside the spring"
    spring_id = WS_D - WS_B - 2 * WS_END_LAP if PRINT_SPRING else METAL_OD - 2  # Wire of up to 1 mm.
    assert spring_id > HUB_D + 1, "the hub does not fit inside the spring"
    if PRINT_SPRING:
        per_ring = (SPRING_L - SPRING_PRESSED) / WS_RINGS
        assert per_ring <= 0.5 * (WS_H - WS_JOIN), "each ring bends more than half its wave: add rings"
        assert WS_B >= 2 * LINE - 0.01 and WS_T >= 3 * LAYER - 0.01, "the wave band is too thin to print"
        have, climb, flank = return_budget()
        assert spring_rate() * PRELOAD > 1.5 * SIEVE_LOAD, "the spring cannot hold the full basket up at rest: raise PRELOAD"
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
    assert TIP_Z > CARRIER_TOP + RACK_PITCH, "the tongue tip at rest is too close to the carrier block"
    assert RACK_Z0 + RACK_L < ROD_TOP - ROD_BOT - SOCKET - 1, "the rack runs into the button socket"
    # The cup and its stops.
    assert TRAVEL > 2 * RACK_PITCH, "the cup travels less than two teeth"
    assert SKIRT_W >= 2 * LINE - 0.01, "the basket wall is thinner than two lines"
    assert CARRIER_TOP - CARRIER_H - CARRIER_D > SIEVE_REST + SIEVE_T + SKIRT_H, "the carrier is too low for its ribs"
    assert SIEVE_REST + SIEVE_T + SKIRT_H < HUB_BOT - 2, "the cup rim reaches the lid plug at rest"


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

def sector(r0, r1, a0, a1, h, z):
    """Return a ring sector from radius r0 to r1 and angle a0 to a1 in degrees, h high from z."""
    k = 24
    pts = [(0.0, 0.0)] + [(2 * r1 * math.cos(math.radians(a0 + (a1 - a0) * i / k)),
                           2 * r1 * math.sin(math.radians(a0 + (a1 - a0) * i / k))) for i in range(k + 1)]
    wedge = Polygon(pts).translate(0, 0, z - 1).extrude(h + 2)
    ring = cyl(2 * r1, h, z) - cyl(2 * r0, h + 2, z - 1) if r0 > 0 else cyl(2 * r1, h, z)
    return ring & wedge


STENCIL_DEPS = ["STENCIL_T", "COLLAR_OD", "COLLAR_ID", "COLLAR_H", "HOP_D", "HOP_ID", "HEART_W", "LUG_H", "LUG_D", "LUG_A",
                "LOCK_Z", "TWIST", "CAP_DROP", "BAY_ANGLES", "EAR_L", "EAR_W", "EAR_H", "BAY_WALL"]


def stencil():
    return cached("stencil", STENCIL_DEPS, stencil_build)


def stencil_build():
    """Return the stencil, locked: a grip flange with the heart, a collar and three bayonet lugs.

    The flange is as wide as the tube, with notches round its edge and two ears with lips for the fingers.
    The lugs stand 1 mm out of the collar, so their undersides print as short overhangs.
    """
    st = cyl(HOP_D, STENCIL_T, -STENCIL_T)
    for k in range(18):
        a = 2 * math.pi * (k + 0.5) / 18
        st -= cyl(2.0, STENCIL_T + 2, -STENCIL_T - 1).translate(HOP_D / 2 * math.cos(a), HOP_D / 2 * math.sin(a), 0)
    if EAR_L > 0:
        # Two ears at +X and -X. Outside the bayonet band each ear is a solid tab EAR_H high for the fingers.
        r_tip = HOP_D / 2 + EAR_L - EAR_W / 2
        for a in (0, 180):
            h = STENCIL_T + CAP_DROP + EAR_H
            ear = rect(r_tip - HOP_D / 2 + 2, EAR_W, h, (HOP_D / 2 - 2 + r_tip) / 2, 0, -STENCIL_T)
            ear += cyl(EAR_W, h, -STENCIL_T).translate(r_tip, 0, 0)
            # Under the band the ear stays as thin as the flange, with 1 mm of room to the band.
            # A flat inner face keeps the tab corners square.
            ear -= rect(2 * (HOP_ID / 2 + BAY_WALL + 1.0), EAR_W + 2, h + 2, 0, 0, 0.0)
            st += ear.rotate(Z, a)
    st += cyl(COLLAR_OD, COLLAR_H + 0.01, -0.01) - cyl(COLLAR_ID, COLLAR_H + 2, -1)
    st -= Polygon(heart_points(HEART_W)).translate(0, 0, -STENCIL_T - 1).extrude(STENCIL_T + 2)
    return st.translate(0, 0, -CAP_DROP) + bayonet_lugs(COLLAR_OD / 2)


def sieve_holes(r_max):
    """Return a hex grid of holes over the floor, each hole fully inside r_max."""
    return [(x, y) for x, y in hex_points(r_max, SIEVE_PITCH) if math.hypot(x, y) <= r_max - SIEVE_HOLE / 2 - LINE]


def holed_disc(d, pts):
    """Return a disc of diameter d and thickness SIEVE_T with a hole at each point.

    The holes go out of the 2D outline before the extrusion, which is two times faster than solid cuts.
    """
    sk = Circle(d / 2) - [Circle(SIEVE_HOLE / 2).translate(x, y, 0) for x, y in pts]
    return sk.extrude(SIEVE_T)


SHELL_DEPS = ["HOP_D", "HOP_ID", "HOP_H", "WALL", "GRIP_RIBS", "GRIP_D", "GRIP_PROUD", "CAP_DROP",
              "BAY_WALL", "BAY_H", "GROOVE_FLOOR", "GROOVE_H", "LUG_D", "LUG_A", "TWIST", "DETENT", "BAY_ANGLES", "BODY_Z"]
SIEVE_DEPS = ["SIEVE_D", "SIEVE_T", "SIEVE_HOLE", "SIEVE_PITCH", "SKIRT_H", "SKIRT_W", "RIB_W", "RIB_D",
              "CARRIER_D", "CARRIER_H", "CARRIER_TOP", "SIEVE_REST", "SOCKET", "ROD_SQ", "ROD_PRESS"]


def bayonet_grooves():
    """Return the three L groove cutters for a bayonet band whose rim is at z = 0 and which goes up from it."""
    ri = HOP_ID / 2
    r1 = ri + LUG_D + 0.2
    half = LUG_A / 2 + 2
    cut = None
    for a in BAY_ANGLES:
        g = sector(ri - 1, r1, a - half, a + half, GROOVE_FLOOR + GROOVE_H + 1, -1)
        g += sector(ri - 1, r1, a - half, a + TWIST + half, GROOVE_H, GROOVE_FLOOR)
        cut = g if cut is None else cut + g
    return cut


def bayonet_bumps():
    """Return the click bumps on the groove floors, just past the entry slots, in the frame of bayonet_grooves()."""
    ri = HOP_ID / 2
    r1 = ri + LUG_D + 0.2
    half = LUG_A / 2 + 2
    bumps = [sector(ri - 0.01, r1 + 0.01, a + half + 1, a + half + 4, DETENT + 0.01, GROOVE_FLOOR - 0.01) for a in BAY_ANGLES]
    return bumps[0] + bumps[1] + bumps[2]


def bayonet_lugs(r_in):
    """Return the three locked lugs on a collar of radius r_in, in the frame of bayonet_grooves() with a CAP_DROP gap."""
    lugs = [sector(r_in - 0.2, HOP_ID / 2 + LUG_D - 0.2, a + TWIST - LUG_A / 2, a + TWIST + LUG_A / 2, LUG_H, LOCK_Z)
            for a in BAY_ANGLES]
    return (lugs[0] + lugs[1] + lugs[2]).translate(0, 0, -CAP_DROP)


def top_frame(shape, zt):
    """Turn a bayonet shape from the bottom frame upside down, onto a rim at zt."""
    return shape.rotate(X, 180).translate(0, 0, zt)


def shell_build():
    """Return the body in the use frame: the tube, a bayonet band at each end and the grip ribs.

    The bands are thicker than the tube for the grooves, and 45 degree faces join them to the tube.
    The top band holds the lid the same way as the bottom band holds the stencil.
    The tube rim is CAP_DROP under the lid plate, so the lid lugs can lift over the click bumps.
    """
    zt = BODY_Z + HOP_H - CAP_DROP
    ri, ro, rb = HOP_ID / 2, HOP_D / 2, HOP_ID / 2 + BAY_WALL
    b = cyl(HOP_D, zt)
    b += Polygon((ro - 0.5, 0), (rb, 0), (rb, BAY_H), (ro - 0.5, BAY_H + rb - ro + 0.5)).on(Plane.XZ).revolve(Z)
    b += Polygon((ro - 0.5, zt), (rb, zt), (rb, zt - BAY_H), (ro - 0.5, zt - BAY_H - rb + ro - 0.5)).on(Plane.XZ).revolve(Z)
    if GRIP_RIBS > 0:
        # Round vertical rods half sunk into the tube wall. They stand on the bayonet band, which is wider,
        # so their bottoms do not print in the air.
        rc = ro - GRIP_D / 2 + GRIP_PROUD
        z0, z1 = BAY_H - 0.01, zt - BAY_H + 0.01
        for k in range(GRIP_RIBS):
            a = 2 * math.pi * (k + 0.5) / GRIP_RIBS
            b += cyl(GRIP_D, z1 - z0, z0).translate(rc * math.cos(a), rc * math.sin(a), 0)
    b -= cyl(HOP_ID, zt + 2, -1)  # The bore, open at both ends: the cocoa cup slides in it.
    # Each L groove: an entry slot in from the rim, then a leg along the twist.
    grooves = bayonet_grooves()
    b -= grooves
    b -= top_frame(grooves, zt)
    if DETENT > 0:
        bumps = bayonet_bumps()
        b += bumps + top_frame(bumps, zt)
    return b


def body():
    """Return the body: one tube from the coffee cup to the lid."""
    return cached("shell", SHELL_DEPS, shell_build)


def body_plain():
    """Return the body for the checks. The body has no holes now, so it is the same part."""
    return body()


def sieve_build(holes=True):
    """Return the sieve basket on z = 0, at rest height in its own frame.

    The basket is a holed floor with a tall wall, so it holds the cocoa.
    Three ribs go from the wall up and in to a block with a square socket for the rod.
    The ribs stand 30 degrees from vertical, and a steep cone holds the block, so it prints with no supports.
    """
    r_out = SIEVE_D / 2
    r_in = r_out - SKIRT_W
    top = CARRIER_TOP - SIEVE_REST
    blk_bot = top - CARRIER_H
    pts = sieve_holes(r_in) if holes else []
    s = holed_disc(SIEVE_D, pts)
    s += cyl(SIEVE_D, SKIRT_H + 0.1, SIEVE_T - 0.1) - cyl(2 * r_in, SKIRT_H + 2, SIEVE_T - 1)
    # The round block, and a steep cone of the same diameter under it.
    cr = CARRIER_D / 2
    s += cyl(CARRIER_D, top - blk_bot, blk_bot)
    s += Polygon((0, blk_bot - 1.5 * cr), (cr, blk_bot), (cr, blk_bot + 0.5), (0, blk_bot + 0.5)).on(Plane.XZ).revolve(Z)
    w = RIB_D + 0.5
    rib = Polygon((r_in - RIB_D, SIEVE_T - 0.1), (r_in + 0.5, SIEVE_T - 0.1), (w - RIB_D, blk_bot + 1.0),
                  (-RIB_D, blk_bot + 1.0))
    rib = rib.on(Plane.XZ.offset(-RIB_W / 2)).extrude(RIB_W)
    for k in range(3):
        s += rib.rotate(Z, 90 + 120 * k)
    sq = ROD_SQ + 2 * ROD_PRESS
    s -= rect(sq, sq, SOCKET + 1, 0, 0, top - SOCKET)
    return s


CUP_DEPS = SIEVE_DEPS + ["RACK_PITCH", "RACK_DEPTH", "RACK_Z0", "RACK_TEETH", "ROD_TOP", "ROD_BOT", "BODY_Z"]


def cup_build():
    """Return the cocoa cup on z = 0: the sieve basket and the rod as one part.

    The rack teeth print upright, with their down flank 34 degrees from vertical.
    """
    return sieve_build() + rod().translate(0, 0, -(BODY_Z + SIEVE_REST))


def cup(press=0.0):
    """Return the cocoa cup in the use frame. The press moves it down."""
    return cached("cup", CUP_DEPS, cup_build).translate(0, 0, BODY_Z + SIEVE_REST - press)


def cup_plain(press=0.0):
    """Return the cup with no holes, for the checks and the drawing."""
    return (cached("sieve-plain", SIEVE_DEPS, sieve_build, False).translate(0, 0, BODY_Z + SIEVE_REST - press)
            + rod(press))


def tongue_solid():
    """Return the striker tongue in the body frame: a finger that hangs from the hub top on the +X side.

    Its body is just outside the guide hole.
    A 45 degree nub at the free end reaches ROD_PLAY + TONGUE_BITE inward, so only the nub rides the teeth.
    """
    x_body = ROD_SQ / 2 + ROD_PLAY
    reach = ROD_PLAY + TONGUE_BITE
    half = reach * (RACK_PITCH / 2) / RACK_DEPTH  # The nub flanks have the slope of the tooth flanks, so the nub sits in a valley.
    finger = rect(TONGUE_T, TONGUE_W, TONGUE_L + 0.5, x_body + TONGUE_T / 2, 0, TIP_Z)
    nub = Polygon((x_body + 0.01, TIP_Z), (x_body - reach, TIP_Z + half), (x_body + 0.01, TIP_Z + 2 * half))
    # A gusset on the flex side rounds the root, so the bend does not start at a sharp corner.
    x_out, root = x_body + TONGUE_T, TIP_Z + TONGUE_L
    gusset = Polygon((x_out - 0.01, root - ROOT_R), (x_out - 0.01, root + 0.01), (x_out + ROOT_R, root + 0.01))
    side = Plane.XZ.offset(-TONGUE_W / 2)
    return finger + nub.on(side).extrude(TONGUE_W) + gusset.on(side).extrude(TONGUE_W)


def lid(with_tongue=True):
    """Return the lid in the use frame. It locks into the body top with a bayonet, the same as the stencil below."""
    rb = HOP_ID / 2 + BAY_WALL
    plate = cyl(2 * rb, LID_T, HOP_H)
    plug_od = HOP_ID - 2 * LID_FIT
    plug = cyl(plug_od, LID_PLUG, HUB_BOT) - cyl(plug_od - 2 * 4 * LINE, LID_PLUG + 2, HUB_BOT - 1)
    hub = cyl(HUB_D, HUB_TOP - HUB_LOW, HUB_LOW)
    l = plate + plug + hub + top_frame(bayonet_lugs(plug_od / 2), HOP_H - CAP_DROP)
    l -= cyl(SEAT_D, SEAT_DEPTH + 1, LID_TOP - SEAT_DEPTH) - cyl(HUB_D, SEAT_DEPTH + 3, LID_TOP - SEAT_DEPTH - 1)
    sq = ROD_SQ + 2 * ROD_PLAY
    l -= rect(sq, sq, HUB_TOP - HUB_LOW + 2, 0, 0, HUB_LOW - 1)
    # The pocket the tongue swings in goes from the guide hole out through the tongue and its flex room.
    # It is a little wider than the tongue, and it goes from below the tip up to the root.
    x_in, x_out = ROD_SQ / 2 + ROD_PLAY - 0.01, ROD_SQ / 2 + ROD_PLAY + TONGUE_T + TONGUE_FLEX
    l -= rect(x_out - x_in, TONGUE_W + 1.2, TONGUE_L + 1.0, (x_in + x_out) / 2, 0, TIP_Z - 1.0)
    if POUR_ANGLE > 0:
        # The pour opening: an arc on the -X side, between the button and the plug.
        r0, r1 = BTN_D / 2 + 1.0, HOP_ID / 2 - LID_FIT - 4 * LINE - 1.0
        l -= sector(r0, r1, 180 - POUR_ANGLE / 2, 180 + POUR_ANGLE / 2, LID_T + 2, HOP_H - 1)
    if with_tongue:
        l += tongue_solid()
    if LID_R > 0:
        l = rounded(l, smallest_circles(l, LID_TOP, LID_TOP), LID_R, "lid")
    # Grip notches round the plate edge, cut after the round so it does not pick their small arcs.
    for k in range(18):
        a = 2 * math.pi * (k + 0.5) / 18
        l -= cyl(2.0, LID_T + 2, HOP_H - 1).translate(rb * math.cos(a), rb * math.sin(a), 0)
    return l.translate(0, 0, BODY_Z)


def rod(press=0.0):
    """Return the square rod, straight, with the rack on its +X face. Its bottom goes into the basket carrier."""
    r = rect(ROD_SQ, ROD_SQ, ROD_TOP - ROD_BOT)
    r -= Polygon(rack_profile()).on(Plane.XZ.offset(-(ROD_SQ / 2 + 1))).extrude(ROD_SQ + 2)
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
    for name, fn in (("stencil", stencil), ("body", body), ("lid", lid)):
        if name not in FIXED:
            FIXED[name] = fn()
    ps = {"stencil": FIXED["stencil"], "body": FIXED["body"], "lid": FIXED["lid"],
          "cup": cup(press), "button": button(press)}
    if PRINT_SPRING:
        ps["spring"] = spring(press)
    return ps


def build():
    """Return the assembly at rest as a list of separate parts."""
    check_design()
    return list(parts().values())


def drawing_shapes():
    """Return the assembly for the Drawing view of the configurator, with a sieve with no holes.

    The hidden-line step over the 1,000 sieve holes took minutes a view.
    """
    ps = parts()
    ps["cup"] = cup_plain()
    return list(ps.values())


def section_shapes():
    """Return the parts by name for the Section view of the configurator, with a cup with no holes."""
    ps = parts()
    ps["cup"] = cup_plain()
    return ps


def device():
    """Return the cup, and the bought spring when there is one, for the ghost view."""
    cup = (cyl(CUP_D, CUP_H, -CUP_H) - cyl(CUP_D - 6, CUP_H, -CUP_H + 4)).translate(0, 0, -STENCIL_T - CAP_DROP - 3.0)
    if PRINT_SPRING:
        return cup
    z = BODY_Z + LID_TOP - SEAT_DEPTH
    return cup + (cyl(SPRING_OD, SPRING_REST, z) - cyl(SPRING_OD - 1.6, SPRING_REST + 2, z - 1))


def features():
    zb = BODY_Z
    f = {
        "Heart": {"at": (0, 0, -STENCIL_T - CAP_DROP - 0.5), "normal": (0, 0, -1), "params": ["HEART_W"]},
        "Stencil flange": {"at": (HOP_D / 2 - 1.5, 0, -STENCIL_T - CAP_DROP - 0.5), "normal": (0, 0, -1),
                           "params": ["STENCIL_T", "STENCIL_PLAY", "COLLAR_W"]},
        "Bayonet": {"at": (HOP_ID / 2 + BAY_WALL + 0.5, 0, BAY_H / 2), "normal": (1, 0, 0),
                    "params": ["LUG_H", "LUG_D", "LUG_A", "LOCK_Z", "TWIST", "BAY_WALL", "DETENT"]},
        "Drop chamber": {"at": (HOP_D / 2 + 0.5, 0, zb - DROP_H / 2), "normal": (1, 0, 0), "params": ["DROP_H"]},
        "Body tube": {"at": (HOP_D / 2 + 0.5, 0, zb + HOP_H / 2), "normal": (1, 0, 0),
                      "params": ["HOP_H", "WALL", "SIEVE_PLAY", "GRIP_RIBS"]},
        "Pour opening": {"at": (-(BTN_D / 2 + HOP_ID / 2) / 2, 0, zb + LID_TOP + 0.5), "normal": (0, 0, 1),
                         "params": ["POUR_ANGLE"]},
        "Lid": {"at": (HOP_D / 2 - 4, 0, zb + LID_TOP + 0.5), "normal": (0, 0, 1),
                "params": ["LID_T", "LID_PLUG", "LID_FIT", "HUB_D", "HUB_DOWN"]},
        "Button": {"at": (0, 0, zb + BTN_Z + BTN_CAV + BTN_TOP + 0.5), "normal": (0, 0, 1),
                   "params": ["STROKE", "BTN_D", "BTN_CAV", "BTN_TOP"]},
        "Sieve": {"at": (SIEVE_D / 2 - 8, 0, zb + SIEVE_REST - 0.5), "normal": (0, 0, -1),
                  "params": ["SIEVE_D", "SIEVE_HOLE", "SIEVE_PITCH", "SKIRT_H"]},
        "Carrier rib": {"at": (0, 14, zb + (SIEVE_REST + CARRIER_TOP) / 2), "normal": (0, 1, 0),
                        "params": ["RIB_W", "RIB_D"]},
        "Rack": {"at": (ROD_SQ / 2 + 0.5, 0, zb + ROD_BOT + RACK_Z0 + RACK_L / 2), "normal": (1, 0, 0),
                 "params": ["RACK_PITCH", "RACK_DEPTH", "STROKE", "ROD_SQ", "ROD_PLAY"]},
        "Striker tongue": {"at": (ROD_SQ / 2 + ROD_PLAY + TONGUE_T + 0.3, 0, zb + TIP_Z + TONGUE_L / 2), "normal": (1, 0, 0),
                           "params": ["TONGUE_T", "TONGUE_L", "TONGUE_W", "TONGUE_BITE", "TONGUE_FLEX", "TONGUE_ROOT"]},
        "Spring": {"at": (SPRING_OD / 2 + 0.5, 0, zb + LID_TOP + STROKE / 2), "normal": (1, 0, 0),
                   "params": ["PRINT_SPRING", "WS_D", "WS_T", "WS_H", "WS_WAVES", "WS_RINGS"]},
    }
    return f


def labels():
    out = {"_views": {"front": "Front (key side)", "top": "Button side", "bottom": "Cup side"}}
    for name, f in features().items():
        out[name] = {"at": list(f["at"]), "normal": list(f["normal"])}
    return out


# Print orientation per part: "flip" turns it upside down. The cup prints as used, sieve down.
PRINT_FLIP = {"stencil": "", "body": "", "cup": "", "lid": "flip", "button": "flip", "spring": ""}


def for_print(p, turn):
    if turn == "flip":
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
    # A part that is almost the same at both ends, like the spring, may differ a little; a wrong flip differs a lot.
    assert lo >= 0.9 * hi, f"{name}: more material at the top than on the bed, check the flip"
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
    pressed = parts(press=TRAVEL)  # Full press: the basket is on the ledge.
    export_step(list(pressed.values()), "cocoa_dispenser_pressed.step")
    taps = STROKE / RACK_PITCH
    print(f"one press: about {taps:.0f} taps down and {taps:.0f} up; rack {RACK_L:.1f} mm, {RACK_TEETH} teeth")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # The tongue must be on the rack at rest and at full press, and bite by TONGUE_BITE and no more.
    tongue = tongue_solid().translate(0, 0, BODY_Z)
    # The "loose" state moves the rod away from the tongue by the full play, as a printed guide can let it.
    for state, press, shift in (("rest", 0.0, 0.0), ("pressed", TRAVEL, 0.0), ("loose", 0.0, -ROD_PLAY)):
        tip_rod_z = TIP_Z - (ROD_BOT - press)  # Tip height in the rod frame.
        assert RACK_Z0 + 1 < tip_rod_z < RACK_Z0 + RACK_L - 1, f"{state}: the tongue tip is off the rack"
        # Against the plain square of the rod the nub must reach in by the bite, and no more.
        # Against the toothed rod it overlaps less, because it sits in a tooth valley.
        env = rect(ROD_SQ, ROD_SQ, ROD_TOP - ROD_BOT, shift, 0, BODY_Z + ROD_BOT - press)
        v_env, v_rod = shared(tongue, env), shared(tongue, rod(press).translate(shift, 0, 0))
        assert v_env > 0.05, f"{state}: the tongue does not reach the rod"
        assert v_env < TONGUE_BITE ** 2 * TONGUE_W * 2, f"{state}: the tongue is buried in the rod"
        assert v_rod < v_env + 0.01, f"{state}: the tongue is not over the teeth"
        print(f"tongue {state}: nub reaches {v_env:.2f} mm3 into the rod's square, {v_rod:.2f} mm3 into the teeth")
    # Interference in the use frame, at rest and at full press.
    # The check uses the lid without its tongue, because the design wants the bite of the tongue.
    for state, pp in (("rest", ps), ("pressed", pressed)):
        pp = dict(pp)
        pp["lid"] = lid(with_tongue=False)
        pp["cup"] = cup_plain(0.0 if state == "rest" else TRAVEL)
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
    layout = {"body": (2, 2), "stencil": (76, 2), "lid": (166, 2), "cup": (2, 76), "button": (68, 76),
              "spring": (106, 76)}
    boxes = []
    if PRINT_SPRING:
        ps["spring"] = wave_spring()  # The spring prints at its free length.
    for name, p in ps.items():
        assert p.is_valid(), f"{name}: invalid solid"
        assert len(p.solids()) == 1, f"{name}: not one solid"
        pr = for_print(p, PRINT_FLIP[name])
        # The STL goes in the cache with the part: the 1,000 holes of the body take a long time to mesh.
        stl_key = KEYS.get("shell" if name == "body" else name)
        if name == "spring":
            stl_key = part_key("spring-free", SPRING_DEPS, wave_spring)
        cached_stl = CACHE_DIR / f"{name}-{stl_key}-{PRINT_FLIP[name] or 'up'}.stl" if (USE_CACHE and stl_key) else None
        if cached_stl and cached_stl.exists():
            shutil.copyfile(cached_stl, f"{name}.stl")
        else:
            slab_test(pr, name)
            # The 871 tiny sieve holes mesh fast with a coarse angle.
            export_stl(pr, f"{name}.stl", tolerance=0.05, angle=30.0 if name == "cup" else 12.0)
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
        print(f"return: {have:.1f} N net of the basket load at the last tooth against {climb:.1f} N to climb its {flank:.0f} degree flank "
              f"({have / climb:.1f}x); press peak about {k * (PRELOAD + STROKE) + climb:.0f} N")
    print(f"wrote cocoa_dispenser.step, cocoa_dispenser_pressed.step, {len(ps)} part STLs, cocoa_dispenser_plate.stl, labels.json "
          f"in {time.monotonic() - t_run:.0f} s" + ("" if USE_CACHE else " without the cache"))
