# Peckham Levels / multi-storey car park, 95a Rye Lane. Cues (Commons geograph photo + SOS Brutalism / Southwark / The Spaces text):
# 1 ~10 levels (~31 m); lower 4 levels = 1980s Sainsbury's/Peckhamplex block clad in orange-brown stock brick with pale concrete piers, window grid, lattice grilles at ground
# 2 upper 6 levels = open decks: pale concrete slab edge band + brown brick parapet + dark open slot, concrete columns, strip lights
# 3 ramps between decks, stair/lift core cladded (blue-grey) with vertical glowing slits and 'PECKHAM LEVELS' sign
# 4 rooftop: festoon lights on poles, small cafe/bar box with lit glazing (Frank's Cafe / Bold Tendencies), parapet
# 5 stepped brick parapet at roofline, stub columns for viewing platform
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
reset()
rng = random.Random(11)
OX, OY, YAW = -1.2, -2.9, -28.5
poly = to_local(FP['levels']['polygon_blender_xy'], OX, OY, YAW)
b = B().frame(OX, OY, YAW)
brick = mat('Brick', (146, 100, 62), 0.85)
brick2 = mat('Brick_Dark', (110, 74, 48), 0.9)
conc = mat('Concrete', (150, 149, 144), 0.9)
conc_d = mat('Concrete_Dark', (92, 92, 94), 0.9)
dark = mat('Opening_Dark', (14, 14, 18), 0.8)
winw = mat('Emit_Window', (255, 205, 120), 0.3, emit=(255, 190, 100), strength=3.5)
strip = mat('Emit_Strip', (255, 240, 200), 0.3, emit=(255, 240, 190), strength=4.0)
clad = mat('Cladding', (70, 96, 120), 0.45, 0.4)
clad2 = mat('Cladding_Light', (150, 175, 190), 0.5, 0.4)
sign = mat('Emit_Sign', (255, 90, 120), 0.4, emit=(255, 70, 110), strength=4.5)
steel = mat('Steel', (40, 42, 48), 0.5, 0.7)
festoon = mat('Emit_Festoon', (255, 220, 150), 0.3, emit=(255, 200, 110), strength=7.0)
wood = mat('Timber', (150, 105, 60), 0.7)
FL_LO, N_LO = 3.3, 4
FL_UP, N_UP = 3.0, 6
z_open0 = FL_LO * N_LO                       # 13.2
z_roof = z_open0 + FL_UP * N_UP              # 31.2
# ---- lower brick block
b.prism(brick, poly, 0, z_open0)
for k in range(1, N_LO + 1):   # slab bands
    pass
# slabs/decks of upper levels
for k in range(N_UP):
    z = z_open0 + k * FL_UP
    b.prism(conc, poly, z, z + 0.35, top=True, bottom=True)
