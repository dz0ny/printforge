"""Cocoa duster for latte art with a shutter: press the button on top, a sieve plate
turns open for one dose, the spring turns it closed again. A slide-in stencil (a heart
by default) shapes the dose on the cup. Made with CadQuery, no bought parts.

Eight printed parts (or seven and a bought metal spring, PRINT_SPRING = False):
  Stand    sits on the cup rim, holds the stencil in a slot and centres the body.
  Stencil  slides into the stand from the front; a lip makes it a tray for the spill.
  Body     the cocoa hopper. Its floor is the fixed sieve plate: 1 mm holes in six
           30-degree sectors, solid between them.
  Rotor    a plate that lies on the sieve plate, with six open sectors. At rest its
           solid sectors cover the holes (closed). A square follower in its boss
           rides on the twisted rod.
  Rod      a square rod. Its lower part is twisted: pushing it down through the
           rotor's follower turns the rotor ROT_ANGLE degrees (a push drill). The
           upper part is straight and runs in the lid's square hole, so the rod
           itself cannot turn.
  Lid      push-fit on the hopper, square guide hole, spring seat.
  Button   push-fit on the rod top; its skirt hides the spring and is the end stop.
  Spring   PETG wave spring around the rod.

Use frame: Z up, z = 0 is the cup rim (the stand's underside), the stencil tab
points to -Y (the front). One press turns the rotor open: its open sectors line up
with the hole sectors, the rotor edge shears the cocoa through, and the spring turns
it closed. The dose is the open time and the hole area; nothing falls out at rest.
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

# 🕳️ Sieve plate. The body floor; holes are vertical in the print.
SIEVE_D = 48.0       # Sieve diameter: the rotor sits inside it. Heart + 8 mm. [30:62]
SIEVE_T = 6 * LAYER  # Plate thickness. [0.8:2]
SIEVE_HOLE = 1.0     # Hole diameter. 1.0 is the smallest that stays open with a 0.4 nozzle. [0.8:2]
SIEVE_PITCH = 2.0    # Hole spacing, hex grid. Web = pitch - hole. [1.6:4]
SECTORS = 6          # Hole sectors; the same number of solid sectors between them. [4:8]
HOLE_R_MIN = 8.0     # Holes start outside the rotor boss. [6:12]

# 🔄 Rotor and rod. The push-to-turn shutter.
ROTOR_T = 6 * LAYER  # Rotor plate thickness. [0.8:2]
ROTOR_GAP = 0.3      # Rotor edge clearance to the sieve cone. [0.2:0.6]
ROT_ANGLE = 30.0     # Rotor turn per full press, degrees: one sector pitch. Derived from SECTORS.
OPEN_SHRINK = 2.0    # Rotor open sectors are this much narrower than a sector, degrees each side, so closed is closed. [0.5:4]
BOSS_D = 13.0        # Rotor boss diameter. [10:18]
BOSS_H = 16.0        # Rotor boss height; the follower is its top FOLLOW_T. [12:24]
FOLLOW_T = 6 * LAYER  # Follower thickness. Thin, because the rod twists through it. [0.8:2]
FOLLOW_PLAY = 0.35   # Follower clearance per side on the square rod. [0.2:0.6]
ROD_SQ = 6.0         # Rod square side. [5:9]
PIVOT_H = 1.5        # Pivot post height: the printed plain bearing under the rotor boss. [1:3]
PIVOT_PLAY = 0.25    # Clearance per side between the post and the rotor bore. [0.15:0.5]
KEEPER_H = 1.0       # Snap ridge above the rotor edge, 45 degree underside, keeps the rotor down. [0:1.5]
VANE_H = 3.0         # Two stirring vanes on the rotor top. [0:6]

# 🖼️ Stencil. Slides into the stand from the front.
STENCIL_D = 82.0     # Stencil disc diameter. [70:95]
STENCIL_T = 6 * LAYER  # Stencil thickness. [0.8:2]
STENCIL_LIP = 1.5    # Lip around the disc, so the spill stays on the stencil. [0:3]
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

# 🔘 Lid and button.
STROKE = 10.0        # Button travel. [4:20]
ROD_PLAY = 0.3       # Clearance per side of the rod in the lid's square guide. [0.15:0.6]
LID_T = 16 * LAYER   # Lid plate thickness. [1.6:5]
LID_PLUG = 6.0       # Depth of the lid plug inside the hopper. [3:12]
LID_FIT = 0.2        # Clearance per side of the lid plug in the hopper. [0.05:0.5]
HUB_D = 13.0         # Lid guide hub diameter. [10:20]
SEAT_DEPTH = 8 * LAYER  # Spring seat depth in the lid top. [0.8:3]
SPRING_PLAY = 1.0    # Clearance per side around the spring in the seat and the button skirt. [0.3:2]
BTN_WALL = 9 * LINE  # Button skirt wall. [1.2:6]
BTN_TOP = 8.0        # Solid cap above the skirt; holds the rod socket. [5:14]
SOCKET = 6.0         # Rod depth in the button. [3:10]
ROD_PRESS = 0.05     # Socket clearance per side; tight, add a drop of glue. [0:0.2]

# 🌀 Spring. A printed PETG wave spring, or a bought metal one.
PRINT_SPRING = True  # True: print the wave spring. False: buy a metal spring.
PRELOAD = 2.0        # Spring compression at rest, so the button does not rattle. [0.5:5]
WS_D = 20.0          # Wave spring mean diameter. Larger is softer. [12:30]
WS_B = 4 * LINE      # Band width, radial, 4 lines. [1.2:4]
WS_T = 4 * LAYER     # Band thickness, vertical, 4 layers. Thinner is much softer. [0.6:2]
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
ROT_ANGLE = 180.0 / SECTORS
SECTOR = 360.0 / SECTORS
ROD_FOOT = STROKE + PIVOT_H + 0.5          # Rod bottom above the sieve plate at rest; it stops above the post.
PIVOT_D = ROD_D + 2 * 0.4 - 2 * PIVOT_PLAY  # Post diameter: the rotor bore less the play.
TWIST_L = BOSS_H - ROD_FOOT + STROKE + 2   # Twisted length: the follower rides on it over the whole stroke.
TWIST_DEG = ROT_ANGLE * TWIST_L / STROKE
SEAT_D = SPRING_OD + 2 * SPRING_PLAY
BTN_CAV_D = SPRING_OD + 2 * SPRING_PLAY
BTN_D = BTN_CAV_D + 2 * BTN_WALL
BTN_CAV = SPRING_L - PRELOAD - STROKE - SEAT_DEPTH   # Skirt depth: the spring at rest fits exactly.
HOP_ID = HOP_D - 2 * WALL
SLOT_H = STENCIL_T + STENCIL_LIP + SLOT_PLAY
STAND_TOP = STAND_BASE + SLOT_H
SLOT_R = STENCIL_D / 2 + SLOT_SIDE
BODY_Z = STAND_TOP                      # Body underside in the use frame.
HUB_BOT = HOP_H - LID_PLUG              # Lid hub underside, body frame.
LID_TOP = HOP_H + LID_T
ROD_BOT = SIEVE_T + ROD_FOOT            # Rod bottom at rest, body frame.
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
    assert BOSS_D > ROD_D + 2 * FOLLOW_PLAY + 2 * 2 * LINE, "the rotor boss wall is thinner than two lines"
    assert TWIST_L + 2 < HUB_BOT - ROD_BOT, "the twisted rod reaches into the lid: lower BOSS_H"
    assert BOSS_H - FOLLOW_T - ROD_FOOT >= 1.0, "the rod bottom is above the follower at rest: raise BOSS_H"
    assert HOLE_R_MIN > BOSS_D / 2 + 1, "holes start under the rotor boss"
    assert PIVOT_D > ROD_D - 1, "the pivot post is thinner than the rod"
    assert OPEN_SHRINK * 2 < SECTOR / 2, "the open sectors vanished"
    assert WS_D - WS_B > ROD_D + 1 if PRINT_SPRING else SPRING_OD - 1.6 > ROD_D + 1, "the spring does not clear the rod's diagonal"
    follow_twist = ROT_ANGLE / STROKE * FOLLOW_T
    assert ROD_SQ / 2 * math.sin(math.radians(follow_twist)) < FOLLOW_PLAY, \
        "the follower is too thick for the twist: it binds; thin FOLLOW_T or add FOLLOW_PLAY"
    assert SPRING_OD + 1 <= BTN_CAV_D and SPRING_OD <= SEAT_D, "the spring does not fit"
    assert SPRING_REST < SPRING_L, "no spring preload: shorten BTN_CAV or use a longer spring"
    assert SPRING_PRESSED > SPRING_SOLID + 0.5, "the spring goes solid before the button lands"
    assert ROD_TOP - BTN_Z + BTN_TOP - SOCKET > 0
    assert BTN_CAV_D > ROD_D + 2, "the rod's diagonal does not fit the button cavity"
    assert BTN_CAV > 3, "the spring is too short for this stroke"
    assert SEAT_D < HOP_D - 6, "the spring seat is wider than the lid"
    assert SPRING_OD - 2 * (WS_B if PRINT_SPRING else 0.8) > ROD_D + 2, "the rod does not fit inside the spring"
    if PRINT_SPRING:
        per_ring = (SPRING_L - SPRING_PRESSED) / WS_RINGS
        assert per_ring <= 0.5 * (WS_H - WS_JOIN), "each ring bends more than half its wave: add rings"
        assert WS_B >= 2 * LINE and WS_T >= 3 * LAYER, "the wave band is too thin to print"


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


def sector_points(r_min, r_max, pitch, hole, sectors, centre_deg=0.0):
    """Hex grid points inside the hole sectors (width SECTOR / 2, centred on k * SECTOR + centre_deg),
    with the whole hole inside the sector and the radius band."""
    out = []
    half = SECTOR / 4
    for x, y in hex_points(r_max, pitch):
        r = math.hypot(x, y)
        if r < r_min + hole / 2 or r > r_max - hole / 2:
            continue
        margin = math.degrees(math.asin((hole / 2 + LINE) / r))
        a = (math.degrees(math.atan2(y, x)) - centre_deg) % SECTOR
        a = min(a, SECTOR - a)
        if a <= half - margin:
            out.append((x, y))
    return out


def wedge(r_in, r_out, a0, a1, h, z=0.0):
    """A sector of a ring from angle a0 to a1 (degrees), extruded h from z."""
    n = max(4, int((a1 - a0) / 5))
    pts = [(r_out * math.cos(math.radians(a0 + (a1 - a0) * i / n)), r_out * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r_in * math.cos(math.radians(a1 - (a1 - a0) * i / n)), r_in * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return cq.Workplane("XY").workplane(offset=z).polyline(pts).close().extrude(h)


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
    if STENCIL_LIP > 0:
        st = st.union(cq.Workplane("XY").workplane(offset=STENCIL_T).circle(STENCIL_D / 2).circle(STENCIL_D / 2 - 3 * LINE).extrude(STENCIL_LIP))
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
    pts = sector_points(HOLE_R_MIN, r0, SIEVE_PITCH, SIEVE_HOLE, SECTORS)
    if pts:
        holes = cq.Workplane("XY").workplane(offset=-1).pushPoints(pts).circle(SIEVE_HOLE / 2).extrude(SIEVE_T + 2)
        b = b.cut(holes)
    if KEEPER_H > 0:
        # Rotor keeper: a ridge on the cone just above the rotor, 45 degree underside, the
        # rotor snaps under it. Inner radius = rotor radius - 0.3 so it holds.
        zk = SIEVE_T + ROTOR_T + 0.3
        ri = r0 - ROTOR_GAP - 0.5
        # Profile: inner face from zk up KEEPER_H, 2 mm into the cone, 45 degree underside.
        # Profile: inner face at ri, a 0.8 mm flat underside over the rotor edge, then 45 degrees out.
        ro = r0 - ROTOR_GAP + 0.3  # Just outside the rotor edge.
        keeper = cq.Workplane("XZ").polyline([(ri, zk + KEEPER_H), (ri + 2.5, zk + KEEPER_H), (ri + 2.5, zk - (2.5 - (ro - ri))),
                                              (ro, zk), (ri, zk)]).close().revolve(360, (0, 0, 0), (0, 1, 0))
        b = b.union(keeper)
    # Pivot post: the printed plain bearing the rotor boss turns on.
    b = b.union(cyl(PIVOT_D, SIEVE_T + PIVOT_H))
    return b.translate((0, 0, BODY_Z))


def lid():
    plate = cyl(HOP_D, LID_T, HOP_H)
    plug_od = HOP_ID - 2 * LID_FIT
    plug = cyl(plug_od, LID_PLUG, HUB_BOT).cut(cyl(plug_od - 2 * 4 * LINE, LID_PLUG + 2, HUB_BOT - 1))
    hub = cyl(HUB_D, LID_PLUG, HUB_BOT)
    l = plate.union(plug).union(hub)
    l = l.cut(cyl(SEAT_D, SEAT_DEPTH + 1, LID_TOP - SEAT_DEPTH))
    sq = ROD_SQ + 2 * ROD_PLAY
    l = l.cut(cq.Workplane("XY").workplane(offset=HUB_BOT - 1).rect(sq, sq).extrude(LID_PLUG + LID_T + 2))
    return l.translate((0, 0, BODY_Z))


def rod(press=0.0):
    """Square rod: twisted over TWIST_L at the bottom, straight above. Built so the
    straight part is axis-aligned (it runs in the lid's square hole)."""
    twist = cq.Workplane("XY").rect(ROD_SQ, ROD_SQ).twistExtrude(TWIST_L, TWIST_DEG)
    twist = twist.rotate((0, 0, 0), (0, 0, 1), -TWIST_DEG)  # Top of the twist now axis-aligned.
    straight = cq.Workplane("XY").workplane(offset=TWIST_L - 0.01).rect(ROD_SQ, ROD_SQ).extrude(ROD_TOP - ROD_BOT - TWIST_L + 0.01)
    r = twist.union(straight)
    return r.translate((0, 0, BODY_Z + ROD_BOT - press))


def rotor_angle(press=0.0):
    """Rotor orientation in the use frame for a given press: the twist angle at the follower."""
    z_follow = BOSS_H - FOLLOW_T / 2 - ROD_FOOT + press  # Follower height above the rod's bottom.
    return -TWIST_DEG + TWIST_DEG * z_follow / TWIST_L


def rotor_part():
    """The rotor in its own frame: square follower axis-aligned, solid sectors centred so that
    after rotating by rotor_angle(0) they cover the hole sectors."""
    r_out = SIEVE_D / 2 - ROTOR_GAP
    plate = cyl(2 * r_out, ROTOR_T)
    a_rest = rotor_angle(0.0)
    half_open = SECTOR / 4 - OPEN_SHRINK
    for k in range(SECTORS):
        c = k * SECTOR + SECTOR / 2 - a_rest  # Open sectors sit between the hole sectors at rest.
        plate = plate.cut(wedge(BOSS_D / 2 + 1.5, r_out + 1, c - half_open, c + half_open, ROTOR_T + 2, -1))
    boss = cyl(BOSS_D, BOSS_H)
    bore = cyl(ROD_D + 2 * 0.4, BOSS_H - FOLLOW_T + 1, -1)
    sq = ROD_SQ + 2 * FOLLOW_PLAY
    follow = cq.Workplane("XY").workplane(offset=BOSS_H - FOLLOW_T - 0.5).rect(sq, sq).extrude(FOLLOW_T + 1)
    p = plate.union(boss).cut(bore).cut(follow)
    if VANE_H > 0:
        for k in range(2):
            c = k * 180 - a_rest  # On the solid sectors.
            p = p.union(wedge(BOSS_D / 2, r_out - 1, c - 2.5, c + 2.5, VANE_H, ROTOR_T))
    p = p.cut(cyl(ROD_D + 2 * 0.4, BOSS_H - FOLLOW_T + 1, -1))
    return p


def rotor(press=0.0):
    return rotor_part().rotate((0, 0, 0), (0, 0, 1), rotor_angle(press)).translate((0, 0, BODY_Z + SIEVE_T))


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


def spring(press=0.0):
    length = SPRING_REST - press
    return wave_spring(length).translate((0, 0, BODY_Z + LID_TOP - SEAT_DEPTH))


def parts(press=0.0):
    ps = {"stand": stand(), "stencil": stencil(), "body": body(), "rotor": rotor(press), "lid": lid(),
          "rod": rod(press), "button": button(press)}
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
        "Sieve plate": {"at": (SIEVE_D / 2 - 6, 0, zb - 0.5), "normal": (0, 0, -1),
                        "params": ["SIEVE_D", "SIEVE_HOLE", "SIEVE_PITCH", "SECTORS"]},
        "Rotor": {"at": (0, 0, zb + SIEVE_T + BOSS_H + 0.5), "normal": (0, 0, 1),
                  "params": ["ROTOR_T", "OPEN_SHRINK", "BOSS_H", "FOLLOW_T", "FOLLOW_PLAY"]},
        "Pivot post": {"at": (PIVOT_D / 2 + 0.5, 0, zb + SIEVE_T + PIVOT_H / 2), "normal": (1, 0, 0),
                       "params": ["PIVOT_H", "PIVOT_PLAY"]},
        "Rod": {"at": (ROD_SQ / 2 + 0.5, 0, zb + HUB_BOT - 8), "normal": (1, 0, 0),
                "params": ["ROD_SQ", "STROKE", "ROD_PLAY"]},
        "Stencil lip": {"at": (STENCIL_D / 2 - 1, 0, STAND_BASE + STENCIL_T + STENCIL_LIP + 0.5), "normal": (0, 0, 1),
                        "params": ["STENCIL_LIP"]},
        "Spring": {"at": (SPRING_OD / 2 + 0.5, 0, zb + LID_TOP + STROKE / 2), "normal": (1, 0, 0),
                   "params": ["PRINT_SPRING", "WS_D", "WS_T", "WS_H", "WS_WAVES", "WS_RINGS"]},
    }


