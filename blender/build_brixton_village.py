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
GLASS = mat('Emit_RoofGlass', hexc('#cfe6ff'), 0.3, emit=hexc('#b8d8ff'), strength=1.1)
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

# ---------------------------------------------------------------- arched gabled entrances (ornate Dutch-style gable fronts)
LET = ['GRANVILLE ARCADE', 'BRIXTON VILLAGE', 'BRIXTON VILLAGE']
BOARD = mat('SignBoard', hexc('#1b1230'), 0.6)
LETC = [SIGNS[0], SIGNS[1], SIGNW, SIGNS[2], SIGNS[3], SIGNS[5]]


def gable_pts(hw=4.2, z0=0.0):
    r = [(hw, z0), (hw, z0 + 1.2), (hw - 0.7, z0 + 1.6), (hw - 1.1, z0 + 2.4), (hw - 1.7, z0 + 2.8), (hw - 2.2, z0 + 3.6),
         (1.5, z0 + 4.4)]
    arc = [(math.cos(math.pi * (1 - t / 8)) * 1.5, z0 + 4.4 + math.sin(math.pi * (1 - t / 8)) * 1.5) for t in range(1, 8)]
    right = r
    left = [(-x, z) for (x, z) in reversed(r)]
    return right + arc + left


for idx, (ex, ey, nrm, tan, ang) in enumerate(entrance_edges):
    outang = math.atan2(nrm[1], nrm[0]) + math.pi / 2
    B.push(outang, ex + nrm[0] * 0.05, ey + nrm[1] * 0.05)
    sgn_col = SIGNS[(idx * 2) % len(SIGNS)]
    B.box(0, 0.5, 0, 8.4, 1.4, H + 1.0, RENDER)
    B.vprism(gable_pts(4.2, H + 1.0), -0.2, 0.9, RENDER)
    # coping line following the gable (thin stone rim, slightly proud)
    gp = gable_pts(4.2, H + 1.0)
    for a, b in zip(gp[:-1], gp[1:]):
        dx, dz = b[0] - a[0], b[1] - a[1]
        Lg = math.hypot(dx, dz)
        if Lg < 0.05:
            continue
        ca, sa = dx / Lg, dz / Lg
        B.obox(((a[0] + b[0]) / 2, -0.3, (a[1] + b[1]) / 2), (ca, 0, sa), (0, 1, 0), (-sa, 0, ca), Lg + 0.05, 0.3, 0.28, CONC)
    # pinnacles + finial + scroll volutes
    for sx in (-1, 1):
        B.box(sx * 4.2, -0.2, H + 1.0, 0.7, 0.7, 1.4, CONC)
        B.sphere(sx * 4.2, -0.2, H + 2.7, 0.35, CONC, 8, 5)
        ring = [(sx * 3.1 + math.cos(2 * math.pi * k / 16) * 0.65, -0.34, H + 3.0 + math.sin(2 * math.pi * k / 16) * 0.65) for k in range(16)]
        B.face(ring if sx > 0 else list(reversed(ring)), CONC)
        ring2 = [(sx * 3.1 + math.cos(2 * math.pi * k / 12) * 0.3, -0.38, H + 3.0 + math.sin(2 * math.pi * k / 12) * 0.3) for k in range(12)]
        B.face(ring2 if sx > 0 else list(reversed(ring2)), sgn_col)
    B.sphere(0, -0.2, H + 1.0 + 4.4 + 1.5 + 0.35, 0.4, CONC, 8, 5)
    # medallion (lit) in the gable head
    ring = [(math.cos(2 * math.pi * k / 20) * 0.95, -0.36, H + 1.0 + 3.4 + math.sin(2 * math.pi * k / 20) * 0.95) for k in range(20)]
    B.face(ring, sgn_col)
    ring = [(math.cos(2 * math.pi * k / 20) * 0.6, -0.4, H + 1.0 + 3.4 + math.sin(2 * math.pi * k / 20) * 0.6) for k in range(20)]
    B.face(ring, SIGNW)
    # pilasters framing + capitals
    for sx in (-1, 1):
        B.box(sx * 4.05, -0.3, 0, 0.9, 0.6, H + 1.0, BRICK)
        B.box(sx * 4.05, -0.35, H + 0.8, 1.15, 0.8, 0.35, CONC)
        B.box(sx * 3.2, -0.3, 0, 0.5, 0.4, H, CONC)
    # arch with sunburst fanlight
    B.arch_prism(-2.6, 2.6, -0.3, 0.0, 4.3, 0.1, CONC)
    B.arch_prism(-2.3, 2.3, -0.4, 0.2, 4.3, 0.1, SHOP)
    for t in range(1, 8):
        th = math.pi * t / 8
        r_mid = 1.25
        B.obox((math.cos(th) * r_mid, -0.5, 4.3 + math.sin(th) * r_mid), (math.cos(th), 0, math.sin(th)), (0, 1, 0),
               (-math.sin(th), 0, math.cos(th)), 2.3, 0.05, 0.06, DARK)
    for gx in (-1.15, 0, 1.15):
        B.box(gx, -0.5, 0.3, 0.06, 0.05, 4.0, DARK)
    for gz in (1.4, 2.8):
        B.box(0, -0.5, gz, 4.6, 0.05, 0.06, DARK)
    # hand-lettered sign: dark board, bright border, one emissive colour per letter, slight baseline wobble
    B.box(0, -0.42, 7.05, 7.6, 0.3, 1.85, BOARD)
    B.box(0, -0.6, 7.1, 7.4, 0.04, 0.1, SIGNW)
    B.box(0, -0.6, 8.8, 7.4, 0.04, 0.1, SIGNW)
    txt = LET[idx % 3]
    pitch = 7.0 / len(txt)
    for ci, chx in enumerate(txt):
        if chx == ' ':
            continue
        B.text(chx, -3.5 + pitch * (ci + 0.5), -0.62, 7.95 + (0.08 if ci % 2 else -0.05), pitch / 0.82, LETC[(ci + idx) % len(LETC)], extrude=0.1)
    # small shop signs flanking
    for sx in (-1, 1):
        B.box(sx * 3.4, -0.5, 5.0, 0.8, 0.3, 2.4, SIGNS[(idx + 2 + sx) % len(SIGNS)])
    # hanging lanterns / bunting
    for lx in (-2.2, 0, 2.2):
        B.box(lx, -1.4, 4.9, 0.03, 0.03, 0.9, DARK)
        B.sphere(lx, -1.4, 4.75, 0.2, LAMP, 8, 5)
    for k in range(12):
        t = k / 11
        x = -3.9 + 7.8 * t
        z = 6.4 - 0.5 * math.sin(math.pi * t)
        col = SIGNS[(k + idx) % len(SIGNS)]
        B.face([(x - 0.18, -1.0, z), (x + 0.18, -1.0, z), (x, -1.0, z - 0.4)], col)
        B.face([(x + 0.18, -1.0, z), (x - 0.18, -1.0, z), (x, -1.0, z - 0.4)], col)
    B.pop()

