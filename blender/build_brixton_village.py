"""Brixton Village / Granville Arcade covered market (1937, Burr & Burr). Run: blender -b --python build_brixton_village.py
Cues (Historic England 1393881 / Wikipedia / Brixton Buzz / photos):
 1 one long roofed block (OSM polygon) ~8 m to parapet: double-height covered 'avenues' inside, lit from roof windows
 2 arched, gabled glazed ENTRANCES (cream pilasters, stepped gable, big arched glass) with big colourful illuminated signs
 3 perimeter of small SHOPFRONTS 3.2 m bays: glowing glass, brightly coloured fascia boards, hand-painted signs
 4 upper row of lit windows (flats/offices) under a plain parapet, painted render in warm cream / brick
 5 glazed ridge lanterns ('ceiling windows') over the avenues, cool-lit; plant + flues on the roof
 6 string bunting + hanging lanterns at entrances, roller shutters on some bays
"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lbx_common import *

random.seed(7)
reset_scene()
B = Builder()
RENDER = mat('Render_Cream', hexc('#d8c8a4'), 0.9)
BRICK = mat('Brick', hexc('#9a6a4c'), 0.9)
PAINT = mat('PaintBand', hexc('#2f7f78'), 0.8)
ROOF = mat('Roof', hexc('#3c4046'), 0.85)
CONC = mat('Concrete', hexc('#8f8c86'), 0.9)
STEEL = mat('Steel', hexc('#4c5258'), 0.5, 0.7)
DARK = mat('Dark', hexc('#17191c'), 0.7)
SHUT = mat('Shutter', hexc('#6a6e73'), 0.6, 0.5)
WIN = mat('Emit_Window', hexc('#ffc77a'), 0.4, emit=hexc('#ffb050'), strength=4.5)
SHOP = mat('Emit_Shop', hexc('#ffd9a0'), 0.4, emit=hexc('#ffc27a'), strength=4.0)
GLASS = mat('Emit_RoofGlass', hexc('#cfe6ff'), 0.3, emit=hexc('#b8d8ff'), strength=2.0)
LAMP = mat('Emit_Lamp', hexc('#ffe9a8'), 0.4, emit=hexc('#ffd878'), strength=8.0)
COLS = [('Emit_SignPink', '#ff2e7a'), ('Emit_SignYellow', '#ffc400'), ('Emit_SignTeal', '#12c2b6'),
        ('Emit_SignPurple', '#9a4cff'), ('Emit_SignGreen', '#3fd04f'), ('Emit_SignOrange', '#ff6a1f'),
        ('Emit_SignBlue', '#2f7bff'), ('Emit_SignRed', '#ff2a2a')]
SIGNS = [mat(n, hexc(c), 0.5, emit=hexc(c), strength=3.5) for n, c in COLS]
SIGNW = mat('Emit_SignWhite', hexc('#fff3d8'), 0.4, emit=hexc('#fff0cf'), strength=6.0)

POLY = [(14.06, -9.86), (13.76, -11.56), (-9.43, -11.43), (-9.68, -20.48), (-23.26, -20.89), (-23.58, -11.55),
        (-46.93, -12.84), (-46.68, -10.08), (-40.19, -4.99), (-37.81, -1.42), (-34.34, -0.68), (-32.86, 5.25),
        (-22.04, 5.33), (-5.64, 41.21), (44.74, 19.41), (48.89, 17.31), (48.52, 16.4), (57.11, 12.62),
        (55.73, 9.59), (49.62, -11.34)]
H = 8.0  # parapet / eaves
FIRST = 4.6  # first-floor level (upper windows)

pl = ccw(POLY)
n = len(pl)
B.prism(POLY, 0, H, RENDER)
B.prism(POLY, 0, 0.5, CONC)
B.prism(POLY, H, H + 0.25, ROOF)

ENTR = []  # (mx,my,nx,ny,tx,ty)


def pip(x, y, poly):
    c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def dist_edge(x, y, poly):
    best = 1e9
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / L2))
        d = math.hypot(x - (x0 + t * dx), y - (y0 + t * dy))
        best = min(best, d)
    return best


# ---------------------------------------------------------------- perimeter walls
entrance_edges = []
for i in range(n):
    a, b = pl[i], pl[(i + 1) % n]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 0.4:
        continue
    tan = (dx / L, dy / L)
    nrm = (dy / L, -dx / L)
    ang = math.atan2(dy, dx)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    # parapet cornice
    B.box(mx + nrm[0] * 0.25, my + nrm[1] * 0.25, H - 0.35, L, 0.7, 0.4, CONC, rot=ang)
    B.box(mx + nrm[0] * 0.05, my + nrm[1] * 0.05, H - 0.3, L, 0.2, 0.0001 + 0.3, PAINT, rot=ang) if False else None
    B.box(mx + nrm[0] * 0.08, my + nrm[1] * 0.08, FIRST - 0.35, L, 0.2, 0.3, PAINT, rot=ang)  # painted band
    if L < 3.4:
        continue
    # entrance on the long front-ish edges (facing -Y), centred
    is_front = nrm[1] < -0.9 and L > 20
    ent_u = None
    if is_front:
        ent_u = 0.0 if L < 30 else -L * 0.18
        entrance_edges.append((mx + tan[0] * ent_u, my + tan[1] * ent_u, nrm, tan, ang))
    k = max(1, int(round(L / 3.2)))
    step = L / k
    for j in range(k):
        u = -L / 2 + (j + 0.5) * step
        if ent_u is not None and abs(u - ent_u) < 4.6:
            continue
        cx, cy = mx + tan[0] * u + nrm[0] * 0.04, my + tan[1] * u + nrm[1] * 0.04
        B.push(ang + math.pi, cx, cy)  # local -Y faces outward? rotate by ang+pi: local -Y -> (sin(ang+pi), -cos(ang+pi))
        B.pop()
        outang = math.atan2(nrm[1], nrm[0]) + math.pi / 2  # local -Y after rotation -> outward normal
        B.push(outang, cx, cy)
        w = step - 0.5
        # pilaster
        B.box(step / 2, 0.15, 0.0, 0.45, 0.35, H - 0.4, BRICK)
        kind = random.random()
        col = random.choice(SIGNS)
        # shopfront: glowing glass + coloured fascia + stall board
        if kind < 0.18:  # roller shutter closed, lit sign above
            B.box(0, -0.06, 0.3, w - 0.2, 0.12, 2.9, SHUT)
            for z in range(0, 14):
                B.box(0, -0.13, 0.35 + z * 0.2, w - 0.25, 0.04, 0.05, DARK)
        else:
            B.box(0, -0.06, 0.4, w - 0.2, 0.12, 2.8, SHOP)
            B.box(0, -0.1, 0.3, w - 0.1, 0.18, 0.18, DARK)  # stall riser
            if kind > 0.6:  # door
                B.box(w * 0.28, -0.14, 0.4, 0.9, 0.1, 2.5, DARK)
        B.box(0, -0.12, 3.15, w, 0.16, 0.75, col)  # fascia
        B.box(0, -0.2, 3.2, w - 0.5, 0.04, 0.3, SIGNW)  # painted name
        # upper windows (flats): lit warm, some dark
        if random.random() < 0.75:
            B.box(0, -0.05, FIRST + 0.5, 1.6, 0.12, 2.0, WIN)
            B.box(0, 0.0, FIRST + 0.35, 2.0, 0.08, 2.4, CONC)
        else:
            B.box(0, -0.05, FIRST + 0.5, 1.6, 0.12, 2.0, DARK)
        B.pop()

# ---------------------------------------------------------------- arched gabled entrances
LET = ['GRANVILLE ARCADE', 'BRIXTON VILLAGE', 'BRIXTON VILLAGE']
for idx, (ex, ey, nrm, tan, ang) in enumerate(entrance_edges):
    outang = math.atan2(nrm[1], nrm[0]) + math.pi / 2
    B.push(outang, ex + nrm[0] * 0.05, ey + nrm[1] * 0.05)
    # gable block (cream, rises above parapet) + stepped top
    B.box(0, 0.5, 0, 8.4, 1.4, H + 2.2, RENDER)
    B.box(0, 0.35, H + 2.2, 7.0, 1.2, 0.5, CONC)
    B.box(0, 0.3, H + 2.7, 4.4, 1.0, 0.5, CONC)
    B.box(0, 0.3, H + 3.2, 1.6, 0.9, 0.4, CONC)
    # pilasters framing
    for sx in (-1, 1):
        B.box(sx * 4.05, -0.3, 0, 0.9, 0.55, H + 2.8, BRICK)
        B.box(sx * 3.2, -0.3, 0, 0.5, 0.35, H + 1.0, CONC)
    # big arched glazed opening, lit
    B.arch_prism(-2.5, 2.5, -0.3, 0.0, 4.3, 0.1, CONC)
    B.arch_prism(-2.25, 2.25, -0.4, 0.2, 4.3, 0.1, SHOP)
    # glazing bars
    for gx in (-1.1, 0, 1.1):
        B.box(gx, -0.5, 0.3, 0.06, 0.05, 6.4, DARK)
    for gz in (2.2, 4.4):
        B.box(0, -0.5, gz, 4.6, 0.05, 0.06, DARK)
    # coloured sign board above the arch (two colours) + white letters
    B.box(0, -0.4, 7.65, 6.4, 0.3, 1.5, SIGNS[idx % len(SIGNS)])
    B.text(LET[idx % 3], 0, -0.62, 8.4, 0.62, SIGNW, extrude=0.08)
    # side shop signs
    for sx in (-1, 1):
        B.box(sx * 3.4, -0.5, 5.0, 0.8, 0.3, 2.8, SIGNS[(idx + 2 + sx) % len(SIGNS)])
    # hanging lanterns / bunting
    for lx in (-2.2, 0, 2.2):
        B.box(lx, -1.4, 4.9, 0.03, 0.03, 0.9, DARK)
        B.sphere(lx, -1.4, 4.75, 0.2, LAMP, 8, 5)
    for k in range(10):
        t = k / 9
        x = -3.5 + 7.0 * t
        z = 6.2 - 0.45 * math.sin(math.pi * t)
        col = SIGNS[(k + idx) % len(SIGNS)]
        B.face([(x - 0.18, -1.0, z), (x + 0.18, -1.0, z), (x, -1.0, z - 0.4)], col)
        B.face([(x + 0.18, -1.0, z), (x - 0.18, -1.0, z), (x, -1.0, z - 0.4)], col)
    B.pop()

# ---------------------------------------------------------------- roof: glazed ridge lanterns (the 'ceiling windows')
LAN = 0
step_x, step_y = 9.0, 7.5
y = -17.0
while y < 41:
    x = -45.0
    while x < 58:
        if pip(x, y, pl) and dist_edge(x, y, pl) > 3.0:
            for sx in (-1, 1):
                pass
            B.box(x, y, H + 0.25, 7.0, 3.0, 0.7, CONC)
            # gabled glass: two slopes
            lo, hi = H + 0.95, H + 1.95
            B.face([(x - 3.3, y - 1.3, lo), (x + 3.3, y - 1.3, lo), (x + 3.3, y, hi), (x - 3.3, y, hi)], GLASS)
            B.face([(x - 3.3, y + 1.3, lo), (x - 3.3, y, hi), (x + 3.3, y, hi), (x + 3.3, y + 1.3, lo)], GLASS)
            B.face([(x - 3.3, y - 1.3, lo), (x - 3.3, y, hi), (x - 3.3, y + 1.3, lo)], GLASS)
            B.face([(x + 3.3, y + 1.3, lo), (x + 3.3, y, hi), (x + 3.3, y - 1.3, lo)], GLASS)
            B.box(x, y, H + 1.95, 6.8, 0.1, 0.12, STEEL)
            LAN += 1
        x += step_x
    y += step_y
    if int(y) % 2:
        pass
# plant/flues
random.seed(3)
for k in range(10):
    for _ in range(40):
        x, y = random.uniform(-45, 55), random.uniform(-10, 40)
        if pip(x, y, pl) and dist_edge(x, y, pl) > 4:
            B.box(x, y, H + 0.25, 1.2, 1.2, random.uniform(1.4, 2.6), BRICK)
            B.box(x, y, H + 2.9, 1.5, 1.5, 0.2, CONC)
            break

cams = [
    ('front34', (-70, -85, 45), (5, 8, 5), 38),
    ('frontclose', (-5, -45, 12), (0, -11, 5), 34),
    ('rear34', (40, 85, 45), (5, 10, 5), 40),
    ('side', (130, 0, 40), (5, 10, 5), 40),
    ('top', (5, 12, 160), (5, 12, 0), 40),
]
finish(B, 'brixton_village', footprint=(104.0, 62.1),
       notes="Brixton Village / Granville Arcade: OSM-footprint market block 8 m to parapet, ~125 lit 3.2 m shopfront bays with coloured fascia boards, 3 arched/gabled glazed entrances with big signs ('GRANVILLE ARCADE'/'BRIXTON VILLAGE', bunting), glazed ridge lanterns on the roof, plant. Origin = footprint centre, front -Y.",
       cams=cams, bevel=0.02, skip_bevel=tuple(n for n, _ in COLS) + ('Emit_Window', 'Emit_Shop', 'Emit_RoofGlass', 'Emit_Lamp', 'Emit_SignWhite'),
       res=(1100, 750))
