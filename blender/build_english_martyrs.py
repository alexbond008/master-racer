"""english_martyrs - Church of the English Martyrs (RC), Mitcham Lane / Streatham High Rd, Streatham. A E Purdie 1892-94, Grade II*.

Cues (Historic England listing text + Commons photos; the brief's 'red brick' is WRONG - it is stone):
 1. Built of COURSED KENTISH RAGSTONE RUBBLE (cool grey with ochre/brown flecks) with pale BATH STONE dressings (Portland for the spire); SLATE roofs.
 2. French Gothic. Plan: five-bay nave + aisles, three-bay chancel, N and S chapels, SOUTH-WEST TOWER standing slightly proud of the west front.
 3. Tall SLENDER TOWER, 3 stages: traceried west window + arched doorway with colonnettes (stage 1), two lancets + statue niches (stage 2),
    belfry with THREE POINTED ARCHES PER FACE filled with wooden louvres (stage 3).
 4. Tall BROACHED OCTAGONAL SPIRE (~46 m overall, dark ragstone) with narrow LUCARNES and a metal finial.
 5. WEST FRONT: steep gable with a large TRACERIED window (wheel/roundels), elaborate entrance with colonnettes and a steep pediment; staged buttresses.
 6. Aisles have triple trefoil-headed lancets under small roundels; nave has a roundel clerestory; steep (about 55 deg) nave roof, lower chancel ridge.
 7. 1962 north-side extension (Sibthorp) to the east end - broad gabled hall on the N (left) side of the chancel, making the footprint a wide 'T'.
 8. Footprint 37 x 38 m, rotated +11.3 deg; tower + gable front face the street (-Y).
"""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sl_lib import *
from mathutils import Vector

THETA = 11.3
rng = random.Random(5)
b = Builder(THETA)

define('Ragstone', '#80796a', rough=0.97)
define('Ragstone_Dk', '#6a6558', rough=0.97)
define('Bath_Stone', '#d3c7a7', rough=0.85)
define('Slate_Roof', '#3a3e46', rough=0.6, metal=0.1)
define('Spire_Stone', '#5f5d52', rough=0.9)
define('Church_Glow', '#ffc67c', rough=0.4, emit=2.4)
define('Church_Glow_Cool', '#ffe1b0', rough=0.4, emit=2.0)
define('Wood_Louvre', '#4b3a2c', rough=0.8)
define('Door_Wood', '#3b2a1e', rough=0.7)
define('Grave', '#6f6e69', rough=0.95)

# ---------------------------------------------------------------- dimensions (local frame)
YF = -15.6                 # west front plane (nave gable)
NXa, NXb = -0.2, 7.6       # nave
AXn = -4.1                 # north aisle outer wall
AXs = 11.3                 # south aisle outer wall
YN_END = 3.7               # nave / aisle end (chancel begins)
YE = 19.6                  # east end
H_AISLE, H_AISLE_TOP = 5.6, 9.0
H_NAVE, H_NAVE_RIDGE = 11.2, 16.8
H_CHAN, H_CHAN_RIDGE = 9.6, 14.2

def arch_y(mat, x, cy, z0, w, h, out, depth, pointed=True):
    b.arch_y(mat, x, cy, z0, w, h, out=out, depth=depth, pointed=pointed)