# ---------------------------------------------------------------- market stalls with striped canopies along the front
STR = [(mat('StripeRed', hexc('#d4352f'), 0.8), mat('StripeWhite', hexc('#ece6d6'), 0.8)),
       (mat('StripeGreen', hexc('#2e9c4a'), 0.8), mat('StripeWhite', hexc('#ece6d6'), 0.8)),
       (mat('StripeYellow', hexc('#f0b81c'), 0.8), mat('StripeBlue', hexc('#2b5fd0'), 0.8)),
       (mat('StripeOrange', hexc('#ec6a1c'), 0.8), mat('StripeWhite', hexc('#ece6d6'), 0.8))]
WOOD = mat('Wood', hexc('#6a4a30'), 0.85)
GOODS = [mat('GoodsRed', hexc('#c9302a'), 0.8), mat('GoodsYel', hexc('#e8c020'), 0.8), mat('GoodsGrn', hexc('#3a9a40'), 0.8),
         mat('GoodsOrg', hexc('#e8761e'), 0.8), mat('GoodsPur', hexc('#7a3a8a'), 0.8)]
nst = 0
for i in range(n):
    a, b = pl[i], pl[(i + 1) % n]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    if L < 10:
        continue
    tan = (dx / L, dy / L)
    nrm = (dy / L, -dx / L)
    if nrm[1] > -0.9:
        continue
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ent_u = (0.0 if L < 30 else -L * 0.18)
    k = int((L - 3) / 3.9)
    for j in range(k):
        u = -L / 2 + 1.8 + 3.9 * j + (L - 3 - 3.9 * k) / 2
        if abs(u - ent_u) < 5.4:
            continue
        c1, c2 = STR[(j + i) % len(STR)]
        outang = math.atan2(nrm[1], nrm[0]) + math.pi / 2
        B.push(outang, mx + tan[0] * u + nrm[0] * 2.0, my + tan[1] * u + nrm[1] * 2.0)
        # table + goods + poles + striped sloping canopy (front low, back high) + scalloped valance
        B.box(0, -0.2, 0.0, 3.4, 1.3, 0.85, WOOD)
        for g in range(8):
            B.box(-1.4 + g * 0.4, -0.25 + (g % 2) * 0.25, 0.85, 0.32, 0.32, 0.22, GOODS[(g + j) % len(GOODS)])
        for (px, py) in ((-1.7, -0.9), (1.7, -0.9), (-1.7, 0.9), (1.7, 0.9)):
            B.box(px, py, 0.0, 0.06, 0.06, 2.4 if py < 0 else 2.8, WOOD)
        NS = 8
        for sidx in range(NS):
            xa, xb = -1.9 + 3.8 * sidx / NS, -1.9 + 3.8 * (sidx + 1) / NS
            m = c1 if sidx % 2 == 0 else c2
            B.face([(xa, -1.2, 2.35), (xb, -1.2, 2.35), (xb, 1.1, 2.85), (xa, 1.1, 2.85)], m)
            B.face([(xa, 1.1, 2.85), (xb, 1.1, 2.85), (xb, -1.2, 2.35), (xa, -1.2, 2.35)], m)
            B.face([(xa, -1.2, 2.35), (xb, -1.2, 2.35), (xb, -1.22, 2.05), (xa, -1.22, 2.05)], m)
        B.sphere(0, -0.8, 2.15, 0.12, LAMP, 6, 4)
        B.pop()
        nst += 1
