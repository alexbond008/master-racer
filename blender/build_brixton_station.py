"""Brixton railway station on its brick viaduct. Run: blender -b --python build_brixton_station.py
Footprint (OSM) is a ~20.5 x 61 m rectangle rotated ~7.5 deg, long axis ~ +Y; the model is built in that local frame
(viaduct runs along local Y; the -Y end is the station frontage / entrance; the arch rows face +-X).
Cues (Wikipedia / Brixton Buzz / photos):
 1 Victorian brick viaduct: raised deck ~7.2 m above street carried on a row of round-headed brick ARCHES (8 per side)
 2 arches filled with roller-shutters / lit shopfronts and warm lit fascia signs (Station Road / Atlantic Road style)
 3 brick parapet with stone coping + string course, murals/graffiti panels on the parapet face
 4 two platforms with long steel-framed platform canopies (valance, columns, lit underside) and a brick waiting room
 5 station name boards 'BRIXTON', two running tracks with third rail + sleepers
 6 plate-girder overbridge crossing above the platform end (South London line), rails across it
 7 station entrance frontage at the -Y end: large central arch with STAIRS climbing into a lit hall, two flanking shop arches,
   projecting glazed entrance CANOPY with lit underside and big lit 'BRIXTON' sign
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbx_common import *

random.seed(11)
reset_scene()
B = Builder()
BRICK = mat('Brick', hexc('#7b5240'), 0.92)
BRICK_L = mat('BrickLight', hexc('#93644c'), 0.92)
BRICK_D = mat('BrickSoot', hexc('#45302a'), 0.95)
STONE = mat('Stone', hexc('#bdb6a6'), 0.8)
CONC = mat('Concrete', hexc('#8a8782'), 0.9)
STEEL = mat('Steel', hexc('#3d4a58'), 0.5, 0.7)
STEEL_G = mat('SteelGreen', hexc('#2c5a4c'), 0.5, 0.5)
SHUT = mat('Shutter', hexc('#5e6368'), 0.55, 0.55)
DARK = mat('Dark', hexc('#141619'), 0.7)
BALLAST = mat('Ballast', hexc('#4a4742'), 0.95)
SLEEP = mat('Sleeper', hexc('#2e2a27'), 0.9)
RAIL = mat('Rail', hexc('#6a6d72'), 0.4, 0.8)
YELLOW = mat('PlatformEdge', hexc('#e5c200'), 0.7)
PLAT = mat('PlatformSurface', hexc('#767470'), 0.85)
WHITE = mat('WhitePaint', hexc('#d9d9d2'), 0.7)
WIN = mat('Emit_Window', hexc('#ffc77a'), 0.4, emit=hexc('#ffb050'), strength=4.5)
SHOP = mat('Emit_Shop', hexc('#ffd9a0'), 0.4, emit=hexc('#ffc27a'), strength=4.0)
LAMP = mat('Emit_Lamp', hexc('#ffe9a8'), 0.4, emit=hexc('#ffd878'), strength=7.0)
SIGN_W = mat('Emit_SignWarm', hexc('#ffb55a'), 0.4, emit=hexc('#ffa23a'), strength=5.0)
SIGN_B = mat('Emit_SignBlue', hexc('#1556d6'), 0.4, emit=hexc('#1350d0'), strength=5.0)
SIGN_T = mat('Emit_SignWhite', hexc('#fff3d8'), 0.4, emit=hexc('#fff0cf'), strength=6.0)
SIGN_R = mat('Emit_SignRed', hexc('#ff2a2a'), 0.4, emit=hexc('#ff2020'), strength=5.0)
SIGN_G = mat('Emit_SignGreen', hexc('#25d070'), 0.4, emit=hexc('#20d060'), strength=4.0)
MURALS = [mat('Mural%d' % i, hexc(c), 0.8) for i, c in enumerate(['#c7503c', '#2f8fa0', '#d9a62e', '#6a4aa8', '#4f9a4a', '#d96a9a'])]

ROT = math.radians(7.5)
B.push(ROT, 0.0, 0.0)

HW = 10.25  # half width
VMIN, VMAX = -30.5, 30.5
DECK = 7.2
PARA = 8.4


def face2(pts, m, smooth=False):
    B.face(pts, m, smooth)
    B.face(list(reversed(pts)), m, smooth)


def arch_pts(cx, r, spring, segs=12):
    pts = []
    for i in range(1, segs):
        a = math.pi - math.pi * i / segs
        pts.append((cx + math.cos(a) * r, spring + math.sin(a) * r))
    return pts


def wall_with_arches(x0, x1, top, notches, y, depth, m, bottom=0.0):
    """Wall polygon in XZ with U-notches (cx, r, spring) cut from the bottom."""
    pts = [(x0, bottom)]
    for (cx, r, sp) in sorted(notches):
        pts += [(cx - r, bottom), (cx - r, sp)] + arch_pts(cx, r, sp) + [(cx + r, sp), (cx + r, bottom)]
    pts += [(x1, bottom), (x1, top), (x0, top)]
    B.vprism(pts, y, depth, m)


# ---------------------------------------------------------------- viaduct body
B.box(0, 0, 0, 2 * HW, VMAX - VMIN, 0.1, BRICK_D)  # base
# deck slab + ballast
B.box(0, 0, DECK - 0.4, 2 * HW, VMAX - VMIN, 0.4, CONC)
B.box(0, 0, DECK, 2 * HW - 2 * 0.5, VMAX - VMIN - 1.0, 0.3, BALLAST)


# solid core + plain side walls (so nothing is hollow)
B.box(0, (-25.0 + VMAX) / 2, 0, 2 * (HW - 3.3), VMAX + 25.0, DECK - 0.4, BRICK_D)
for side in (-1, 1):
    B.box(side * (3.2 + (HW - 3.2) / 2), (VMIN - 25.0) / 2 + 0.0, 0, HW - 3.2, 5.5 + 0.0, DECK - 0.4, BRICK_D)
    B.box(side * (HW - 0.6), (VMIN + V0) / 2, 0, 1.2, V0 - VMIN, DECK, BRICK)
    B.box(side * (HW - 0.6), (V0 + PITCH * NB + VMAX) / 2, 0, 1.2, VMAX - (V0 + PITCH * NB), DECK, BRICK)
B.box(0, -27.8, 5.5, 6.4, 5.4, DECK - 0.4 - 5.5, BRICK_D)

# ---- arches along both long faces
NB = 8
PITCH = 6.4
V0 = -21.6
R = 2.6
SP = 3.2
TUN = 3.2  # tunnel depth before shutter
for side in (1, -1):
    for i in range(NB):
        vc = V0 + PITCH * (i + 0.5)
        B.push(math.pi / 2 * side, side * HW, vc)
        # wall with arch notch (brick), thickness 1.2 so reveals are visible
        wall_with_arches(-PITCH / 2, PITCH / 2, DECK, [(0, R, SP)], 0.0, 1.2, BRICK if (i % 2) else BRICK_L)
        # arch ring (voussoir band) in stone: thin arch slab around notch: draw as arch ring polygon strip
        outer = arch_pts(0, R + 0.45, SP, 14)
        inner = arch_pts(0, R, SP, 14)
        for k in range(len(outer) - 1):
            B.face([(inner[k][0], -0.06, inner[k][1]), (inner[k + 1][0], -0.06, inner[k + 1][1]),
                    (outer[k + 1][0], -0.06, outer[k + 1][1]), (outer[k][0], -0.06, outer[k][1])], STONE) if False else None
        # arch ring as flat quads on front face
        for k in range(len(outer) - 1):
            B.face([(outer[k][0], -0.04, outer[k][1]), (inner[k][0], -0.04, inner[k][1]),
                    (inner[k + 1][0], -0.04, inner[k + 1][1]), (outer[k + 1][0], -0.04, outer[k + 1][1])], STONE)
        # springing blocks (impost)
        B.box(-R - 0.2, -0.05, SP - 0.15, 0.5, 0.2, 0.3, STONE)
        B.box(R + 0.2, -0.05, SP - 0.15, 0.5, 0.2, 0.3, STONE)
        # tunnel lining (barrel) 1.2 -> TUN
        pa = arch_pts(0, R, SP, 12)
        ring = [(-R, SP)] + pa + [(R, SP)]
        for k in range(len(ring) - 1):
            face2([(ring[k][0], 1.2, ring[k][1]), (ring[k + 1][0], 1.2, ring[k + 1][1]),
                   (ring[k + 1][0], TUN, ring[k + 1][1]), (ring[k][0], TUN, ring[k][1])], BRICK_D)
        face2([(-R, 1.2, 0), (-R, 1.2, SP), (-R, TUN, SP), (-R, TUN, 0)], BRICK_D)
        face2([(R, 1.2, 0), (R, 1.2, SP), (R, TUN, SP), (R, TUN, 0)], BRICK_D)
        # back infill: shutter / lit shop / open
        kind = (i * 3 + (0 if side > 0 else 1)) % 5
        poly_back = [(-R, 0.0), (R, 0.0), (R, SP)] + [(p[0], p[1]) for p in reversed(arch_pts(0, R, SP, 12))] + [(-R, SP)]
        poly_back = [(-R, 0.0), (R, 0.0), (R, SP)] + list(reversed(arch_pts(0, R, SP, 12))) + [(-R, SP)]
        if kind in (0, 3):  # roller shutter
            B.vprism(poly_back, TUN, 0.08, SHUT)
            for z in range(0, 15):
                B.box(0, TUN - 0.04, 0.2 + z * 0.22, 2 * R - 0.1, 0.05, 0.05, DARK)
        elif kind in (1, 4):  # lit shop front
            B.vprism(poly_back, TUN, 0.08, SHOP)
            B.box(0, TUN - 0.05, 0.1, 2 * R, 0.08, 0.9, DARK)  # stall board
            B.box(-1.6, TUN - 0.06, 0.1, 0.1, 0.05, 3.0, DARK)
            B.box(1.6, TUN - 0.06, 0.1, 0.1, 0.05, 3.0, DARK)
            B.box(0.3, TUN - 0.06, 0.1, 0.1, 0.05, 3.2, DARK)
        else:  # open dark with lamp
            B.vprism(poly_back, TUN, 0.08, DARK)
            B.box(0, TUN - 0.1, 2.9, 0.5, 0.1, 0.2, LAMP)
        # lit fascia sign inside the arch above the shutter / at the arch face
        if kind != 2:
            colm = [SIGN_W, SIGN_R, SIGN_B, SIGN_G, SIGN_W][(i + side) % 5]
            B.box(0, 0.5, SP + R * 0.55, 3.6, 0.3, 0.7, colm)
            B.box(0, 0.33, SP + R * 0.55 + 0.1, 3.0, 0.04, 0.4, SIGN_T)
        B.pop()
    # string course + parapet on this face
    B.push(math.pi / 2 * side, side * HW, 0)
    B.box(0, -0.12, DECK - 0.5, 2 * 0.0 + (VMAX - VMIN), 0.3, 0.35, STONE)
    B.pop()

# brick parapet walls both sides (above deck) + stone coping
for side in (1, -1):
    B.box(side * (HW - 0.3), 0, DECK, 0.6, VMAX - VMIN, PARA - DECK, BRICK)
    B.box(side * (HW - 0.2), 0, PARA, 0.9, VMAX - VMIN + 0.2, 0.18, STONE)
    # murals on parapet face (flat coloured panels)
    for k in range(4):
        vc = random.uniform(-22, 25)
        B.box(side * (HW + 0.02), vc, DECK + 0.1, 0.04, random.uniform(3, 6), 0.9, random.choice(MURALS))

# end faces: back end (+V) solid brick wall w/ parapet; front (-V) station frontage below
B.box(0, VMAX - 0.3, 0, 2 * HW, 0.6, PARA, BRICK)

# ---------------------------------------------------------------- tracks + platforms
TRACKS = [-1.9, 1.9]
V_T0, V_T1 = -28.0, 30.0
for c in TRACKS:
    for dx in (-0.72, 0.72):
        B.box(c + dx, (V_T0 + V_T1) / 2, DECK + 0.3 + 0.14, 0.08, V_T1 - V_T0, 0.18, RAIL)
    B.box(c + 1.0, (V_T0 + V_T1) / 2, DECK + 0.3 + 0.1, 0.07, V_T1 - V_T0, 0.1, RAIL)  # third rail
    v = V_T0
    while v < V_T1:
        B.box(c, v, DECK + 0.3, 2.5, 0.22, 0.14, SLEEP)
        v += 0.75
# platforms A (-u) and B (+u): 44 m
PV0, PV1 = -21.0, 21.0
for side in (-1, 1):
    ux = side * 7.45
    B.box(ux, (PV0 + PV1) / 2, DECK, 4.9, PV1 - PV0, 1.0, CONC)
    B.box(side * 5.15, (PV0 + PV1) / 2, DECK + 1.0 - 0.02, 0.5, PV1 - PV0, 0.04, YELLOW)
    B.box(ux, (PV0 + PV1) / 2, DECK + 1.0, 4.9, PV1 - PV0, 0.03, PLAT)
Z0 = DECK + 1.0
# canopy columns and roofs
CAN_V0, CAN_V1 = -20.0, 20.0
for side in (-1, 1):
    # roof cross-section (u, z) extruded along v : high at back, low at track side
    u_out, u_in = side * 9.8, side * 4.6
    pts = [(u_out, Z0 + 5.0), (u_in, Z0 + 3.9), (u_in, Z0 + 3.7), (u_out, Z0 + 4.8)]
    B.vprism(pts, CAN_V0, CAN_V1 - CAN_V0, STEEL_G)
    # valance (white fascia board) along the track-side edge
    B.box(u_in, (CAN_V0 + CAN_V1) / 2, Z0 + 3.55, 0.12, CAN_V1 - CAN_V0, 0.55, WHITE)
    # columns every 5 m + beams
    nv = int((CAN_V1 - CAN_V0) / 5) + 1
    for k in range(nv):
        v = CAN_V0 + 5 * k + 0.0
        B.box(side * 6.2, v, Z0, 0.28, 0.28, 3.8, STEEL)
        B.box(side * 7.2, v, Z0 + 3.9, 5.2 if False else 0.18, 0.22, 0.4, STEEL)
        # lit underside strip lamps
        B.box(side * 6.0, v + 2.5, Z0 + 3.6, 0.2, 1.4, 0.06, LAMP)
        # name board on column (faces the track) every 15 m
        if k % 3 == 1:
            B.push(-side * math.pi / 2 + math.pi, side * 5.95, v)
            B.pop()
            B.box(side * 5.95, v, Z0 + 2.3, 0.1, 2.1, 0.75, SIGN_B)
            B.push(math.pi / 2 * (-side), side * 5.88, v)
            B.text('BRIXTON', 0, 0, Z0 + 2.62, 0.45, SIGN_T, extrude=0.04)
            B.pop()
        # bench + back rail
        if k % 2 == 0:
            B.box(side * 8.6, v + 1.0, Z0, 0.5, 1.8, 0.45, DARK)
            B.box(side * 8.85, v + 1.0, Z0 + 0.45, 0.08, 1.8, 0.5, DARK)
    # brick waiting room on platform
    wr_v = -4.0 if side < 0 else 6.0
    B.box(side * 8.7, wr_v, Z0, 2.4, 7.0, 2.9, BRICK_L)
    B.box(side * 8.7, wr_v, Z0 + 2.9, 2.7, 7.4, 0.25, CONC)
    for k in range(3):
        B.box(side * 7.46, wr_v - 2.4 + k * 2.4, Z0 + 0.7, 0.06, 1.5, 1.5, WIN)
    B.box(side * 7.46, wr_v, Z0 + 2.2, 0.06, 6.0, 0.25, SIGN_B)
    # lamp posts on platform edge
    for v in (-16, -8, 0, 8, 16):
        B.box(side * 5.5, v, Z0, 0.1, 0.1, 3.0, STEEL)
        B.sphere(side * 5.5, v, Z0 + 3.1, 0.18, LAMP, 8, 5)

# ---------------------------------------------------------------- overbridge (South London line) across the platform end
OV0, OV1 = 23.5, 30.2
B.box(0, (OV0 + OV1) / 2, DECK + 4.4, 2 * HW - 0.2, OV1 - OV0, 0.7, STEEL)  # bridge deck
B.box(0, (OV0 + OV1) / 2, DECK + 5.1, 2 * HW - 1.2, OV1 - OV0 - 0.4, 0.25, BALLAST)
# plate girders (outer faces along u) -- side faces perpendicular to v at OV0/OV1
for vv in (OV0 + 0.1, OV1 - 0.1):
    B.box(0, vv, DECK + 3.6, 2 * HW, 0.25, 2.4, STEEL)
    for k in range(9):  # stiffeners
        B.box(-HW + 1.0 + k * 2.3, vv + (-0.2 if vv < 26 else 0.2), DECK + 3.7, 0.12, 0.12, 2.2, DARK)
# brick abutments both sides
for side in (-1, 1):
    B.box(side * (HW - 0.9), (OV0 + OV1) / 2, DECK, 1.8, OV1 - OV0 + 0.6, 4.4, BRICK)
    B.box(side * (HW - 0.9), (OV0 + OV1) / 2, DECK + 4.2, 2.1, OV1 - OV0 + 0.9, 0.25, STONE)
# rails on the bridge, running across u
for dv in (-0.72, 0.72):
    B.box(0, (OV0 + OV1) / 2 + dv, DECK + 5.35 + 0.1, 2 * HW - 2.0, 0.08, 0.17, RAIL)
uu = -HW + 1.0
while uu < HW - 1.0:
    B.box(uu, (OV0 + OV1) / 2, DECK + 5.35, 0.22, 2.5, 0.14, SLEEP)
    uu += 0.7
B.box(0, (OV0 + OV1) / 2, DECK + 5.6, 2 * HW - 1.2, 0.1, 0.06, SIGN_W) if False else None
# lit underside strip of the bridge
B.box(0, (OV0 + OV1) / 2, DECK + 4.35, 2 * HW - 2.0, 0.4, 0.05, LAMP)

# ---------------------------------------------------------------- station frontage at -V end (street level)
FV = VMIN
B.push(0, 0, FV)
FRONT_H = PARA
wall_with_arches(-HW, HW, FRONT_H, [(0, 3.0, 3.2), (-7.0, 1.7, 2.4), (7.0, 1.7, 2.4)], 0.0, 1.0, BRICK_L)
# arch rings (stone) on the 3 arches
for (cx, r, sp) in ((0, 3.0, 3.2), (-7.0, 1.7, 2.4), (7.0, 1.7, 2.4)):
    outer = arch_pts(cx, r + 0.4, sp, 14)
    inner = arch_pts(cx, r, sp, 14)
    for k in range(len(outer) - 1):
        B.face([(outer[k][0], -0.04, outer[k][1]), (inner[k][0], -0.04, inner[k][1]),
                (inner[k + 1][0], -0.04, inner[k + 1][1]), (outer[k + 1][0], -0.04, outer[k + 1][1])], STONE)
    B.box(cx - r - 0.2, -0.05, sp - 0.15, 0.55, 0.2, 0.3, STONE)
    B.box(cx + r + 0.2, -0.05, sp - 0.15, 0.55, 0.2, 0.3, STONE)
# string course + coping + cornice
B.box(0, -0.15, FRONT_H - 1.3, 2 * HW + 0.4, 0.4, 0.4, STONE)
B.box(0, -0.12, FRONT_H, 2 * HW + 0.5, 0.7, 0.2, STONE)
# main arch: stair hall (stairs rise into a lit hall)
nst = 14
tread, rise = 0.3, 0.17
for i in range(nst):
    B.box(0, 1.0 + tread * (i + 0.5), 0.0, 5.6, tread, rise * (i + 1), STONE)
hall_y = 1.0 + tread * nst
B.box(0, hall_y + 0.3, 0.0, 2 * 3.0, 0.2, 5.5, SHOP)  # lit glow at the stair head
B.box(-3.0, 1.0 + (hall_y - 1.0) / 2, 0.0, 0.2, hall_y - 1.0, 5.0, BRICK_D)
B.box(3.0, 1.0 + (hall_y - 1.0) / 2, 0.0, 0.2, hall_y - 1.0, 5.0, BRICK_D)
# hall ceiling lights
for k in range(3):
    B.box(0, 1.5 + k * 1.4, 4.0 + 0.6 * 0, 1.6, 0.4, 0.06, LAMP)
# handrails
for sx in (-2.4, 2.4):
    B.obox((sx, 1.0 + tread * nst / 2, 0.9 + rise * nst / 2), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.06, tread * nst, 0.06, STEEL) if False else None
    B.box(sx, 1.0 + tread * nst / 2, 0.9, 0.05, tread * nst, 0.05, STEEL)
    B.box(sx, 1.0, 0.0, 0.05, 0.05, 1.0, STEEL)
# flanking shop arches (lit kiosk / cafe / ticket office)
for cx, kind in ((-7.0, 0), (7.0, 1)):
    poly = [(cx - 1.7, 0.0), (cx + 1.7, 0.0), (cx + 1.7, 2.4)] + [(p[0], p[1]) for p in reversed(arch_pts(cx, 1.7, 2.4, 12))] + [(cx - 1.7, 2.4)]
    B.vprism(poly, 1.9, 0.08, SHOP if kind == 0 else SIGN_W)
    B.box(cx, 1.8, 0.0, 3.4, 0.2, 1.0, DARK)
    # tunnel sides
    B.box(cx - 1.7, 1.45, 0.0, 0.12, 0.9, 2.4, BRICK_D)
    B.box(cx + 1.7, 1.45, 0.0, 0.12, 0.9, 2.4, BRICK_D)
# big lit station sign above main arch + text
B.box(0, -0.3, 6.35, 9.0, 0.45, 1.5, SIGN_B)
B.box(0, -0.55, 6.5, 8.6, 0.08, 1.2, SIGN_B)
B.text('BRIXTON', 0, -0.62, 7.1, 1.0, SIGN_T, extrude=0.1)
B.text('STATION', -3.0, -0.62, 6.6, 0.28, SIGN_T, extrude=0.05) if False else None
# red 'tube/rail' roundel style disc on left of sign: ring + bar
ring = [(math.cos(2 * math.pi * i / 24) * 0.75 - 5.9, -0.58, 7.1 + math.sin(2 * math.pi * i / 24) * 0.75) for i in range(24)]
B.face(ring, SIGN_R)
inner = [(math.cos(2 * math.pi * i / 24) * 0.5 - 5.9, -0.62, 7.1 + math.sin(2 * math.pi * i / 24) * 0.5) for i in range(24)]
B.face(inner, SIGN_T)
B.box(-5.9, -0.66, 6.95, 1.7, 0.05, 0.3, SIGN_B)
# projecting glazed entrance canopy over the stairs (steel + glass) with lit underside
CW = 8.4
B.box(0, -1.6, 4.65, CW, 3.0, 0.15, STEEL)
B.box(0, -1.6, 4.58, CW - 0.4, 2.6, 0.04, LAMP)
B.box(0, -3.1, 4.5, CW, 0.12, 0.55, STEEL_G)
for sx in (-CW / 2 + 0.2, CW / 2 - 0.2):
    B.box(sx, -3.0, 0.0, 0.2, 0.2, 4.55, STEEL)
B.pop()

# ---------------------------------------------------------------- finish
B.pop()

cams = [
    ('front34', (-45, -58, 24), (0, -3, 4), 36),
    ('rear34', (45, 60, 28), (0, 2, 5), 38),
    ('side', (70, -2, 14), (0, 2, 5), 36),
    ('top', (0, -2, 90), (0, 0, 0), 40),
    ('frontclose', (0, -45, 8), (0, -30, 5), 40),
    ('deck', (-9, -34, 16), (0, 8, 8), 42),
]
finish(B, 'brixton_station', footprint=(28.0, 63.5),
       notes="Brixton station on brick viaduct: built in the OSM footprint's local frame (20.5 x 61 m, rotated 7.5 deg; viaduct runs along local Y, NOT along X - matches footprint). 8 round-headed arches per long side with roller shutters / lit shopfronts and warm signs, parapet+murals, 2 tracks with third rail, 2 platforms with lit canopies + waiting rooms, plate-girder overbridge at +Y end, station frontage at -Y end with stairs, canopy and lit BRIXTON sign. Deck 7.2 m. Origin = footprint centre.",
       cams=cams, bevel=0.025,
       skip_bevel=('Emit_Window', 'Emit_Shop', 'Emit_Lamp', 'Emit_SignWarm', 'Emit_SignBlue', 'Emit_SignWhite',
                   'Emit_SignRed', 'Emit_SignGreen', 'Rail', 'Sleeper'),
       res=(1100, 750))