def labels():
    out = {"_views": {"front": "Front (tab side)", "top": "Button side", "bottom": "Cup side"}}
    for name, f in features().items():
        out[name] = {"at": list(f["at"]), "normal": list(f["normal"])}
    return out


# Print orientation per part: True = flip it upside down.
PRINT_FLIP = {"stand": False, "stencil": False, "body": False, "rotor": False, "lid": True, "rod": False,
              "button": True, "spring": False}


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
    print(f"rotor turns {ROT_ANGLE:.0f} degrees per press; twist {TWIST_DEG:.0f} degrees over {TWIST_L:.0f} mm of rod")
    with open("labels.json", "w") as f:
        json.dump(labels(), f, indent=1)

    # Shutter: at rest every hole is under a solid rotor sector; at full press under an open one.
    r_out = SIEVE_D / 2 - ROTOR_GAP
    for state, press, want_open in (("rest", 0.0, False), ("pressed", STROKE, True)):
        rot = rotor(press)
        probe = cq.Workplane("XY").workplane(offset=BODY_Z + SIEVE_T - 0.5) \
            .pushPoints(sector_points(HOLE_R_MIN, SIEVE_D / 2, SIEVE_PITCH, SIEVE_HOLE, SECTORS)) \
            .circle(SIEVE_HOLE / 2).extrude(ROTOR_T + 1)
        covered = rot.intersect(probe).val().Volume() if rot.intersect(probe).vals() else 0.0
        full = probe.val().Volume() * ROTOR_T / (ROTOR_T + 1)
        frac = covered / full
        print(f"shutter {state}: rotor covers {frac * 100:.0f}% of the hole area")
        assert (frac < 0.05) if want_open else (frac > 0.95), f"shutter {state}: wrong"
    # Interference in the use frame, at rest and at full press.
    for state, pp in (("rest", ps), ("pressed", pressed)):
        names = list(pp)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                v = pp[a].intersect(pp[b]).val().Volume() if pp[a].intersect(pp[b]).vals() else 0.0
                assert v < 0.5, f"{state}: {a} and {b} overlap by {v:.2f} mm3"
        gc.collect()

    # Each part on its own, then one plate STL from those meshes, so the sieve
    # (about 700 holes) is tessellated only once: it needs ~2.7 GB as it is.
    layout = {"stand": (2, 2), "body": (112, 2), "stencil": (2, 112), "lid": (92, 112),
              "rotor": (170, 112), "rod": (225, 112), "button": (170, 170), "spring": (212, 170)}
    boxes = []
    if PRINT_SPRING:
        ps["spring"] = wave_spring()  # Printed at its free length.
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
    print(f"spring {SPRING_REST:.1f} mm at rest, {SPRING_PRESSED:.1f} mm pressed (free {SPRING_L:.1f}, solid {SPRING_SOLID:.1f})")
    if PRINT_SPRING:
        # Crest-to-crest wave spring estimate, PETG E about 2000 MPa. Test it: printed parts vary.
        k = 2000 * WS_B * WS_T ** 3 * WS_WAVES ** 4 / (2.4 * WS_D ** 3) / WS_RINGS
        print(f"spring rate about {k:.1f} N/mm: {k * PRELOAD:.0f} N at rest, {k * (PRELOAD + STROKE):.0f} N pressed")
    print(f"wrote cocoa_dispenser.step, cocoa_dispenser_pressed.step, {len(ps)} part STLs, cocoa_dispenser_plate.stl, labels.json")