def circle_y(mat, x, cy, cz, r, out, depth, n=12):
    pts = [(cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    if out > 0:
        b.profile_y(mat, pts, x, x + depth)
    else:
        b.profile_y(mat, pts, x - depth, x)

def circle_x(mat, cx, y, cz, r, out, depth, n=12):
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    if out < 0:
        b.profile_x(mat, pts, y - depth, y)
    else:
        b.profile_x(mat, pts, y, y + depth)

# ================================================================== NAVE + CHANCEL
b.bbox('Ragstone', NXa, NXb, YF, YN_END, 0, H_NAVE)
b.gable('Slate_Roof', NXa, NXb, YF, YN_END, H_NAVE, H_NAVE_RIDGE - H_NAVE, ridge='y', oh=0.0)
b.bbox('Ragstone', NXa, NXb, YN_END, YE, 0, H_CHAN)
b.gable('Slate_Roof', NXa, NXb, YN_END, YE, H_CHAN, H_CHAN_RIDGE - H_CHAN, ridge='y', oh=0.0)
# ridge cresting
b.bbox('Bath_Stone', (NXa + NXb) / 2 - 0.1, (NXa + NXb) / 2 + 0.1, YF, YN_END, H_NAVE_RIDGE - 0.05, H_NAVE_RIDGE + 0.2)
b.bbox('Bath_Stone', (NXa + NXb) / 2 - 0.1, (NXa + NXb) / 2 + 0.1, YN_END, YE, H_CHAN_RIDGE - 0.05, H_CHAN_RIDGE + 0.2)
xm = (NXa + NXb) / 2

# stone front gable (west) in ragstone proud of slate
b.profile_x('Ragstone', [(NXa - 0.02, H_NAVE - 0.05), (NXb + 0.02, H_NAVE - 0.05), (xm, H_NAVE_RIDGE + 0.05)], YF - 0.08, YF)
# east gable (chancel end)
b.profile_x('Ragstone', [(NXa - 0.02, H_CHAN - 0.05), (NXb + 0.02, H_CHAN - 0.05), (xm, H_CHAN_RIDGE + 0.05)], YE, YE + 0.08)
# nave/chancel gable above the lower chancel roof (east face of nave gable) is visible - rubble
b.profile_x('Ragstone', [(NXa, H_CHAN), (NXb, H_CHAN), (xm, H_NAVE_RIDGE)], YN_END - 0.02, YN_END + 0.06)

# ---- aisles (lean-to), N and S; walls + wedge roof
b.bbox('Ragstone', AXn, NXa, YF, YE, 0, H_AISLE)          # north aisle + north chapel (continues to east end, lower)
b.lean('Slate_Roof', AXn, NXa, YF, YN_END, H_AISLE, H_AISLE_TOP, slope='x+')
b.lean('Slate_Roof', AXn, NXa, YN_END, YE, H_AISLE - 0.4, H_AISLE_TOP - 1.0, slope='x+')
b.bbox('Ragstone', NXb, AXs, -11.8, 14.8, 0, H_AISLE)     # south aisle + south chapel
b.lean('Slate_Roof', NXb, AXs, -11.8, YN_END, H_AISLE, H_AISLE_TOP, slope='x-')
b.lean('Slate_Roof', NXb, AXs, YN_END, 14.8, H_AISLE - 0.4, H_AISLE_TOP - 1.0, slope='x-')
# stone fronts for the aisle lean-to triangles at the west front (N aisle)
b.profile_x('Ragstone', [(AXn, H_AISLE - 0.05), (NXa, H_AISLE - 0.05), (NXa, H_AISLE_TOP), ], YF - 0.08, YF)

# south chapel east stub (sacristy bump in footprint)
b.bbox('Ragstone', AXs, 17.4, 14.8, 18.8, 0, 5.0)
b.gable('Slate_Roof', AXs, 17.4, 14.8, 18.8, 5.0, 2.6, ridge='x', oh=0.15)
b.bbox('Ragstone', 7.6, AXs, 14.8, 18.8, 0, H_AISLE - 0.6)
b.bbox('Ragstone', NXb, AXs, 14.8, YE, 0, H_AISLE - 0.6)

# ---- 1962 north extension hall (broad, gabled, ridge along y) x -18.3..AXn
EX0, EX1, EY0, EY1 = -18.3, AXn, 1.0, 19.5
b.bbox('Ragstone', EX0, EX1, EY0, EY1, 0, 5.9)
b.gable('Slate_Roof', EX0, EX1, EY0, EY1, 5.9, 5.0, ridge='y', oh=0.2)
b.profile_x('Ragstone', [(EX0, 5.85), (EX1, 5.85), ((EX0 + EX1) / 2, 10.9 + 0.2)], EY1 + 0.2, EY1 + 0.28)
b.profile_x('Ragstone', [(EX0, 5.85), (EX1, 5.85), ((EX0 + EX1) / 2, 10.9 + 0.2)], EY0 - 0.28, EY0 - 0.2)
b.bbox('Ragstone', AXn, NXa, YN_END, YE, 0, H_AISLE)
for k in range(5):
    y = EY0 + 2.2 + k * 3.7
    for (yy) in (y,):
        arch_y('Bath_Stone', EX0, yy, 1.6, 2.0, 3.6, -1, 0.1)
        arch_y('Church_Glow', EX0 - 0.06, yy, 1.8, 1.5, 3.2, -1, 0.08)
# end window of extension (east wall y=EY1)
EXc = (EX0 + EX1) / 2
b.arch('Bath_Stone', EXc, EY1, 1.8, 3.4, 6.2, depth=0.12, pointed=True, face='+Y')
b.arch('Church_Glow', EXc, EY1 + 0.1, 2.0, 2.8, 5.7, depth=0.08, pointed=True, face='+Y')
b.bbox('Bath_Stone', EXc - 0.07, EXc + 0.07, EY1, EY1 + 0.2, 2.0, 7.2)

# ================================================================== TOWER (south-west)
TXa, TXb = 6.3, 11.4
TYa, TYb = -17.1, -11.8
TXc, TYc = (TXa + TXb) / 2, (TYa + TYb) / 2
H1, H2, H3 = 9.0, 16.5, 23.0
b.bbox('Ragstone', TXa, TXb, TYa, TYb, 0, H3)
# buttresses: SE (x+) buttress per footprint + corner buttresses
for (cx, cy) in ((TXa, TYa), (TXb, TYa)):
    b.bbox('Ragstone', cx - 0.7 if cx == TXa else cx - 0.0, cx + 0.0 if cx == TXa else cx + 1.2, TYa - 0.0, TYa + 0.0 if False else TYa + 1.2, 0, H1)
b.bbox('Ragstone', TXb, 12.6, -15.8, -10.8, 0, H1 - 1.5)
b.bbox('Bath_Stone', TXb - 0.1, 12.7, -15.9, -10.7, H1 - 1.6, H1 - 1.4)
# string courses
for z in (H1, H2, H3):
    b.bbox('Bath_Stone', TXa - 0.15, TXb + 0.15, TYa - 0.15, TYb + 0.15, z - 0.12, z + 0.12)
# corner offset pilasters to suggest stepped buttressing
for (cx, cy) in ((TXa, TYa), (TXb, TYa)):
    sx = -0.5 if cx == TXa else 0.5
    b.bbox('Bath_Stone', min(cx, cx + sx), max(cx, cx + sx), TYa - 0.5, TYa, 0.3, H2)
    b.bbox('Bath_Stone', min(cx, cx + sx * 0.7), max(cx, cx + sx * 0.7), TYa - 0.3, TYa, H2, H3 - 0.2)
# stage 1 front (west face y=TYa): doorway + traceried window
b.arch('Bath_Stone', TXc, TYa, 0.0, 2.6, 4.4, depth=0.3, pointed=True, face='-Y')
b.arch('Door_Wood', TXc, TYa - 0.2, 0.0, 1.7, 3.6, depth=0.2, pointed=True, face='-Y')
# steep pediment/gablet over the door + colonnettes
b.profile_x('Bath_Stone', [(TXc - 1.6, 4.3), (TXc + 1.6, 4.3), (TXc, 6.3)], TYa - 0.35, TYa)
for sx in (-1, 1):
    for k in range(3):
        b.cyl('Bath_Stone', TXc + sx * (1.0 + k * 0.28), TYa - 0.2, 0.0, 0.1, 3.0, n=6)
b.arch('Bath_Stone', TXc, TYa, 6.6, 1.9, 4.1, depth=0.12, pointed=True, face='-Y')
b.arch('Church_Glow', TXc, TYa - 0.06, 6.8, 1.4, 3.6, depth=0.1, pointed=True, face='-Y')
b.bbox('Bath_Stone', TXc - 0.05, TXc + 0.05, TYa - 0.16, TYa, 6.8, 9.2)
# stage 2: two lancets + statue niches on the west face; lancets on all faces
for dx in (-0.85, 0.85):
    b.arch('Bath_Stone', TXc + dx, TYa, H1 + 1.3, 0.85, 4.2, depth=0.1, pointed=True, face='-Y')
    b.arch('Glass_Dark', TXc + dx, TYa - 0.05, H1 + 1.45, 0.55, 3.8, depth=0.08, pointed=True, face='-Y')
b.arch_y('Bath_Stone', TXb, TYc, H1 + 1.3, 0.85, 4.2, out=1, depth=0.1)
b.arch_y('Glass_Dark', TXb + 0.05, TYc, H1 + 1.45, 0.55, 3.8, out=1, depth=0.08)
b.arch_y('Bath_Stone', TXa, TYc, H1 + 1.3, 0.85, 4.2, out=-1, depth=0.1)
# belfry: three louvred pointed arches per face
for k in (-1, 0, 1):
    for (y, face) in ((TYa, '-Y'), (TYb, '+Y')):
        b.arch('Bath_Stone', TXc + k * 1.55, y, H2 + 0.7, 1.25, 5.2, depth=0.12, pointed=True, face=face)
        b.arch('Wood_Louvre', TXc + k * 1.55, y + (-0.05 if face == '-Y' else 0.05), H2 + 0.85, 0.95, 4.8, depth=0.1, pointed=True, face=face)
    for (x, out) in ((TXa, -1), (TXb, 1)):
        arch_y('Bath_Stone', x, TYc + k * 1.55, H2 + 0.7, 1.25, 5.2, out, 0.12)
        arch_y('Wood_Louvre', x + out * -0.05, TYc + k * 1.55, H2 + 0.85, 0.95, 4.8, out, 0.1)
# broached octagonal spire
RB = (TXb - TXa) / 2 / math.cos(math.radians(22.5)) + 0.03
SPH = 22.0
b.frustum('Spire_Stone', TXc, TYc, H3 + 0.1, RB, SPH, n=8, r_top=0.0, rot=22.5)
# broaches at the 4 corners (tetra wedges from square corner up onto octagon faces)
hw = (TXb - TXa) / 2
hd = (TYb - TYa) / 2
zb = H3 + 0.1
for sx in (-1, 1):
    for sy in (-1, 1):
        A = (TXc + sx * hw, TYc + sy * hd, zb)
        Bp = (TXc + sx * hw, TYc + sy * RB * math.sin(math.radians(22.5)), zb)
        Cp = (TXc + sx * RB * math.sin(math.radians(22.5)), TYc + sy * hd, zb)
        zt = zb + 5.0
        r = RB * (1 - 5.0 / SPH) * math.cos(math.radians(22.5))
        Dp = (TXc + sx * r * 0.99, TYc + sy * r * 0.99, zt)
        b.mesh('Spire_Stone', [A, Bp, Cp, Dp, (A[0], A[1], zb - 0.3), (Bp[0], Bp[1], zb - 0.3), (Cp[0], Cp[1], zb - 0.3)],
               [[0, 1, 3], [1, 2, 3][::1] if False else [1, 2, 3], [2, 0, 3], [0, 2, 1]])
# lucarnes: two tiers on the four faces
for (t, w) in ((7.0, 0.55), (13.0, 0.4)):
    zl = zb + t
    rr = RB * (1 - t / SPH) * math.cos(math.radians(22.5))
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        px, py = TXc + dx * rr, TYc + dy * rr
        if dx != 0:
            b.profile_y('Bath_Stone', [(py - w, zl), (py + w, zl), (py, zl + 1.7)], px if dx > 0 else px - 0.45, px + 0.45 if dx > 0 else px)
            b.profile_y('Glass_Dark', [(py - w * 0.5, zl + 0.05), (py + w * 0.5, zl + 0.05), (py, zl + 1.1)], px + (0.44 if dx > 0 else -0.46), px + (0.46 if dx > 0 else -0.44))
        else:
            b.profile_x('Bath_Stone', [(px - w, zl), (px + w, zl), (px, zl + 1.7)], py if dy > 0 else py - 0.45, py + 0.45 if dy > 0 else py)
            b.profile_x('Glass_Dark', [(px - w * 0.5, zl + 0.05), (px + w * 0.5, zl + 0.05), (px, zl + 1.1)], py + (0.44 if dy > 0 else -0.46), py + (0.46 if dy > 0 else -0.44))
# spire bands + finial
for t in (9.5, 15.5):
    rr = RB * (1 - t / SPH)
    b.frustum('Bath_Stone', TXc, TYc, zb + t, rr * 1.01, 0.25, n=8, r_top=rr * 0.97, rot=22.5)
zt = zb + SPH
b.bbox('Trim_Dark', TXc - 0.06, TXc + 0.06, TYc - 0.06, TYc + 0.06, zt - 0.1, zt + 2.2)
b.bbox('Trim_Dark', TXc - 0.5, TXc + 0.5, TYc - 0.05, TYc + 0.05, zt + 1.3, zt + 1.45)

# ================================================================== WEST FRONT (nave gable) details
# big traceried window
wc = xm
b.arch('Bath_Stone', wc, YF - 0.0, 4.2, 5.4, 10.6, depth=0.28, pointed=True, face='-Y')
b.arch('Church_Glow', wc, YF - 0.22, 4.5, 4.7, 9.9, depth=0.1, pointed=True, face='-Y')
for dx in (-1.17, 0, 1.17):
    b.bbox('Bath_Stone', wc + dx - 0.07, wc + dx + 0.07, YF - 0.34, YF - 0.2, 4.5, 11.0)
for z in (8.8, 11.4):
    b.bbox('Bath_Stone', wc - 2.4, wc + 2.4, YF - 0.34, YF - 0.2, z, z + 0.14)
circle_x('Bath_Stone', wc, YF - 0.2, 12.6, 1.05, -1, 0.14, n=16)
circle_x('Church_Glow_Cool', wc, YF - 0.3, 12.6, 0.8, -1, 0.1, n=16)
for dx in (-1.6, 1.6):
    circle_x('Bath_Stone', wc + dx, YF - 0.2, 11.7, 0.5, -1, 0.12)
    circle_x('Church_Glow_Cool', wc + dx, YF - 0.3, 11.7, 0.35, -1, 0.1)
# N aisle front: lancet + small door
b.arch('Bath_Stone', -2.1, YF, 0.0, 1.9, 3.5, depth=0.2, pointed=True, face='-Y')
b.arch('Door_Wood', -2.1, YF - 0.12, 0.0, 1.4, 3.1, depth=0.12, pointed=True, face='-Y')
b.arch('Bath_Stone', -2.1, YF, 4.4, 1.0, 3.2, depth=0.08, pointed=True, face='-Y')
b.arch('Church_Glow', -2.1, YF - 0.05, 4.55, 0.7, 2.9, depth=0.08, pointed=True, face='-Y')
# front-corner staged buttresses + between nave and tower
for (x, h) in ((AXn, 9.5), (NXa, 12.0)):
    b.bbox('Ragstone', x - 0.4, x + 0.4, YF - 0.6, YF, 0, h)
    b.bbox('Bath_Stone', x - 0.45, x + 0.45, YF - 0.65, YF - 0.55, h - 0.2, h)
    b.bbox('Bath_Stone', x - 0.45, x + 0.45, YF - 0.5, YF - 0.4, 4.0, 4.15)

# ================================================================== SIDE WALLS: aisle windows, clerestory roundels, buttresses
def aisle_bay(x, yc, out, z0=1.9):
    for dx in (-0.95, 0, 0.95):
        arch_y('Bath_Stone', x, yc + dx, z0, 0.78, 3.3, out, 0.1)
        arch_y('Church_Glow' if rng.random() < 0.8 else 'Glass_Dark', x + out * 0.05, yc + dx, z0 + 0.12, 0.5, 2.95, out, 0.08)
    circle_y('Bath_Stone', x, yc, z0 + 3.0 + 0.25, 0.32, out, 0.1, n=8)

# south aisle wall (x = AXs, normal +x)
for yc in (-9.1, -4.6, -0.1):
    aisle_bay(AXs, yc, 1)
for yc in (7.2, 11.7):
    aisle_bay(AXs, yc, 1, z0 = 1.5)
for y in (-11.5, -6.9, -2.3, 3.7, 9.4, 14.8):
    b.bbox('Ragstone', AXs, AXs + 0.65, y - 0.3, y + 0.3, 0, H_AISLE - 0.3)
    b.bbox('Bath_Stone', AXs - 0.02, AXs + 0.7, y - 0.34, y + 0.34, H_AISLE - 0.4, H_AISLE - 0.3)
# north aisle wall (x = AXn, normal -x)
for yc in (-13.2, -8.4, -3.6, 1.2):
    aisle_bay(AXn, yc, -1)
for y in (-15.3, -10.8, -6.0, -1.2, 3.7):
    b.bbox('Ragstone', AXn - 0.65, AXn, y - 0.3, y + 0.3, 0, H_AISLE - 0.3)
# clerestory roundels (nave walls above aisle roofs), both sides
for yc in [-13.2, -8.4, -3.6, 1.2]:
    for (x, out) in ((NXa, -1), (NXb, 1)):
        circle_y('Bath_Stone', x, yc, 10.1, 0.72, out, 0.1)
        circle_y('Church_Glow_Cool', x + out * 0.05, yc, 10.1, 0.52, out, 0.08)
for yc in (8.2, 12.6, 16.4):
    for (x, out) in ((NXa, -1), (NXb, 1)):
        circle_y('Bath_Stone', x, yc, 7.6, 0.65, out, 0.1)
        circle_y('Church_Glow_Cool', x + out * 0.05, yc, 7.6, 0.47, out, 0.08)
# east end (y = YE): chancel big traceried window + side lancets
b.arch('Bath_Stone', xm, YE, 2.4, 3.6, 7.2, depth=0.2, pointed=True, face='+Y')
b.arch('Church_Glow', xm, YE + 0.14, 2.6, 3.0, 6.7, depth=0.1, pointed=True, face='+Y')
for dx in (-0.75, 0.75):
    b.bbox('Bath_Stone', xm + dx - 0.06, xm + dx + 0.06, YE, YE + 0.28, 2.6, 8.6)
circle_x('Bath_Stone', xm, YE + 0.1, 11.3, 0.9, 1, 0.14, n=16)
circle_x('Church_Glow_Cool', xm, YE + 0.18, 11.3, 0.65, 1, 0.1, n=16)
for (x0, x1) in ((AXn, NXa), (NXb, 14.8 if False else AXs)):
    b.arch('Bath_Stone', (x0 + x1) / 2, YE, 1.5, 1.0, 3.0, depth=0.1, pointed=True, face='+Y')
    b.arch('Church_Glow', (x0 + x1) / 2, YE + 0.08, 1.65, 0.7, 2.7, depth=0.08, pointed=True, face='+Y')

# ---- small stone-trim plinth and ground path hint
b.bbox('Bath_Stone', AXn - 0.1, AXs + 0.1, YF - 0.1, YF + 0.05, 0, 0.35)

b.finish('english_martyrs', footprint=FOOT['english_martyrs']['footprint_bbox_m'],
         notes='English Martyrs RC church, Streatham (Purdie 1892-94). Grey Kentish ragstone with Bath-stone dressings (NOT red brick), French Gothic, steep slate roofs, '
               'gable front with big traceried window, slender SW tower with 3-arch louvred belfry and ~46 m broached octagonal spire, lit windows, 1962 north extension.',
         cams={
             'front34': (Vector((-0.55, -1.0, 0.38)), 1.0),
             'front34b': (Vector((0.7, -1.0, 0.3)), 1.0),
             'rear34': (Vector((0.8, 1.0, 0.45)), 1.0),
             'side': (Vector((1.0, -0.1, 0.22)), 1.0),
             'front': (Vector((0.0, -1.0, 0.2)), 1.0),
             'top': (Vector((0.12, -0.5, 1.4)), 1.0),
             'tower': (Vector((0.25, -1.0, 0.2)), 1.0, wpt(THETA, 4, -15, 12), 30),
         })
