"""Brixton Windmill (Ashby's Mill, 1816). Run: blender -b --python build_windmill.py
Cues: 4-storey brick tower mill, 14.94 m overall, 12.04 m to curb, base dia 6.71 m tapering to ~3.7 m;
boat-shaped white cap (hand-wheel, NO fantail); 4 sails (2 patent shuttered, 2 common lattice) facing the front (-Y);
dark tarred plinth + door, small windows tier by tier, white lintels, dark curb ring.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *

reset_scene()
B = Builder()
BRICK = mat('Brick', hexc('#8c4f3a'), 0.85)
BRICK_D = mat('BrickDark', hexc('#3a2a24'), 0.9)
STONE = mat('Stone', hexc('#cfc9bb'), 0.8)
CAP = mat('CapWhite', hexc('#e9e7e0'), 0.7)
TIMBER = mat('Timber', hexc('#d8d4c8'), 0.75)
IRON = mat('Iron', hexc('#222426'), 0.5, 0.6)
WIN = mat('Emit_Window', hexc('#ffb55a'), 0.4, emit=hexc('#ffa23a'), strength=4.0)
DOOR = mat('Door', hexc('#1c1f24'), 0.7)

CX, CY = -0.1, 0.13
R0, R1, H = 3.355, 1.85, 12.04


def rad(z):
    return R0 + (R1 - R0) * z / H


# tower: segmented in stages with a slight step (string courses)
STG = [0, 0.6, 3.4, 6.4, 9.3, 12.04]
B.push(0, CX, CY)
B.frustum(0, 0, 0, 0.7, R0 + 0.12, R0 + 0.06, BRICK_D, segs=28, cap_top=False)  # plinth
for a, b in zip(STG[1:-1], STG[2:]):
    B.frustum(0, 0, a, b, rad(a), rad(b), BRICK, segs=28, cap_top=False)
# bands (darker thin course / lighter stone string courses)
for z in (3.4, 6.4, 9.3):
    B.frustum(0, 0, z - 0.1, z + 0.1, rad(z) + 0.06, rad(z) + 0.06, STONE, segs=28, cap_top=False)
# curb ring on top
B.frustum(0, 0, H - 0.02, H + 0.25, rad(H) + 0.18, rad(H) + 0.18, IRON, segs=28, cap_top=False)
B.frustum(0, 0, H + 0.25, H + 0.25, rad(H) + 0.18, rad(H) - 0.1, IRON, segs=28, cap_top=True)

# windows (front is -Y; spread around, mostly front-ish and sides)
def window(z, ang, w=0.5, h=0.9, lit=True):
    r = rad(z) - 0.02
    x, y = math.cos(ang) * r, math.sin(ang) * r
    rot = ang + math.pi / 2
    B.box(x * 1.0, y * 1.0, z - h / 2, w + 0.36, 0.3, 0.14, STONE, rot=rot)  # sill
    B.box(x, y, z + h / 2, w + 0.3, 0.3, 0.13, STONE, rot=rot)  # lintel
    B.box(x * 1.015, y * 1.015, z - h / 2 + 0.1, w, 0.16, h, WIN if lit else DOOR, rot=rot)


ang_front = -math.pi / 2
for z, angs, w, h in [(2.2, [-0.9, 0.35], 0.5, 0.8), (4.9, [ang_front, 0.1, 3.0, -2.3], 0.5, 0.9),
                      (7.8, [ang_front + 0.45, -2.7, 0.4, 2.3], 0.45, 0.85), (10.6, [ang_front, 0.2, 2.9], 0.38, 0.75)]:
    for a in angs:
        window(z, a, w, h, True)
# door on front-left with arch head
a = ang_front - 0.35
r = rad(0.0)
dx, dy = math.cos(a) * (r + 0.1), math.sin(a) * (r + 0.1)
B.box(dx, dy, 0.0, 1.35, 0.5, 2.3, DOOR, rot=a + math.pi / 2)
B.box(dx, dy, 2.3, 1.7, 0.55, 0.18, STONE, rot=a + math.pi / 2)
B.pop()

# ---- cap (boat shaped) : hull loft along Y, centred over tower
zc = H + 0.25
rings = []
L0, L1 = -2.9, 2.6  # front (sails side) to rear
secs = 15
for i in range(secs + 1):
    t = i / secs
    y = L0 + (L1 - L0) * t
    # half width: fuller at front (windshaft bearing), tapering to rear, narrowed at the bow tip
    w = 2.05 * math.sin(math.pi * (0.06 + 0.9 * t)) ** 0.6 if t < 0.5 else 2.05 * math.cos(math.pi * (t - 0.5) * 0.85) ** 0.7
    w = max(w, 0.15)
    hh = 1.5 * (1 - (2 * t - 0.8) ** 2 * 0.35)  # wall height
    hr = 1.5 * (1 - (2 * t - 0.8) ** 2 * 0.3)  # roof rise
    hr = max(hr, 0.2)
    ring = []
    # section closed loop: bottom left -> up left wall -> roof arc -> right wall -> bottom
    ring.append((-w, y, 0.0))
    ring.append((-w * 1.0, y, hh * 0.55))
    for k in range(1, 6):
        a = math.pi * (k / 6)
        ring.append((-w * math.cos(a), y, hh + hr * math.sin(a) * 0.0 + hr * math.sin(a)))
    ring.append((w * 1.0, y, hh * 0.55))
    ring.append((w, y, 0.0))
    ring = [(CX + p[0], CY + p[1], zc + p[2]) for p in ring]
    rings.append(ring)
# flip winding by reversing each ring order
rings = [list(reversed(r)) for r in rings]
B.loft(rings, CAP, smooth=True, closed=False)
# close the bottom
B.face([(CX - 2.0, CY + L0 + 0.3, zc), (CX + 2.0, CY + L0 + 0.3, zc), (CX + 2.0, CY + L1 - 0.3, zc),
        (CX - 2.0, CY + L1 - 0.3, zc)], CAP)
# end caps (open ends of the loft)
for ring in (rings[0], rings[-1]):
    B.face(list(ring), CAP)
# dark kerb band at the cap base
B.box(CX, CY, zc - 0.05, 3.9, 5.2, 0.2, IRON)
# ridge beam + hand wheel on rear
B.box(CX, CY + 0.2, zc + 3.0, 0.12, 4.3, 0.12, IRON)
B.box(CX, CY + L1 + 0.1, zc + 0.9, 0.2, 0.2, 0.9, IRON)
# small cap window/door at rear (lit)
B.box(CX, CY + L1 - 0.28, zc + 0.9, 0.7, 0.14, 0.9, WIN)

# ---- sails: windshaft axis along -Y, hub front of cap
hub = (CX, CY + L0 - 0.55, zc + 1.15)
B.box(hub[0], hub[1] + 0.9, hub[2] - 0.12, 0.5, 2.0, 0.5, IRON)  # shaft/poll-end
B.sphere(hub[0], hub[1] - 0.15, hub[2], 0.42, IRON, 10, 6)  # canister
SAIL_R = 7.2
THETA0 = math.radians(28)
ey = (0, 1, 0)
for k in range(4):
    th = THETA0 + k * math.pi / 2
    ux = (math.cos(th), 0, math.sin(th))  # along sail
    vz = (-math.sin(th), 0, math.cos(th))  # across sail (leading side +v)
    # stock
    c = (hub[0] + ux[0] * (SAIL_R / 2 + 0.2), hub[1] - 0.18, hub[2] + ux[2] * (SAIL_R / 2 + 0.2))
    B.obox(c, ux, ey, vz, SAIL_R - 0.4, 0.14, 0.2, TIMBER)
    patent = k % 2 == 0
    u0, u1 = 1.6, SAIL_R - 0.25
    wv = 1.9  # sail width
    voff = -0.15  # frame mostly on trailing side (-v)
    # two long whips at frame edges
    for vv in (voff, voff - wv):
        c2 = (hub[0] + ux[0] * (u0 + u1) / 2 + vz[0] * vv, hub[1] - 0.14, hub[2] + ux[2] * (u0 + u1) / 2 + vz[2] * vv)
        B.obox(c2, ux, ey, vz, u1 - u0, 0.08, 0.1, TIMBER)
    n = 11 if patent else 14
    for j in range(n + 1):
        u = u0 + (u1 - u0) * j / n
        c3 = (hub[0] + ux[0] * u + vz[0] * (voff - wv / 2), hub[1] - 0.14, hub[2] + ux[2] * u + vz[2] * (voff - wv / 2))
        if patent:
            # shutter slat, slightly angled look = thicker slab
            B.obox(c3, ux, ey, vz, 0.42, 0.05, wv - 0.1, TIMBER)
        else:
            B.obox(c3, ux, ey, vz, 0.07, 0.07, wv, TIMBER)
    if not patent:
        # lattice horizontal bars (2 along the length) + cloth-ish dark bar
        for vv in (voff - wv * 0.33, voff - wv * 0.66):
            c2 = (hub[0] + ux[0] * (u0 + u1) / 2 + vz[0] * vv, hub[1] - 0.14, hub[2] + ux[2] * (u0 + u1) / 2 + vz[2] * vv)
            B.obox(c2, ux, ey, vz, u1 - u0, 0.05, 0.05, TIMBER)
    else:
        # heavy leading-edge board
        c4 = (hub[0] + ux[0] * (u0 + u1) / 2 + vz[0] * 0.18, hub[1] - 0.14, hub[2] + ux[2] * (u0 + u1) / 2 + vz[2] * 0.18)
        B.obox(c4, ux, ey, vz, u1 - u0, 0.06, 0.16, TIMBER)

# low brick boundary plinth/ground disc to anchor
B.push(0, CX, CY)
B.frustum(0, 0, 0, 0.06, R0 + 0.9, R0 + 0.9, STONE, segs=28, cap_top=True)
B.pop()

cams = [
    ('front34', (-22, -30, 12), (0, 0, 10), 35),
    ('rear34', (22, 30, 12), (0, 0, 10), 35),
    ('side', (-42, 0, 10), (0, 0, 10), 35),
    ('top', (0, -14, 50), (0, 0.5, 9), 35),
    ('front', (0, -45, 10), (0, 0, 10), 35),
]
finish(B, 'windmill', footprint=(6.4, 6.4),
       notes="Brixton Windmill (Ashby's Mill 1816): tapering brick tower mill 6.7->3.7 m, 12.04 m to curb, 14.94 m overall; white boat cap, 4 sails (2 patent shuttered, 2 common lattice) facing -Y, lit windows. Origin = footprint centre; tower at (-0.1, 0.13).",
       cams=cams, bevel=0.02, skip_bevel=('Emit_Window',))
