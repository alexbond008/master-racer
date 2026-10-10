"""St Matthew's Church, Brixton (1822, Bedford & Porden, Grade II*). Run: blender -b --python build_stmatthews.py
Cues (Historic England / Wikipedia / photos):
 1 giant Greek Doric portico, six unfluted-looking fat tapering columns (no bases) on a stylobate with 5 steps, facing the street (-Y)
 2 full Doric entablature: plain architrave, TRIGLYPH frieze, mutule cornice, low pediment with plain tympanum
 3 pale stuccoed / Roman-cement body on a stone plinth; five bays of pilastered side walls, two tiers of tall windows
 4 low slate gable roof with ridge along Y, tower at the rear (east) end, behind the portico
 5 stepped tower: square stage w/ pilasters -> clock stage (4 clock faces) -> open Doric 'screens' bell stage ->
   octagonal 'Tower of the Winds' lantern (8 columns, lit) -> small crown + cross
 6 three doors at the back of the portico glowing warm; iron churchyard railings and gate along street + sides
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbx_common import *

reset_scene()
B = Builder()
STUCCO = mat('Stucco', hexc('#d9cfb4'), 0.85)
STONE = mat('Stone', hexc('#c4bda9'), 0.8)
STONE_L = mat('StoneLight', hexc('#e6dfcb'), 0.75)
SLATE = mat('Slate', hexc('#3b4048'), 0.8)
IRON = mat('Iron', hexc('#1c1e22'), 0.5, 0.6)
GOLD = mat('Gold', hexc('#c8a24a'), 0.4, 0.8)
WIN = mat('Emit_Window', hexc('#ffc77a'), 0.4, emit=hexc('#ffb050'), strength=4.5)
DOOR = mat('Emit_Door', hexc('#ffd9a0'), 0.4, emit=hexc('#ffc070'), strength=5.0)
CLOCK = mat('Emit_Clock', hexc('#fff6df'), 0.4, emit=hexc('#fff0d0'), strength=7.0)
DARK = mat('Dark', hexc('#15171b'), 0.6)
BRICKY = mat('YellowBrick', hexc('#b9a373'), 0.9)

# ---------------------------------------------------------------- dims
BODY_X = 10.0
Y_FRONT = -17.0
FLOOR_Y = -14.1  # stylobate front edge
WALL_Y = -9.5  # front wall plane
NAVE_BACK = 9.5
TOWER_Y1 = 16.9
EAVE = 13.4
RIDGE = 17.6
STYL_Z = 0.9

# plinth + steps
B.box(0, (WALL_Y + NAVE_BACK) / 2, 0, 2 * BODY_X + 0.6, NAVE_BACK - WALL_Y, 0.9, STONE)
for i in range(5):
    y0 = Y_FRONT + 0.55 * i + 0.4
    B.box(0, (y0 + FLOOR_Y + 0.0) / 2 + 0.0, 0, 21.2 - 0.0, FLOOR_Y - y0 + 0.0, 0.18 * (i + 1), STONE_L)
B.box(0, (FLOOR_Y + WALL_Y) / 2, 0, 21.2, WALL_Y - FLOOR_Y, STYL_Z, STONE_L)  # stylobate floor

# ---------------------------------------------------------------- body (nave)
B.box(0, (WALL_Y + NAVE_BACK) / 2, STYL_Z - 0.01, 2 * BODY_X, NAVE_BACK - WALL_Y, EAVE - STYL_Z, STUCCO)
# gable ends + slate roof
B.vprism([(-BODY_X - 0.3, EAVE), (BODY_X + 0.3, EAVE), (0, RIDGE + 0.1)], WALL_Y - 0.2, 0.6, STUCCO)
for sgn in (-1, 1):
    B.face([(sgn * (BODY_X + 0.7), WALL_Y - 0.3, EAVE - 0.35), (sgn * 0.0, WALL_Y - 0.3, RIDGE + 0.15),
            (0, NAVE_BACK + 0.3, RIDGE + 0.15), (sgn * (BODY_X + 0.7), NAVE_BACK + 0.3, EAVE - 0.35)], SLATE)
    # (mirror winding) double-sided: add reverse so it's visible from either side
    B.face([(sgn * (BODY_X + 0.7), NAVE_BACK + 0.3, EAVE - 0.35), (0, NAVE_BACK + 0.3, RIDGE + 0.15),
            (sgn * 0.0, WALL_Y - 0.3, RIDGE + 0.15), (sgn * (BODY_X + 0.7), WALL_Y - 0.3, EAVE - 0.35)], SLATE)
# cornice band all around the nave at eaves
B.box(0, (WALL_Y + NAVE_BACK) / 2, EAVE - 0.5, 2 * BODY_X + 1.2, NAVE_BACK - WALL_Y + 0.8, 0.55, STONE_L)
# rear gable end wall of nave above tower join
B.vprism([(-BODY_X - 0.3, EAVE), (BODY_X + 0.3, EAVE), (0, RIDGE + 0.1)], NAVE_BACK - 0.2, 0.6, STUCCO)

# side walls: pilasters + two tiers of windows (5 bays)
for sgn in (-1, 1):
    xw = sgn * BODY_X
    nb = 5
    L = NAVE_BACK - WALL_Y - 2.0
    for j in range(nb + 1):
        y = WALL_Y + 1.0 + L * j / nb
        B.box(xw + sgn * 0.25, y, STYL_Z, 0.5, 1.0, EAVE - STYL_Z - 0.5, STUCCO)
        B.box(xw + sgn * 0.35, y, STYL_Z, 0.75, 1.3, 0.5, STONE)  # base
        B.box(xw + sgn * 0.35, y, EAVE - 1.1, 0.75, 1.3, 0.35, STONE_L)  # capital
    for j in range(nb):
        y = WALL_Y + 1.0 + L * (j + 0.5) / nb
        B.push(sgn * math.pi / 2 + (math.pi if sgn > 0 else 0) * 0, xw + sgn * 0.0, y)
        B.pop()
        # windows drawn with oriented boxes
        for (z0, z1, w, arch) in ((2.4, 5.4, 1.9, False), (7.6, 11.6, 1.9, True)):
            # face normal +x*sgn: build in a local frame rotated so local -Y points outward (+sgn X)
            ang = (math.pi / 2) if sgn > 0 else (-math.pi / 2)
            B.push(ang, xw + sgn * 0.02, y)
            B.box(0, 0.02, z0 - 0.15, w + 0.6, 0.1, z1 - z0 + 0.3, STONE_L)
            if arch:
                B.arch_prism(-w / 2, w / 2, -0.1, z0, z1 - w / 2, 0.14, WIN)
            else:
                B.box(0, -0.05, z0, w, 0.15, z1 - z0, WIN)
            B.pop()

# rear tower base wall y 9.5..16.9
TX0, TX1 = -4.6, 4.6
TY0, TY1 = NAVE_BACK - 0.3, TOWER_Y1
TCX, TCY = 0.0, (TY0 + TY1) / 2
S1 = 21.0  # square plain stage top
B.box(TCX, TCY, 0, TX1 - TX0, TY1 - TY0, S1, STUCCO)
B.box(TCX, TCY, 0, TX1 - TX0 + 0.5, TY1 - TY0 + 0.5, 1.3, STONE)  # plinth
# tower corner pilasters + two lit arched windows each side
for i, (cx, cy) in enumerate([(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)]):
    B.box(cx, cy, 1.3, 1.1, 1.1, S1 - 1.3, STONE_L)
for face in range(4):
    # faces: -Y (front, hidden by nave mostly), +Y rear, +-X
    if face == 0:
        continue
    a = [0, math.pi, math.pi / 2, -math.pi / 2][face]
    off = [None, (0, TY1 + 0.03), (TX1 + 0.03, TCY), (TX0 - 0.03, TCY)][face]
    B.push(a, off[0], off[1])
    # local -Y after rotation ... we want local +y direction outward: rotate so outward = local -Y
    B.pop()
for (ox, oy, ang) in ((0, TY1 + 0.03, math.pi), (TX1 + 0.03, TCY, math.pi / 2), (TX0 - 0.03, TCY, -math.pi / 2)):
    B.push(ang, ox, oy)
    for (z0, z1, w) in ((4.5, 9.0, 1.6), (12.5, 17.5, 1.6)):
        B.arch_prism(-w / 2 - 0.2, w / 2 + 0.2, 0.0, z0, z1 - w / 2 - 0.2, 0.1, STONE_L)
        B.arch_prism(-w / 2, w / 2, -0.06, z0 + 0.1, z1 - w / 2 - 0.2, 0.12, WIN)
    B.pop()
# cornice
B.box(TCX, TCY, S1, TX1 - TX0 + 1.0, TY1 - TY0 + 1.0, 0.7, STONE_L)
# clock stage (square) z 21.7..25.2 with 4 clock faces
C0, C1 = S1 + 0.7, 25.2
B.box(TCX, TCY, C0, TX1 - TX0 - 0.6, TY1 - TY0 - 0.6, C1 - C0, STUCCO)
cz = (C0 + C1) / 2
for (ox, oy, ang, wd) in ((0, TCY - (TY1 - TY0) / 2 + 0.3, 0.0, 0), (0, TCY + (TY1 - TY0) / 2 - 0.3, math.pi, 0),
                          (TX1 - 0.3, TCY, math.pi / 2, 0), (TX0 + 0.3, TCY, -math.pi / 2, 0)):
    B.push(ang, ox, oy)
    B.box(0, 0, cz - 1.5, 3.2, 0.3, 3.0, STONE_L)
    ring = [(math.cos(2 * math.pi * i / 24) * 1.35, -0.17, cz + math.sin(2 * math.pi * i / 24) * 1.35) for i in range(24)]
    B.face(ring, GOLD)
    dial = [(math.cos(2 * math.pi * i / 24) * 1.2, -0.2, cz + math.sin(2 * math.pi * i / 24) * 1.2) for i in range(24)]
    B.face(dial, CLOCK)
    for hr in range(12):
        t = 2 * math.pi * hr / 12
        r = 1.0
        B.obox((math.cos(t) * r, -0.24, cz + math.sin(t) * r), (math.cos(t), 0, math.sin(t)), (0, 1, 0), (-math.sin(t), 0, math.cos(t)),
               0.2, 0.04, 0.08, DARK)
    for (ah, ln) in ((math.radians(150), 0.8), (math.radians(40), 0.55)):
        B.obox((math.cos(ah) * ln / 2, -0.27, cz + math.sin(ah) * ln / 2), (math.cos(ah), 0, math.sin(ah)), (0, 1, 0),
               (-math.sin(ah), 0, math.cos(ah)), ln, 0.04, 0.1, DARK)
    B.pop()
B.box(TCX, TCY, C1, TX1 - TX0 + 0.2, TY1 - TY0 + 0.2, 0.55, STONE_L)  # cornice

# open Doric bell stage ('screens'): 4 corner piers + 2 columns per face, glowing core
D0, D1 = C1 + 0.55, 30.0
B.box(TCX, TCY, D0, 5.2, 5.2, D1 - D0, WIN)  # lit interior (core) shows through the openings
for sx in (-1, 1):
    for sy in (-1, 1):
        B.box(TCX + sx * 3.3, TCY + sy * 3.3, D0, 1.3, 1.3, D1 - D0, STUCCO)
        B.box(TCX + sx * 3.3, TCY + sy * 3.3, D1 - 0.35, 1.7, 1.7, 0.35, STONE_L)
        B.box(TCX + sx * 3.3, TCY + sy * 3.3, D0, 1.7, 1.7, 0.4, STONE)
# 2 Doric columns per face between the piers
for k in (-1.1, 1.1):
    for (cx, cy) in ((TCX + k, TCY - 3.4), (TCX + k, TCY + 3.4), (TCX - 3.4, TCY + k), (TCX + 3.4, TCY + k)):
        B.frustum(cx, cy, D0 + 0.3, D1 - 0.5, 0.42, 0.34, STUCCO, segs=10, smooth=False)
B.box(TCX, TCY, D1, 8.0, 8.0, 0.45, STONE_L)  # entablature
B.box(TCX, TCY, D1 + 0.45, 7.2, 7.2, 0.3, STONE)
# octagonal "Tower of the Winds" lantern: 8 columns around lit core
O0 = D1 + 0.75
O1 = O0 + 4.6
B.frustum(TCX, TCY, O0, O1 - 0.4, 2.7, 2.55, STUCCO, segs=8, rot=math.pi / 8, smooth=False)
for k in range(8):
    a = 2 * math.pi * k / 8
    ax, ay = TCX + math.cos(a) * 2.75, TCY + math.sin(a) * 2.75
    B.frustum(ax, ay, O0, O1 - 0.4, 0.3, 0.25, STONE_L, segs=8, smooth=False)
    # lit panel centred between columns
    am = a + math.pi / 8
    B.box(TCX + math.cos(am) * 2.6, TCY + math.sin(am) * 2.6, O0 + 0.7, 1.6, 0.14, 2.6, WIN, rot=am + math.pi / 2)
B.frustum(TCX, TCY, O1 - 0.4, O1, 3.4, 3.4, STONE_L, segs=8, rot=math.pi / 8, smooth=False)  # entablature
B.frustum(TCX, TCY, O1, O1 + 1.6, 3.0, 0.5, STONE, segs=8, rot=math.pi / 8, smooth=False)  # low roof
B.frustum(TCX, TCY, O1 + 1.6, O1 + 2.1, 0.55, 0.55, GOLD, segs=8)  # crown ring
for k in range(6):  # crown points
    a = 2 * math.pi * k / 6
    B.frustum(TCX + math.cos(a) * 0.4, TCY + math.sin(a) * 0.4, O1 + 2.1, O1 + 2.7, 0.14, 0.0, GOLD, segs=4)
B.box(TCX, TCY, O1 + 2.1, 0.12, 0.12, 2.4, GOLD)  # cross
B.box(TCX, TCY, O1 + 3.4, 1.0, 0.12, 0.12, GOLD)

# ---------------------------------------------------------------- portico
COL_H = 8.6
Z0 = STYL_Z
colx = [-8.25, -4.95, -1.65, 1.65, 4.95, 8.25]
COL_Y = -13.1
for x in colx:
    B.frustum(x, COL_Y, Z0, Z0 + COL_H, 0.78, 0.6, STUCCO, segs=20, smooth=True)
    B.frustum(x, COL_Y, Z0 + COL_H, Z0 + COL_H + 0.3, 0.6, 0.78, STONE_L, segs=20)  # echinus
    B.box(x, COL_Y, Z0 + COL_H + 0.3, 1.9, 1.9, 0.3, STONE_L)  # abacus
ZA = Z0 + COL_H + 0.6  # architrave bottom
B.box(0, -13.1, ZA, 20.4, 1.7, 1.0, STONE_L)  # architrave
FZ0 = ZA + 1.0
B.box(0, -13.1, FZ0, 20.4, 1.5, 1.15, STUCCO)  # frieze
for i in range(13):
    x = -9.9 + 1.65 * i  # triglyphs over columns and between
    B.box(x, -13.9, FZ0 + 0.05, 0.72, 0.15, 1.05, STONE_L)
    for g in (-0.2, 0, 0.2):
        B.box(x + g, -14.0, FZ0 + 0.08, 0.06, 0.05, 0.98, DARK)
CZ0 = FZ0 + 1.15
B.box(0, -13.3, CZ0, 21.4, 2.3, 0.5, STONE_L)  # cornice
for i in range(25):
    B.box(-10.2 + 0.85 * i, -14.3, CZ0 - 0.12, 0.5, 0.45, 0.12, STONE)  # mutules
PZ = CZ0 + 0.5
rise = 2.5
B.vprism([(-10.7, PZ), (10.7, PZ), (0, PZ + rise)], -14.25, 0.5, STONE_L)  # tympanum
B.vprism([(-9.5, PZ + 0.25), (9.5, PZ + 0.25), (0, PZ + rise - 0.3)], -14.3, 0.1, STUCCO)
# raking cornice (stone slab following the slope) front
for sgn in (-1, 1):
    B.face([(sgn * 10.9, -14.5, PZ), (sgn * 10.9, -9.6, PZ), (0, -9.6, PZ + rise + 0.2), (0, -14.5, PZ + rise + 0.2)], SLATE)
    B.face([(0, -14.5, PZ + rise + 0.2), (0, -9.6, PZ + rise + 0.2), (sgn * 10.9, -9.6, PZ), (sgn * 10.9, -14.5, PZ)], SLATE)
for sgn in (-1, 1):
    # raking edge (thick stone moulding)
    pass
# portico ceiling (underside) + back wall features
B.box(0, (-14.1 + -9.5) / 2, ZA - 0.05, 20.4, 4.6, 0.1, STONE_L)
# doors (3) with glowing leaves + fanlight, windows between; inside portico on the front wall at WALL_Y
for dx in (-4.4, 0.0, 4.4):
    B.box(dx, WALL_Y - 0.06, STYL_Z, 2.8, 0.14, 5.4, STONE_L)
    B.box(dx, WALL_Y - 0.14, STYL_Z, 2.2, 0.12, 4.6, DOOR)
    B.box(dx, WALL_Y - 0.2, STYL_Z + 2.3, 0.08, 0.06, 2.3, DARK)
    B.box(dx, WALL_Y - 0.14, STYL_Z + 5.0, 2.2, 0.12, 0.7, WIN)
for wx in (-2.2, 2.2, -7.5, 7.5):
    B.box(wx, WALL_Y - 0.1, 6.2, 1.5, 0.12, 2.8, WIN)
    B.box(wx, WALL_Y - 0.05, 5.9, 2.0, 0.08, 3.4, STONE_L)
# lamp brackets between columns
for lx in (-3.3, 3.3):
    B.sphere(lx, -11.5, 8.2, 0.28, DOOR, 8, 5)

# ---------------------------------------------------------------- railings (churchyard): front + sides
def railing(p0, p1, h=1.2, step=0.28):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = int(L / step)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    B.box((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.0, L, 0.35, 0.45, STONE, rot=ang)
    B.box((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.45 + h - 0.15, L, 0.05, 0.05, IRON, rot=ang)
    B.box((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 0.5, L, 0.05, 0.05, IRON, rot=ang)
    for i in range(n + 1):
        t = i / max(n, 1)
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        B.box(x, y, 0.45, 0.04, 0.04, h, IRON)
        B.box(x, y, 0.45 + h, 0.07, 0.07, 0.12, IRON)  # spear tip


YF = -16.8
railing((-11.8, YF), (-2.0, YF))
railing((2.0, YF), (11.8, YF))
for gx in (-2.0, 2.0):
    B.box(gx, YF, 0.0, 0.7, 0.7, 2.0, STONE_L)
    B.box(gx, YF, 2.0, 0.9, 0.9, 0.2, STONE)
    B.sphere(gx, YF, 2.45, 0.2, STONE_L, 8, 5)
railing((-11.8, YF), (-11.8, -3.0))
railing((11.8, YF), (11.8, -3.0))

cams = [
    ('front34', (-34, -52, 14), (0, 0, 14), 38),
    ('front', (0, -62, 12), (0, 0, 16), 38),
    ('rear34', (38, 50, 24), (0, 0, 14), 38),
    ('side', (-62, 0, 14), (0, 0, 16), 38),
    ('top', (0, -22, 70), (0, 2, 5), 38),
]
finish(B, 'stmatthews', footprint=(24, 34),
       notes="St Matthew's Church Brixton: giant Greek Doric hexastyle portico facing -Y (6 columns, triglyph frieze, pediment, 5 steps), pale stuccoed nave with slate gable roof, rear stepped tower (clock stage, open Doric bell stage, octagonal Tower-of-the-Winds lantern, crown+cross) ~38.5 m, railings on the street + side boundary. Origin = footprint centre.",
       cams=cams, bevel=0.03, skip_bevel=('Emit_Window', 'Emit_Door', 'Emit_Clock'), res=(1000, 750))