print('STALLS', nst)

# ---------------------------------------------------------------- roof: dark metal sawtooth with glowing skylight risers
ROOFM = mat('RoofMetal', hexc('#2b2f35'), 0.55, 0.6)
SW = 6.5
RZ_LO, RZ_HI = H + 0.3, H + 2.4
y0 = -21.0
nrow = 0
while y0 < 42:
    x = -50.0
    runs = []
    cur = None
    while x < 60:
        ok = pip(x, y0 + 0.4, pl) and pip(x, y0 + SW - 0.4, pl) and dist_edge(x, y0 + 0.4, pl) > 1.2 and dist_edge(x, y0 + SW - 0.4, pl) > 1.2
        if ok:
            if cur is None:
                cur = [x, x]
            cur[1] = x
        else:
            if cur is not None:
                runs.append(cur)
                cur = None
        x += 0.5
    if cur is not None:
        runs.append(cur)
    for (xa, xb) in runs:
        if xb - xa < 3.0:
            continue
        y1 = y0 + SW
        B.face([(xa, y0, RZ_HI), (xb, y0, RZ_HI), (xb, y1, RZ_LO), (xa, y1, RZ_LO)], ROOFM)
        B.face([(xa, y0, RZ_LO), (xb, y0, RZ_LO), (xb, y0, RZ_HI), (xa, y0, RZ_HI)], GLASS)  # glowing riser faces -Y
        # gable ends
        B.face([(xa, y0, RZ_LO), (xa, y0, RZ_HI), (xa, y1, RZ_LO)], ROOFM)
        B.face([(xb, y1, RZ_LO), (xb, y0, RZ_HI), (xb, y0, RZ_LO)], ROOFM)
        # riser mullions + top flashing + gutter
        mm = int((xb - xa) / 1.6)
        for q in range(mm + 1):
            B.box(xa + (xb - xa) * q / max(mm, 1), y0 - 0.02, RZ_LO, 0.08, 0.06, RZ_HI - RZ_LO, DARK)
        B.box((xa + xb) / 2, y0 - 0.03, RZ_HI, xb - xa, 0.16, 0.12, STEEL)
        B.box((xa + xb) / 2, y1, RZ_LO - 0.05, xb - xa, 0.2, 0.2, STEEL)
        # standing seams
        for q in range(int((xb - xa) / 2.4) + 1):
            xs = xa + 1.2 + q * 2.4
            if xs < xb - 0.3:
                B.face([(xs, y0 + 0.02, RZ_HI + 0.02), (xs + 0.07, y0 + 0.02, RZ_HI + 0.02), (xs + 0.07, y1 - 0.02, RZ_LO + 0.02), (xs, y1 - 0.02, RZ_LO + 0.02)], DARK)
    y0 += SW
    nrow += 1
# perimeter flat roof strips remain as dark slab (see POLY prism)
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
