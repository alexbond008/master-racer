"""Lambeth Town Hall (Septimus Warwick & H. Austen Hall, 1908). Run: blender -b --python build_townhall.py
Cues (Historic England 1080534 / Wikipedia / photos):
 1 red brick body (4 storeys ~15 m) with Portland-stone dressings, granite plinth, balustraded parapet + heavy modillion cornice
 2 rusticated stone ground floor (horizontal joints), round-headed ground windows, stone quoins
 3 rounded corner frontage at the junction (OSM arc at +X end): stone, Doric pilasters + central door, coat of arms,
   five tall first-floor windows with oculi alternating with Ionic columns
 4 41 m square brick clock tower with wide stone quoins, behind/above the curved bay
 5 four lit clock faces (stone surround, open pediments above), sculpted figures at the stage corners (Justice/Science/Art/Literature)
 6 heavy bracketed cornice, belfry stage with scrolled angle buttresses, crown finial on plinth
 7 lit windows everywhere (warm), slate roof behind balustrade, chimneys
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbx_common import *
from lbx_common import _area

reset_scene()
B = Builder()
BRICK = mat('Brick', hexc('#8b3d30'), 0.9)
STONE = mat('PortlandStone', hexc('#ddd6c5'), 0.7)
STONE_D = mat('StoneShade', hexc('#bdb5a3'), 0.8)
SLATE_D = mat('SlateDark', hexc('#23272d'), 0.8)
GRANITE = mat('Granite', hexc('#4c5056'), 0.5)
SLATE = mat('Slate', hexc('#353a42'), 0.8)
COPPER = mat('Copper', hexc('#5fa08a'), 0.45, 0.4)
WIN = mat('Emit_Window', hexc('#ffc77a'), 0.4, emit=hexc('#ffb050'), strength=4.5)
CLOCK = mat('Emit_Clock', hexc('#fff6df'), 0.4, emit=hexc('#fff0d0'), strength=7.0)
DARK = mat('Dark', hexc('#14161a'), 0.6)
GOLD = mat('Gold', hexc('#c9a24a'), 0.4, 0.8)
DOOR = mat('Emit_Door', hexc('#ffd9a0'), 0.4, emit=hexc('#ffc070'), strength=5.0)

POLY = [(-36.08, -16.94), (-36.28, -8.24), (-34.8, -8.21), (-35.14, 9.85), (-22.75, 10.18), (-22.56, -0.45),
        (-16.17, -0.37), (-16.07, -7.93), (-6.13, -7.9), (-6.39, -2.43), (0.31, 12.85), (-1.35, 14.68),
        (-2.09, 14.08), (-8.67, 20.99), (-9.52, 20.13), (-10.25, 20.92), (-16.82, 14.57), (-33.2, 31.45),
        (-16.39, 47.16), (-13.63, 44.14), (-11.75, 45.93), (15.37, 17.41), (14.64, 16.81), (33.97, -3.33),
        (34.76, -2.6), (38.1, -6.04), (37.59, -7.52), (39.79, -10.21), (39.9, -11.88), (39.03, -13.82),
        (37.52, -14.93), (36.01, -15.18), (34.57, -14.77), (33.85, -17.08), (27.51, -17.02), (27.55, -16.26),
        (1.32, -16.51), (1.23, -17.4), (-3.23, -17.49), (-3.23, -16.64), (-30.89, -16.78), (-30.84, -18.05),
        (-34.41, -18.23), (-34.37, -16.93)]
H = 15.2  # to cornice
PL = 0.9  # granite plinth
BASE = 5.0  # rusticated stone storey

# ---------------------------------------------------------------- main mass
B.prism(POLY, 0, H, BRICK)
B.prism(POLY, 0, PL, GRANITE)
B.prism(POLY, H, H + 0.3, STONE)
pl = POLY if _area(POLY) > 0 else list(reversed(POLY))
n = len(pl)
ARC = set(range(23, 33))  # indices in original order of the rounded corner polyline (23..33)


def ccw_idx(i):
    return i


def edges():
    for i in range(n):
        a, b = pl[i], pl[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 0.2:
            continue
        yield a, b, (dy / L, -dx / L), (dx / L, dy / L), L


def arc_edge(a, b):
    # edges that lie on the rounded corner region (x > 33.5 and y in -17..-2.5)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return mx > 33.4 and -17.2 < my < -2.4 and not (my < -16.6 and mx < 34.5 and abs(a[1] - b[1]) < 0.3 and (b[0] - a[0]) != 0 and abs(b[0] - a[0]) > 2)


for a, b, nrm, tan, L in edges():
    ang = math.atan2(tan[1], tan[0])
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    arc = arc_edge(a, b)
    front = nrm[1] < -0.85 and L > 2.0 and not arc
    ox, oy = nrm[0], nrm[1]
    if L < 0.9:
        continue
    # rusticated stone base + string course: on front edges and corner arc, and on the long Acre Lane diagonal
    stoneface = front or arc or (L > 12 and nrm[0] > 0.5 and nrm[1] > 0.2)
    if stoneface:
        B.box(mx + ox * 0.14, my + oy * 0.14, PL, L, 0.3, BASE - PL, STONE, rot=ang)
        # rustication grooves: dark thin horizontal strips
        k = 0
        z = PL + 0.55
        while z < BASE - 0.1:
            B.box(mx + ox * 0.3, my + oy * 0.3, z, L, 0.06, 0.05, STONE_D, rot=ang)
            z += 0.6
        # string cornice at first floor sill, entablature
        B.box(mx + ox * 0.3, my + oy * 0.3, BASE, L, 0.5, 0.35, STONE, rot=ang)
    if arc:
        # full-height stone on the curved bay
        B.box(mx + ox * 0.1, my + oy * 0.1, BASE, L, 0.25, H - BASE, STONE, rot=ang)
    # heavy modillion cornice + balustrade parapet everywhere
    B.box(mx + ox * 0.55, my + oy * 0.55, H - 0.25, L, 1.1, 0.5, STONE, rot=ang)
    B.box(mx + ox * 0.25, my + oy * 0.25, H + 0.3, L, 0.5, 1.0, STONE, rot=ang)
    B.box(mx + ox * 0.3, my + oy * 0.3, H + 1.25, L, 0.6, 0.18, STONE, rot=ang)
    # balustrade as dark recessed openings
    if L > 2:
        kk = max(1, int(L / 1.6))
        for j in range(kk):
            u = -L / 2 + (j + 0.5) * L / kk
            B.box(mx + tan[0] * u + ox * 0.55, my + tan[1] * u + oy * 0.55, H + 0.4, 0.5, 0.06, 0.8, STONE_D, rot=ang)
    if L < 3.0:
        continue
    # windows
    spacing = 4.2 if (front or arc) else 4.8
    k = max(1, int(round(L / spacing)))
    step = L / k
    for j in range(k):
        u = -L / 2 + (j + 0.5) * step
        cx, cy = mx + tan[0] * u + ox * 0.05, my + tan[1] * u + oy * 0.05
        B.push(ang, cx, cy)
        # ground floor: round-headed (stone face) / plain
        w0 = 1.5
        B.arch_prism(-w0 / 2 - 0.2, w0 / 2 + 0.2, 0.12 if stoneface else 0.0, 1.2, 3.4, 0.1, STONE_D if stoneface else STONE)
        B.arch_prism(-w0 / 2, w0 / 2, 0.0, 1.3, 3.4, 0.12 if not stoneface else 0.2, WIN)
        # first floor tall windows (stone surround), oculi above
        w1 = 1.7
        B.box(0, 0.12, 5.5, w1 + 0.6, 0.1, 4.3, STONE)
        B.box(0, 0.0, 5.7, w1, 0.12, 3.5, WIN)
        B.box(0, 0.16, 5.55, w1 + 0.9, 0.2, 0.25, STONE)  # sill
        B.box(0, 0.18, 9.35, w1 + 0.5, 0.3, 0.3, STONE)  # head
        # oculus
        B.sphere(0, 0.06, 9.05, 0.28, WIN, 8, 5) if False else None
        # second floor
        B.box(0, 0.1, 10.9, w1 + 0.3, 0.08, 2.5, STONE)
        B.box(0, 0.0, 11.05, w1 - 0.2, 0.12, 2.1, WIN)
        # attic windows (small), under cornice
        B.box(0, 0.0, 13.2, 1.1, 0.12, 1.1, WIN)
        B.pop()
    # stone quoins at wall ends on brick edges
    if not stoneface:
        z = PL
        while z < H - 0.3:
            for sgn in (-1, 1):
                B.box(mx + tan[0] * sgn * (L / 2 - 0.4) + ox * 0.08, my + tan[1] * sgn * (L / 2 - 0.4) + oy * 0.08, z, 0.8, 0.16, 0.5, STONE, rot=ang)
            z += 1.0
    if not stoneface:
        # stone string courses, banded window heads with keystones, pilasters, service doors (rear/side elevations)
        for zc in (BASE - 0.1, 10.2, H - 1.0):
            B.box(mx + ox * 0.1, my + oy * 0.1, zc, L, 0.22, 0.25, STONE, rot=ang)
        for j in range(k):
            u = -L / 2 + (j + 0.5) * step
            B.push(ang, mx + tan[0] * u + ox * 0.1, my + tan[1] * u + oy * 0.1)
            B.box(0, 0.1, 9.35, 2.5, 0.18, 0.3, STONE)       # first-floor flat arch head
            B.box(0, 0.14, 9.5, 0.45, 0.18, 0.7, STONE_D)     # keystone
            B.box(0, 0.1, 13.4, 1.6, 0.16, 0.25, STONE)       # attic head
            B.box(0, 0.12, 2.9, 2.0, 0.14, 0.25, STONE)       # ground arch springing band
            B.pop()
        for j in range(1, k):
            u = -L / 2 + j * step
            B.box(mx + tan[0] * u + ox * 0.12, my + tan[1] * u + oy * 0.12, PL, 0.6, 0.28, H - PL - 0.3, STONE, rot=ang)
        if (nrm[1] > 0.3 or nrm[0] < -0.5) and L > 9:
            for uu in (-L * 0.28, L * 0.28):
                B.push(ang, mx + tan[0] * uu + ox * 0.15, my + tan[1] * uu + oy * 0.15)
                B.box(0, 0.0, 0.0, 2.6, 0.5, 3.4, DARK)
                B.box(0, 0.0, 0.0, 3.2, 0.3, 3.9, STONE)   # surround
                B.box(0, 0.0, 0.0, 2.2, 0.62, 2.9, DOOR)   # lit service door
                B.box(0, 0.7, 3.5, 3.4, 1.0, 0.2, STONE_D)  # canopy
                B.pop()
    # Ionic columns between first-floor windows on front/arc
    if front or arc:
        for j in range(k + 1):
            u = -L / 2 + j * step
            if j == 0:
                u = -L / 2 + 0.35
            if j == k:
                u = L / 2 - 0.35
            B.box(mx + tan[0] * u + ox * 0.22, my + tan[1] * u + oy * 0.22, BASE + 0.4, 0.5, 0.45, 5.2, STONE, rot=ang)
            B.box(mx + tan[0] * u + ox * 0.22, my + tan[1] * u + oy * 0.22, BASE + 5.6, 0.7, 0.55, 0.3, STONE, rot=ang)

# curved-bay central doorway, coat of arms (face direction ~ +X/-Y bisector at (39.8,-10.2) -> outward +X)
B.box(40.3, -10.4, 0, 1.2, 3.6, 5.2, STONE)  # entrance surround block
B.push(math.pi / 2, 40.95, -10.4)  # facing +X
B.arch_prism(-1.3, 1.3, 0, 0.0, 3.2, 0.1, DOOR)
B.box(-1.9, 0.2, 0, 0.5, 0.5, 4.2, STONE)
B.box(1.9, 0.2, 0, 0.5, 0.5, 4.2, STONE)
B.box(0, 0.2, 4.2, 4.8, 0.7, 0.5, STONE)
B.pop()

# ---------------------------------------------------------------- clock tower
TX, TY, TW = 30.6, -9.6, 7.6
TR = math.radians(0)
B.push(TR, TX, TY)
h1 = 24.0
B.box(0, 0, H - 0.1, TW, TW, h1 - H + 0.1, BRICK)
# stone quoins on 4 corners (alternating long/short)
z = H
i = 0
while z < h1 - 0.2:
    for sx in (-1, 1):
        for sy in (-1, 1):
            w = 1.1 if i % 2 == 0 else 0.7
            B.box(sx * (TW / 2 - w / 2 + 0.05), sy * (TW / 2 + 0.02), z, w, 0.28, 0.7, STONE)
            B.box(sx * (TW / 2 + 0.02), sy * (TW / 2 - w / 2 + 0.05), z, 0.28, w, 0.7, STONE)
    z += 0.7
    i += 1
# tall slit windows (lit) on 4 faces, 2 tiers
for face in range(4):
    a = face * math.pi / 2
    B.push(a, 0, 0)
    for zz, hh in ((17.5, 2.6), (21.0, 2.2)):
        B.box(0, -TW / 2 - 0.05, zz, 1.5, 0.15, hh, STONE)
        B.box(0, -TW / 2 - 0.12, zz + 0.15, 0.9, 0.1, hh - 0.3, WIN)
    B.pop()
# clock-stage bracketed cornice at the base of clock stage
B.box(0, 0, h1, TW + 1.4, TW + 1.4, 0.5, STONE)
for sx in range(-3, 4):
    for sy in (-1, 1):
        B.box(sx * 1.05, sy * (TW / 2 + 0.55), h1 - 0.3, 0.5, 0.5, 0.45, STONE)
        B.box(sy * (TW / 2 + 0.55), sx * 1.05, h1 - 0.3, 0.5, 0.5, 0.45, STONE)
# clock stage 24.5 .. 33
c0, c1 = h1 + 0.5, 33.0
B.box(0, 0, c0, TW - 0.4, TW - 0.4, c1 - c0, STONE)
# corner pedestals + sculpted figures
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = sx * (TW / 2 - 0.2), sy * (TW / 2 - 0.2)
        B.box(px, py, c0, 1.3, 1.3, 1.2, STONE_D)
        B.box(px, py, c0 + 1.2, 0.8, 0.8, 1.3, STONE)  # body
        B.sphere(px, py, c0 + 2.75, 0.28, STONE, 8, 5)  # head
        B.box(px + sx * 0.3, py + sy * 0.3, c0 + 1.2, 0.3, 0.3, 1.1, STONE_D)  # drape
# clock faces on 4 sides
CR = 1.95
CZ = (c0 + c1) / 2 + 0.2


def disc(c, ux, uy, r, m, segs=28, z_off=0.0):
    pts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        pts.append((c[0] + (ux[0] * math.cos(a) + uy[0] * math.sin(a)) * r,
                    c[1] + (ux[1] * math.cos(a) + uy[1] * math.sin(a)) * r,
                    c[2] + (ux[2] * math.cos(a) + uy[2] * math.sin(a)) * r))
    return pts


for face in range(4):
    a = face * math.pi / 2
    B.push(a, 0, 0)
    # local: face normal toward -Y
    y0 = -(TW / 2 - 0.2)
    # surround block + open pediment above
    B.box(0, y0 - 0.05, CZ - 2.5, 5.0, 0.35, 5.0, STONE_D)
    B.box(0, y0 - 0.2, CZ - 2.7, 5.4, 0.2, 0.25, STONE)
    # clock dial: disc built as thin cylinder facing -Y -> use frustum rotated: build polygon manually
    ring = [(math.cos(2 * math.pi * i / 28) * 2.05, y0 - 0.3, CZ + math.sin(2 * math.pi * i / 28) * 2.05) for i in range(28)]
    B.face(ring, GOLD)
    dial = [(math.cos(2 * math.pi * i / 28) * CR, y0 - 0.34, CZ + math.sin(2 * math.pi * i / 28) * CR) for i in range(28)]
    B.face(dial, CLOCK)
    # numerals / ticks
    for hr in range(12):
        t = 2 * math.pi * hr / 12
        r = CR * 0.82
        B.obox((math.cos(t) * r, y0 - 0.42, CZ + math.sin(t) * r), (math.cos(t), 0, math.sin(t)), (0, 1, 0),
               (-math.sin(t), 0, math.cos(t)), 0.34 if hr % 3 == 0 else 0.2, 0.06, 0.12 if hr % 3 else 0.17, DARK)
    # hands (10:10)
    for (ang_h, ln, wd) in ((math.radians(120), CR * 0.7, 0.14), (math.radians(60), CR * 0.5, 0.2)):
        c = (math.cos(ang_h) * ln / 2, y0 - 0.46, CZ + math.sin(ang_h) * ln / 2)
        B.obox(c, (math.cos(ang_h), 0, math.sin(ang_h)), (0, 1, 0), (-math.sin(ang_h), 0, math.cos(ang_h)), ln, 0.06, wd, DARK)
    # open (broken) segmental pediment
    B.box(-1.5, y0 - 0.2, c1 - 1.25, 2.6, 0.5, 0.35, STONE)
    B.box(1.5, y0 - 0.2, c1 - 1.25, 2.6, 0.5, 0.35, STONE)
    B.box(-2.35, y0 - 0.2, c1 - 1.65, 0.9, 0.5, 0.4, STONE)
    B.box(2.35, y0 - 0.2, c1 - 1.65, 0.9, 0.5, 0.4, STONE)
    B.box(0, y0 - 0.1, c1 - 0.9, 1.0, 0.45, 0.9, STONE_D)  # central cartouche
    B.pop()
# heavy bracketed cornice above clock stage
B.box(0, 0, c1, TW + 1.6, TW + 1.6, 0.55, STONE)
B.box(0, 0, c1 + 0.55, TW + 1.1, TW + 1.1, 0.3, STONE_D)
for sx in range(-3, 4):
    for sy in (-1, 1):
        B.box(sx * 1.05, sy * (TW / 2 + 0.6), c1 - 0.35, 0.5, 0.5, 0.45, STONE)
        B.box(sy * (TW / 2 + 0.6), sx * 1.05, c1 - 0.35, 0.5, 0.5, 0.45, STONE)
# belfry / top stage: narrower, scrolled angle buttresses, crown finial
t0, t1 = c1 + 0.85, 38.0
BW = TW - 2.2
B.box(0, 0, t0, BW, BW, t1 - t0, STONE)
for face in range(4):
    a = face * math.pi / 2
    B.push(a, 0, 0)
    B.arch_prism(-0.9, 0.9, -BW / 2 - 0.05, t0 + 0.7, t0 + 2.2, 0.1, WIN)
    B.pop()
# scrolled buttresses (voluted console blocks) at the 4 corners
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = sx * (BW / 2), sy * (BW / 2)
        B.box(px, py, t0, 1.0, 1.0, 3.3, STONE_D)
        B.box(px + sx * 0.3, py + sy * 0.3, t0, 0.7, 0.7, 2.0, STONE)
        B.frustum(px + sx * 0.5, py + sy * 0.5, t0 + 1.9, t0 + 3.2, 0.5, 0.15, STONE, segs=8)
B.box(0, 0, t1, BW + 0.8, BW + 0.8, 0.45, STONE)
B.box(0, 0, t1 + 0.45, BW - 0.3, BW - 0.3, 0.5, STONE_D)
# crown finial on plinth up to 41 m
B.frustum(0, 0, t1 + 0.95, 39.6, 1.55, 1.0, STONE, segs=8, rot=math.pi / 8)
B.frustum(0, 0, 39.6, 40.2, 1.2, 1.2, GOLD, segs=8)
for k in range(8):  # crown points
    a = 2 * math.pi * k / 8
    B.frustum(math.cos(a) * 1.0, math.sin(a) * 1.0, 40.2, 40.9, 0.28, 0.0, GOLD, segs=4)
B.frustum(0, 0, 40.2, 41.0, 0.5, 0.05, GOLD, segs=8)
B.pop()

# ---------------------------------------------------------------- central pedimented entrance bay (projecting bump x -3.2..1.2)
CBX = -1.0
B.box(CBX, -18.1, BASE, 6.8, 1.2, 0.5, STONE)  # entablature base
for dx in (-2.4, -0.8, 0.8, 2.4):  # four Ionic columns, full upper order
    B.box(CBX + dx, -18.3, BASE + 0.4, 0.75, 0.75, 6.2, STONE)
    B.box(CBX + dx, -18.3, BASE + 6.6, 1.0, 0.95, 0.35, STONE_D)
B.box(CBX, -18.1, BASE + 6.9, 7.2, 1.5, 1.2, STONE)            # entablature
B.box(CBX, -18.1, BASE + 8.1, 7.6, 1.8, 0.35, STONE_D)           # cornice
# broken pediment above parapet line
B.vprism([(CBX - 3.8, H - 0.7), (CBX + 3.8, H - 0.7), (CBX, H + 2.4)], -18.6, 0.8, STONE)
B.vprism([(CBX - 2.6, H - 0.2), (CBX + 2.6, H - 0.2), (CBX, H + 1.6)], -18.75, 0.1, STONE_D)
B.box(CBX, -18.9, H - 0.1, 1.0, 0.2, 0.9, GOLD)  # cartouche / arms
# lit entrance door + windows
B.push(0, CBX, -17.6)
B.arch_prism(-1.4, 1.4, -0.7, 0.0, 3.5, 0.2, DOOR)
B.box(0, -0.7, 4.6, 3.6, 0.15, 0.8, WIN)
B.pop()
for dx in (-2.4, 2.4):
    B.box(CBX + dx * 1.25, -18.0, 1.2, 0.9, 0.3, 3.0, WIN)

# ---------------------------------------------------------------- pitched slate roofs (mansard-hip ring + lead flat) + dormers + pavilions + chimneys
def simplify(poly, minlen=1.7):
    pts = list(poly)
    changed = True
    while changed and len(pts) > 5:
        changed = False
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if math.hypot(b[0] - a[0], b[1] - a[1]) < minlen:
                pts[i] = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                pts.pop((i + 1) % len(pts))
                changed = True
                break
    return pts


def offset_in(poly, d):
    n_ = len(poly)
    lines = []
    for i in range(n_):
        a, b = poly[i], poly[(i + 1) % n_]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L_ = math.hypot(dx, dy)
        ux, uy = dx / L_, dy / L_
        lines.append(((a[0] - uy * d, a[1] + ux * d), (ux, uy)))
    out = []
    for i in range(n_):
        (p0, d0), (p1, d1) = lines[i - 1], lines[i]
        den = d0[0] * d1[1] - d0[1] * d1[0]
        if abs(den) < 1e-6:
            out.append(p1)
            continue
        t = ((p1[0] - p0[0]) * d1[1] - (p1[1] - p0[1]) * d1[0]) / den
        q = (p0[0] + d0[0] * t, p0[1] + d0[1] * t)
        v = poly[i]
        dist = math.hypot(q[0] - v[0], q[1] - v[1])
        lim = 2.2 * d
        if dist > lim:
            q = (v[0] + (q[0] - v[0]) * lim / dist, v[1] + (q[1] - v[1]) * lim / dist)
        out.append(q)
    return out


def pip(x, y, poly):
    c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


LEAD = mat('Lead', hexc('#5b6468'), 0.6, 0.3)
Z0R = H + 0.8
RISE = 3.6
DR = 3.8
outer = simplify(pl)
inner = offset_in(outer, DR)
no = len(outer)
for i in range(no):
    o0, o1 = outer[i], outer[(i + 1) % no]
    i0, i1 = inner[i], inner[(i + 1) % no]
    B.face([(o0[0], o0[1], Z0R), (o1[0], o1[1], Z0R), (i1[0], i1[1], Z0R + RISE), (i0[0], i0[1], Z0R + RISE)], SLATE)
    # slate courses (thin lines) for texture
    for f in (0.33, 0.66):
        a0 = (o0[0] + (i0[0] - o0[0]) * f, o0[1] + (i0[1] - o0[1]) * f, Z0R + RISE * f)
        a1 = (o1[0] + (i1[0] - o1[0]) * f, o1[1] + (i1[1] - o1[1]) * f, Z0R + RISE * f)
        B.face([a0, a1, (a1[0], a1[1], a1[2] + 0.05), (a0[0], a0[1], a0[2] + 0.05)], SLATE_D)
# eaves underside + base plate so no gaps
B.prism(POLY, H + 0.3, Z0R + 0.02, SLATE)
B.prism(inner, Z0R + RISE - 0.05, Z0R + RISE + 0.1, LEAD)
# ridge cresting along inner polygon edges
for i in range(no):
    a, b = inner[i], inner[(i + 1) % no]
    L_ = math.hypot(b[0] - a[0], b[1] - a[1])
    if L_ > 0.5:
        B.box((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, Z0R + RISE + 0.1, L_, 0.25, 0.3, SLATE_D, rot=math.atan2(b[1] - a[1], b[0] - a[0]))

# dormers along stone / front elevations (on the slope, 1.5 m in from the eaves)
for i in range(no):
    a, b = outer[i], outer[(i + 1) % no]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L_ = math.hypot(dx, dy)
    nx_, ny_ = dy / L_, -dx / L_
    if L_ < 6:
        continue
    if not (ny_ < -0.8 or nx_ > 0.55 or L_ > 14):
        continue
    kk = int(L_ / 6.2)
    for j in range(kk):
        u = (j + 0.5) / kk
        x = a[0] + dx * u - nx_ * 1.7
        y = a[1] + dy * u - ny_ * 1.7
        z = Z0R + 1.7 * RISE / DR
        outang = math.atan2(ny_, nx_) + math.pi / 2
        B.push(outang, x, y)
        B.box(0, 0, z - 0.2, 1.7, 1.4, 1.9, STONE)
        B.box(0, -0.72, z + 0.1, 1.1, 0.1, 1.2, WIN)
        B.box(0, -0.74, z + 1.35, 1.5, 0.12, 0.2, STONE_D)
        # small pediment + slate roof
        B.vprism([(-0.95, z + 1.7), (0.95, z + 1.7), (0, z + 2.55)], -0.78, 0.18, STONE)
        B.face([(-1.0, -0.8, z + 1.68), (0, -0.8, z + 2.58), (0, 0.8, z + 2.58), (-1.0, 0.8, z + 1.68)], SLATE)
        B.face([(1.0, 0.8, z + 1.68), (0, 0.8, z + 2.58), (0, -0.8, z + 2.58), (1.0, -0.8, z + 1.68)], SLATE)
        B.pop()

# hipped pavilion roofs (stone/brick drum + pyramid slate hip + finial)
PAV = [(-29.5, -12.8, 7.0, 6.4), (-1.0, -12.8, 7.6, 6.4), (15.5, -12.5, 7.0, 6.4), (-28.5, 3.0, 6.6, 6.6), (-14.0, 38.0, 7.0, 7.0), (8.0, 24.0, 6.6, 6.6)]
for (x, y, w, d) in PAV:
    if not pip(x, y, pl):
        continue
    z = Z0R + 2.0
    B.box(x, y, z, w, d, 2.6, STONE)
    B.box(x, y, z + 2.6, w + 0.6, d + 0.6, 0.3, STONE_D)
    for sx in (-1, 1):
        B.box(x + sx * 1.6, y - d / 2 - 0.03, z + 0.5, 1.1, 0.1, 1.6, WIN)
        B.box(x + sx * 1.6, y + d / 2 + 0.03, z + 0.5, 1.1, 0.1, 1.6, WIN)
    # pyramidal hip
    hz0, hz1 = z + 2.9, z + 2.9 + 3.8
    for (ax, ay, bx, by) in ((-1, -1, 1, -1), (1, -1, 1, 1), (1, 1, -1, 1), (-1, 1, -1, -1)):
        B.face([(x + ax * (w + 0.6) / 2, y + ay * (d + 0.6) / 2, hz0), (x + bx * (w + 0.6) / 2, y + by * (d + 0.6) / 2, hz0), (x, y, hz1)], SLATE)
    B.box(x, y, hz1 - 0.1, 0.2, 0.2, 1.4, GOLD)

# tall stone chimneys with brick bands and pots
CH = [(-30, -12), (-21, -12.6), (-9, -12.8), (4, -12.5), (24, -12), (-28, 5), (-26, 22), (-12, 34), (-2, 28), (8, 17), (22, 3), (-17, 10)]
for (x, y) in CH:
    if not pip(x, y, pl):
        continue
    B.box(x, y, Z0R, 1.9, 1.9, 5.2, STONE)
    B.box(x, y, Z0R + 2.4, 2.1, 2.1, 0.3, BRICK)
    B.box(x, y, Z0R + 3.4, 2.1, 2.1, 0.3, BRICK)
    B.box(x, y, Z0R + 5.2, 2.4, 2.4, 0.4, STONE_D)
    for dx in (-0.45, 0.45):
        B.frustum(x + dx, y, Z0R + 5.6, Z0R + 6.6, 0.32, 0.26, BRICK, segs=8)
# assembly-hall roof lantern (rear rhombus) - glazed ridge
B.box(-8, 30, Z0R + RISE, 12, 7, 1.0, LEAD, rot=math.radians(-43))
B.box(-8, 30, Z0R + RISE + 1.0, 12.4, 1.0, 0.8, WIN, rot=math.radians(-43)) if False else None

cams = [
    ('front34', (95, -80, 45), (8, 0, 14), 38),
    ('frontclose', (65, -45, 22), (28, -9, 20), 32),
    ('rear34', (-80, 90, 55), (5, 10, 14), 38),
    ('side', (0, -120, 24), (3, 0, 18), 42),
    ('top', (3, 14, 190), (3, 14, 0), 38),
]
finish(B, 'townhall', footprint=(76.2, 65.4),
       notes="Lambeth Town Hall: red-brick body 15 m with Portland stone rusticated ground floor/quoins/cornice/balustrade, stone curved corner bay at +X end with doorway, 41 m clock tower (4 lit clock faces, open pediments, corner figures, scrolled-buttress belfry, crown finial) rising behind the corner bay at (30.6,-9.6). Footprint = OSM polygon, origin = footprint centroid, long street front faces -Y.",
       cams=cams, bevel=0.025,
       skip_bevel=('Emit_Window', 'Emit_Clock', 'Emit_Door'), res=(1100, 750))