# perimeter wall faces (edge detail)
for p, u, n, L in edges(poly):
    # lower block: piers + windows
    nb = max(1, int(L // 3.0)); bw = L / nb
    for i in range(nb + 1):
        x = p[0] + u[0] * bw * i; y = p[1] + u[1] * bw * i
        b.box(conc, x - 0.3 + 0, x + 0.3, y - 0.25, y + 0.25, 0, z_open0) if False else None
    for i in range(nb):
        s0 = bw * i
        base = (p[0] + u[0] * s0, p[1] + u[1] * s0)
        # pier (vertical concrete fin) — rotated box via beam in local coords
        pa = (base[0] + n[0] * 0.15, base[1] + n[1] * 0.15, 0.0); pb = (pa[0], pa[1], z_open0)
        b.beam(conc, (pa[0], pa[1], 0.0), (pa[0], pa[1], z_open0 + 0.4), w=0.55, h=0.55) if False else None
        # (simple pier as a thin wall rectangle)
        b.wrect(conc, (base[0], base[1], 0.0), u, n, 0.5, z_open0, off=0.08)
        # ground: grille opening
        b.wrect(dark, (base[0] + u[0] * 0.8, base[1] + u[1] * 0.8, 0.2), u, n, bw - 1.6, 2.7, off=0.06)
        # floors 1..3 windows
        for fl in range(1, N_LO):
            z = fl * FL_LO + 0.9
            m = winw if rng.random() < 0.38 else dark
            b.wrect(m, (base[0] + u[0] * 0.8, base[1] + u[1] * 0.8, z), u, n, bw - 1.6, 1.6, off=0.06)
        # string band at top of each lower floor
        for fl in range(1, N_LO + 1):
            b.wrect(conc, (base[0], base[1], fl * FL_LO - 0.35), u, n, bw, 0.35, off=0.1)
    # upper open decks: parapet (brick) + slab-edge band; openings dark inside
    for k in range(N_UP):
        z = z_open0 + k * FL_UP
        b.wrect(conc, (p[0], p[1], z - 0.45 if k else z_open0 - 0.45), u, n, L, 0.8, off=0.12)       # slab edge
        b.wrect(brick2, (p[0], p[1], z + 0.35), u, n, L, 1.05, off=0.1)                              # brick parapet
        nc = max(1, int(L // 6.0)); cw = L / nc
        for i in range(nc + 1):
            px_, py_ = p[0] + u[0] * cw * i - n[0] * 0.3, p[1] + u[1] * cw * i - n[1] * 0.3
            b.box(conc, px_ - 0.25, px_ + 0.25, py_ - 0.25, py_ + 0.25, z + 0.35, z + FL_UP)
# parapet walls (thin boxes) are represented by wrect only; add roof parapet solid
for p, u, n, L in edges(poly):
    a = (p[0], p[1]); q = (p[0] + u[0] * L, p[1] + u[1] * L)
    b.beam(brick2, (a[0] + n[0] * -0.2, a[1] + n[1] * -0.2, z_roof + 0.6), (q[0] + n[0] * -0.2, q[1] + n[1] * -0.2, z_roof + 0.6), w=0.4, h=1.2)
# ---- columns + ceilings + lights for open decks
cs = 6.0
xs = [i * cs for i in range(-4, 5)]; ys = [j * cs for j in range(-3, 4)]
for k in range(N_UP):
    z = z_open0 + k * FL_UP
    for x in xs:
        for y in ys:
            if inside(poly, x, y, 1.0):
                b.box(conc, x - 0.25, x + 0.25, y - 0.25, y + 0.25, z + 0.35, z + FL_UP)
    # strip lights under next slab
    zc = z + FL_UP - 0.02
    for x in xs[::2]:
        for y in (-7.0, 7.0):
            if inside(poly, x, y, 3.0):
                b.quad(strip, (x - 0.1, y - 5, zc), (x - 0.1, y + 5, zc), (x + 0.1, y + 5, zc), (x + 0.1, y - 5, zc))
# ramps (sloped slab) between open levels, at alternating sides
for k in range(N_UP - 1):
    z = z_open0 + k * FL_UP + 0.35
    sgn = 1 if k % 2 == 0 else -1
    xa, xb = (-18, 6) if sgn > 0 else (6, -18)
    b.beam(conc_d, (xa, -9 * sgn * 0 + 4.5, z), (xb, 4.5, z + FL_UP), w=5.0, h=0.35)
# ---- roof extras
zr = z_roof + 0.35
b.prism(conc, poly, z_roof, zr, bottom=False)
# stair / lift core at the front corner (min local y vertex) 
vy = min(poly, key=lambda p: p[1] * 1.0 + 0.0)
cx, cy = vy[0] + 0.0, vy[1]
# move inward toward centroid
gx = sum(p[0] for p in poly) / len(poly); gy = sum(p[1] for p in poly) / len(poly)
d = math.hypot(gx - cx, gy - cy); cx += (gx - cx) / d * 5.5; cy += (gy - cy) / d * 5.5
core_h = z_roof + 4.5
cf = Frame(0, 0, 0)
b.box(clad, cx - 3.2, cx + 3.2, cy - 3.2, cy + 3.2, 0, core_h)
for k in range(8):        # vertical glowing stair slits on front (-Y) and side
    b.wrect(winw, (cx - 2.7 + k * 0.7, cy - 3.2, 1.0), (1, 0), (0, -1), 0.28, core_h - 3.0, off=0.05)
for k in range(6):
    b.wrect(winw, (cx + 3.2, cy - 2.5 + k * 0.9, 1.0), (0, 1), (1, 0), 0.28, core_h - 3.0, off=0.05)
b.box(clad2, cx - 3.4, cx + 3.4, cy - 3.4, cy + 3.4, core_h, core_h + 0.4)
for k in range(1, N_LO + N_UP):
    b.wrect(clad2, (cx - 3.2, cy - 3.2, k * 3.1), (1, 0), (0, -1), 6.4, 0.25, off=0.1)
# rooftop cafe / bar
bx, by = gx - 4, gy + 1
b.box(wood, bx - 5, bx + 5, by - 2.5, by + 2.5, zr, zr + 3.2)
b.wrect(winw, (bx - 4.5, by - 2.5, zr + 0.5), (1, 0), (0, -1), 9.0, 2.0, off=0.05)
b.box(steel, bx - 5.4, bx + 5.4, by - 3.2, by + 2.5, zr + 3.2, zr + 3.45)
# festoon poles + lines
poles = []
for x in (-20, -10, 0, 10, 20):
    for y in (-12, 12):
        if inside(poly, x, y, 2.0): poles.append((x, y))
for (x, y) in poles:
    b.beam(steel, (x, y, zr), (x, y, zr + 3.8), w=0.12, n=5)
def line(p0, p1):
    n = 7
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
        z = zr + 3.8 - 0.7 * math.sin(math.pi * t)
        b.box(festoon, x - 0.1, x + 0.1, y - 0.1, y + 0.1, z - 0.2, z)
        
pp = set(poles)
for (x, y) in poles:
    if (x + 10, y) in pp: line((x, y), (x + 10, y))
    if (x, 12) in pp and (x, -12) in pp and y == -12: line((x, -12), (x, 12))
# low planter / seating blocks
for (x, y) in ((-15, 0), (12, -2), (16, 6)):
    if inside(poly, x, y, 3): b.box(conc_d, x - 1.5, x + 1.5, y - 1.0, y + 1.0, zr, zr + 0.8)
objs = b.build('levels')
t = text_mesh('PECKHAM LEVELS', 1.0, sign, Frame(OX, OY, YAW).p(cx, cy - 3.3, z_roof - 1.5), rot=(math.radians(90), 0, math.radians(YAW)), extrude=0.15, name='levels_sign')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
export('levels', 'Peckham multi-storey car park / Peckham Levels: 4 brick-clad lower levels + 6 open concrete/brick-parapet decks (~31 m), ramps, '
       'clad stair core with PECKHAM LEVELS sign, rooftop festoon lights + bar. Rotated -28.5 deg to match OSM footprint.')
shoot = setup_preview('levels', (0, 0), 85, z_roof)
for nm, az, dm, el in (('front34', -35, 1.0, 0.5), ('rear34', 145, 1.0, 0.5), ('side', 90, 0.95, 0.2), ('top', -25, 0.9, 1.2)):
    shoot(nm, az, dm, el)
