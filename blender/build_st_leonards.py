"""st_leonards - St Leonard's parish church, Streatham High Road (Grade II).

Cues from the Historic England listing text + Commons photographs (CORRECTING the brief: no battlements / stair turret / ragstone):
 1. SQUARE WEST TOWER, 14th-c. lower stage of KNAPPED FLINT with stone dressings; upper stages + SPIRE rebuilt 1841 after a lightning strike.
 2. Upper tower and nave are BUFF-OCHRE STUCCO; tower has a round CLOCK face on the street side, two tall narrow louvred lancets per face in the belfry.
 3. SLENDER OCTAGONAL SPIRE in dark grey slate/lead, small gabled LUCARNES low on four faces, thin finial cross; ~39 m overall.
 4. Broad NAVE (1831, J T Parkinson): brick clad in stucco, low-pitched roof behind a plain parapet, tall two-light pointed windows with Decorated tracery, flat pilaster buttresses, cast-iron gallery inside (glows at night).
 5. CHANCEL (1863, William Dyce) in contrasting rubble STONE with thin red-brick bands, STEEP SLATE roof, east gable with round (oculus) window and lancets.
 6. Two gabled stone chapels/vestries (1877) flank the chancel, giving a three-gable east end (as seen in photos).
 7. Churchyard with chest tombs and headstones, paths.
 8. Footprint ~40 x 37 m, long axis NW-SE in the game frame (tower at the NW end), rotated -38.7 deg.
"""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sl_lib import *
from mathutils import Vector

THETA = -38.7
rng = random.Random(11)
b = Builder(THETA)

define('Stucco', '#c9b283', rough=0.9)
define('Stucco_Light', '#d8c79d', rough=0.9)
define('Stone_Trim', '#d6cdb9', rough=0.85)
define('Flint', '#5d5f5e', rough=0.95)
define('Rubble', '#8e8676', rough=0.95)
define('Brick_Band', '#a45a40', rough=0.9)
define('Slate_Roof', '#363a42', rough=0.6, metal=0.1)
define('Spire_Lead', '#4b4d4f', rough=0.55, metal=0.3)
define('Church_Glow', '#ffcf86', rough=0.4, emit=2.6)
define('Clock_Face', '#fff4d6', rough=0.4, emit=3.0)
define('Grave', '#6f6e69', rough=0.95)
define('Grass', '#46603a', rough=1.0)
define('Gravel', '#9b9283', rough=1.0)

# ---------------------------------------------------------------- dimensions (local frame, +x = west->east, tower at -x)
NX0, NX1 = -29.0, -2.5          # nave+aisles
NY0, NY1 = -7.6, 8.0
H_NAVE = 9.6
TX0, TX1, TY0, TY1 = -29.0, -22.5, -3.1, 3.5   # tower
H_T1 = 9.6    # flint stage top
H_T2 = 17.0   # clock stage top
H_T3 = 22.0   # belfry top
H_SPIRE = 17.0

# ---------------------------------------------------------------- nave
b.bbox('Stucco', NX0, NX1, NY0, NY1, 0, H_NAVE)
b.bbox('Stone_Trim', NX0 - 0.15, NX1 + 0.15, NY0 - 0.2, NY1 + 0.2, H_NAVE - 0.5, H_NAVE + 0.15)   # cornice/parapet band
b.bbox('Stone_Trim', NX0 - 0.1, NX1 + 0.1, NY0 - 0.1, NY1 + 0.1, 0, 0.5)                           # plinth
b.hip('Slate_Roof', NX0 + 0.3, NX1 - 0.3, NY0 + 0.3, NY1 - 0.3, H_NAVE + 0.1, 2.4, top_frac=0.0)
# aisle/nave buttress pilasters
bays = 5
bx = [NX0 + 4.0 + i * ((NX1 - NX0 - 4.0 - 0.8) / (bays)) for i in range(bays + 1)]
for x in bx:
    for (y, o) in ((NY0, -1), (NY1, 1)):
        b.bbox('Stone_Trim', x - 0.3, x + 0.3, y if o > 0 else y - 0.35, y + 0.35 if o > 0 else y, 0, H_NAVE)

def arch_win_y(mat, x_wall, cy, z0, w, h, out, depth, pointed=True):
    pts = b.arch_pts(cy, z0, w, h, pointed)
    if out > 0:
        b.profile_y(mat, pts, x_wall, x_wall + depth)
    else:
        b.profile_y(mat, pts, x_wall - depth, x_wall)

# pointed two-light windows along both nave sides (between pilasters)
for i in range(bays):
    xc = (bx[i] + bx[i + 1]) / 2
    for (y, o) in ((NY0, -1), (NY1, 1)):
        face = '-Y' if o < 0 else '+Y'
        b.arch('Stone_Trim', xc, y, 1.9, 2.5, 6.4, depth=0.10, pointed=True, face=face)
        glow = 'Church_Glow' if rng.random() < 0.75 else 'Glass_Dark'
        b.arch(glow, xc, y + (-0.08 if o < 0 else 0.08), 2.2, 2.0, 5.8, depth=0.08, pointed=True, face=face)
        b.bbox('Stone_Trim', xc - 0.06, xc + 0.06, y - 0.2 if o < 0 else y, y if o < 0 else y + 0.2, 2.2, 6.4)  # mullion
        # tracery roundel
        b.cyl('Stone_Trim', xc, y + o * 0.12, 6.1, 0.3, 0.1, n=10, sx=1, sy=1)

# ---------------------------------------------------------------- tower
# flint lower stage
b.bbox('Flint', TX0 - 0.12, TX1, TY0 - 0.12, TY1 + 0.12, 0, H_T1 - 0.2)
b.bbox('Stone_Trim', TX0 - 0.2, TX1 + 0.1, TY0 - 0.2, TY1 + 0.2, H_T1 - 0.4, H_T1 + 0.1)  # string course
# stucco stages
b.bbox('Stucco_Light', TX0, TX1, TY0, TY1, H_T1, H_T3)
b.bbox('Stone_Trim', TX0 - 0.15, TX1 + 0.15, TY0 - 0.15, TY1 + 0.15, H_T2 - 0.2, H_T2 + 0.15)
b.bbox('Stone_Trim', TX0 - 0.25, TX1 + 0.25, TY0 - 0.25, TY1 + 0.25, H_T3 - 0.35, H_T3 + 0.15)  # belfry cornice
# corner pilasters on tower
for (cx, cy) in ((TX0, TY0), (TX1, TY0), (TX0, TY1), (TX1, TY1)):
    b.bbox('Stone_Trim', cx - 0.35, cx + 0.35, cy - 0.35, cy + 0.35, 0, H_T3 - 0.4)
tcy = (TY0 + TY1) / 2
tcx = (TX0 + TX1) / 2
# west doorway + window (west face is x = TX0)
arch_win_y('Stone_Trim', TX0, tcy, 0.0, 2.6, 4.6, -1, 0.18)
arch_win_y('Glass_Dark', TX0 - 0.1, tcy, 0.0, 1.9, 4.0, -1, 0.1)
arch_win_y('Stone_Trim', TX0, tcy, 5.8, 2.0, 3.5, -1, 0.14)
arch_win_y('Church_Glow', TX0 - 0.06, tcy, 6.0, 1.5, 3.1, -1, 0.1)
# stage-2 slit windows on all faces, clock on street-facing sides (-y and -x)
for face_y, o in ((TY0, -1), (TY1, 1)):
    b.arch('Glass_Dark', tcx, face_y + o * 0.0, H_T1 + 1.0, 0.7, 3.0, depth=0.1, pointed=True, face='-Y' if o < 0 else '+Y')
# clock faces: south (-y) and west (-x)
def disc_x_plane(mat, cx, y, cz, r, depth, n=20):  # facing -Y
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    b.profile_x(mat, pts, y - depth, y)
def disc_y_plane(mat, x, cy, cz, r, depth, n=20):  # facing -X
    pts = [(cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    b.profile_y(mat, pts, x - depth, x)
disc_x_plane('Stone_Trim', tcx, TY0 - 0.02, 14.2, 1.55, 0.12)
disc_x_plane('Clock_Face', tcx, TY0 - 0.12, 14.2, 1.3, 0.08)
b.bbox('Trim_Dark', tcx - 0.06, tcx + 0.06, TY0 - 0.26, TY0 - 0.2, 14.2, 15.3)
b.bbox('Trim_Dark', tcx - 0.06, tcx + 0.8, TY0 - 0.26, TY0 - 0.2, 14.15, 14.27)
disc_y_plane('Stone_Trim', TX0 - 0.02, tcy, 14.2, 1.55, 0.12)
disc_y_plane('Clock_Face', TX0 - 0.12, tcy, 14.2, 1.3, 0.08)
# belfry louvred lancets, two per face, all four faces
for k in (-1, 1):
    zc = H_T2 + 0.5
    off = k * 1.1
    for (y, o) in ((TY0, -1), (TY1, 1)):
        b.arch('Stone_Trim', tcx + off, y, zc, 1.1, 3.9, depth=0.12, pointed=True, face='-Y' if o < 0 else '+Y')
        b.arch('Glass_Dark', tcx + off, y + o * -0.05, zc + 0.15, 0.8, 3.5, depth=0.1, pointed=True, face='-Y' if o < 0 else '+Y')
    for (x, o) in ((TX0, -1), (TX1, 1)):
        arch_win_y('Stone_Trim', x, tcy + off, zc, 1.1, 3.9, o, 0.12)
        arch_win_y('Glass_Dark', x + o * -0.05, tcy + off, zc + 0.15, 0.8, 3.5, o, 0.1)

# spire (octagon sitting on the square tower via a short blind plinth)
RB = 3.52
b.frustum('Spire_Lead', tcx, tcy, H_T3 + 0.1, RB, H_SPIRE, n=8, r_top=0.0, rot=22.5)
# lucarnes (gabled dormer openings low on the spire)
zl = H_T3 + 0.1 + 5.2
r = RB * (1 - 5.2 / H_SPIRE) * math.cos(math.radians(22.5))
for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    px, py = tcx + dx * (r + 0.05), tcy + dy * (r + 0.05)
    if dx != 0:
        b.profile_y('Stone_Trim', [(py - 0.5, zl), (py + 0.5, zl), (py, zl + 1.5)], px - 0.02 if dx > 0 else px - 0.4, px + 0.4 if dx > 0 else px + 0.02)
        b.profile_y('Glass_Dark', [(py - 0.28, zl + 0.05), (py + 0.28, zl + 0.05), (py, zl + 1.0)], px + (0.38 if dx > 0 else -0.4), px + (0.42 if dx > 0 else -0.38))
    else:
        b.profile_x('Stone_Trim', [(px - 0.5, zl), (px + 0.5, zl), (px, zl + 1.5)], py - 0.02 if dy > 0 else py - 0.4, py + 0.4 if dy > 0 else py + 0.02)
        b.profile_x('Glass_Dark', [(px - 0.28, zl + 0.05), (px + 0.28, zl + 0.05), (px, zl + 1.0)], py + (0.38 if dy > 0 else -0.4), py + (0.42 if dy > 0 else -0.38))
zt = H_T3 + 0.1 + H_SPIRE
b.bbox('Trim_Dark', tcx - 0.07, tcx + 0.07, tcy - 0.07, tcy + 0.07, zt - 0.1, zt + 1.7)
b.bbox('Trim_Dark', tcx - 0.45, tcx + 0.45, tcy - 0.05, tcy + 0.05, zt + 1.0, zt + 1.12)
# tower-top corner pinnacles
for (cx, cy) in ((TX0, TY0), (TX1, TY0), (TX0, TY1), (TX1, TY1)):
    b.bbox('Stone_Trim', cx - 0.3, cx + 0.3, cy - 0.3, cy + 0.3, H_T3 + 0.1, H_T3 + 0.9)
    b.frustum('Stone_Trim', cx, cy, H_T3 + 0.9, 0.38, 1.0, n=4, rot=45)

# ---------------------------------------------------------------- chancel (stone, steep slate roof) + two gabled chapels
CX0, CX1 = NX1, 10.6
CY0, CY1 = -4.0, 4.5
H_CW = 6.8
b.bbox('Rubble', CX0, CX1, CY0, CY1, 0, H_CW)
b.gable('Slate_Roof', CX0, CX1, CY0, CY1, H_CW, 5.4, ridge='x', oh=0.35)
# east gable infill is part of the profile (slate colour) - add stone gable faces
b.profile_y('Rubble', [(CY0 - 0.35, H_CW - 0.05), (CY1 + 0.35, H_CW - 0.05), ((CY0 + CY1) / 2, H_CW + 5.4 + 0.2)], CX1 + 0.36, CX1 + 0.42)
# brick bands
for z in [0.9 + i * 0.95 for i in range(7)]:
    b.bbox('Brick_Band', CX0, CX1 + 0.04, CY0 - 0.04, CY1 + 0.04, z, z + 0.16)
# east window cluster: lancets + oculus
ccy = (CY0 + CY1) / 2
for dy in (-1.6, 0, 1.6):
    arch_win_y('Stone_Trim', CX1 + 0.05, ccy + dy, 1.9, 1.0, 3.9 if dy == 0 else 3.0, 1, 0.12)
    arch_win_y('Church_Glow', CX1 + 0.1, ccy + dy, 2.1, 0.7, 3.5 if dy == 0 else 2.6, 1, 0.08)
# oculus (round window) in the east gable
pts = [(ccy + 1.05 * math.cos(2 * math.pi * i / 16), H_CW + 2.3 + 1.05 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
b.profile_y('Stone_Trim', pts, CX1 + 0.42, CX1 + 0.5)
pts = [(ccy + 0.78 * math.cos(2 * math.pi * i / 16), H_CW + 2.3 + 0.78 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
b.profile_y('Church_Glow', pts, CX1 + 0.48, CX1 + 0.56)

# south chapel (gable end faces east) and north vestry/chapel
def chapel(y0, y1, x0, x1, hw, rise, name):
    b.bbox('Rubble', x0, x1, y0, y1, 0, hw)
    b.gable('Slate_Roof', x0, x1, y0, y1, hw, rise, ridge='x', oh=0.3)
    b.profile_y('Rubble', [(y0 - 0.3, hw - 0.05), (y1 + 0.3, hw - 0.05), ((y0 + y1) / 2, hw + rise + 0.2)], x1 + 0.31, x1 + 0.37)
    for z in [0.9 + i * 0.95 for i in range(int((hw - 0.8) / 0.95) + 1)]:
        b.bbox('Brick_Band', x0, x1 + 0.04, y0 - 0.04, y1 + 0.04, z, z + 0.16)
    cy = (y0 + y1) / 2
    for dy in (-1.0, 1.0):
        arch_win_y('Stone_Trim', x1 + 0.05, cy + dy, 1.5, 0.9, 3.0, 1, 0.12)
        arch_win_y('Church_Glow', x1 + 0.1, cy + dy, 1.7, 0.6, 2.6, 1, 0.08)
    pts = [(cy + 0.6 * math.cos(2 * math.pi * i / 14), hw + 1.6 + 0.6 * math.sin(2 * math.pi * i / 14)) for i in range(14)]
    b.profile_y('Stone_Trim', pts, x1 + 0.37, x1 + 0.45)
    pts = [(cy + 0.44 * math.cos(2 * math.pi * i / 14), hw + 1.6 + 0.44 * math.sin(2 * math.pi * i / 14)) for i in range(14)]
    b.profile_y('Church_Glow', pts, x1 + 0.43, x1 + 0.5)

chapel(-12.6, -4.0, NX1, 4.9, 5.8, 4.2, 'south')
chapel(4.5, 8.9, NX1, 8.2, 5.2, 3.6, 'north')
# lower lean-to bays filling the footprint steps beside the chancel
b.bbox('Rubble', 4.9, 8.2, -8.7, -4.0, 0, 4.2)
b.lean('Slate_Roof', 4.8, 8.3, -8.8, -3.9, 4.2, 5.6, slope='y+')
b.bbox('Rubble', NX1, 1.7, 8.9, 11.1, 0, 4.2)
b.lean('Slate_Roof', NX1 - 0.1, 1.8, 8.8, 11.2, 4.2, 5.4, slope='y-')
# south side lancets on the long chancel wall are hidden by chapels; add small lancets on the chancel's flank beyond
# ---------------------------------------------------------------- churchyard: chest tombs, headstones, path
bounds = FOOT['st_leonards']
bx0, bx1 = bounds['bbox_x']
by0, by1 = bounds['bbox_y']
th = math.radians(THETA)
def world(x, y):
    return (x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th))
def inside_world_bbox(x, y, m=1.8):
    wx, wy = world(x, y)
    return bx0 + m < wx < bx1 - m and by0 + m < wy < by1 - m
def blocked(x, y, m=1.2):
    for (x0, x1, y0, y1) in ((NX0, NX1, NY0, NY1), (CX0, 10.6, CY0, CY1), (NX1, 8.2, -12.6, -4.0), (NX1, 8.2, 4.5, 11.1), (TX0, TX1, TY0, TY1)):
        if x0 - m < x < x1 + m and y0 - m < y < y1 + m:
            return True
    return False
placed = 0
tries = 0
while placed < 26 and tries < 600:
    tries += 1
    x, y = rng.uniform(-30, 16), rng.uniform(-16, 14)
    if blocked(x, y) or not inside_world_bbox(x, y):
        continue
    if placed % 5 == 0:
        b.box('Grave', x, y, 0, 2.0, 0.95, 0.9, rot=rng.choice([0, 90]))
        b.box('Stone_Trim', x, y, 0.9, 2.15, 1.1, 0.12, rot=0)
    else:
        b.box('Grave', x, y, 0, 0.7, 0.14, rng.uniform(0.8, 1.3), rot=rng.uniform(-8, 8))
    placed += 1
print('graves', placed)

b.finish('st_leonards', footprint=FOOT['st_leonards']['footprint_bbox_m'],
         notes="St Leonard's Church, Streatham. Flint-and-stucco west tower with clock and slate octagonal spire (~39 m), stucco nave with pointed windows, "
               "stone chancel + two gabled stone chapels (three-gable east end), churchyard tombs. Tower is at the NW end in the game frame.",
         cams={
             'front34': (Vector((-0.8, -1.0, 0.42)), 1.0),
             'rear34': (Vector((0.8, 1.0, 0.45)), 1.0),
             'side': (Vector((1.0, -0.1, 0.22)), 1.0),
             'front': (Vector((0.0, -1.0, 0.2)), 1.0),
             'top': (Vector((0.12, -0.5, 1.4)), 1.0),
             'tower': (Vector((-0.6, -0.8, 0.35)), 1.0, wpt(THETA, -26, 0, 18), 24),
             'east': (Vector((0.9, -0.4, 0.3)), 1.0, wpt(THETA, 4, 0, 5), 30),
         })
