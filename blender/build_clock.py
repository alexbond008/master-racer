# Jones & Higgins store + Jarvis clock tower (Rye Lane / Peckham High St corner). Cues (Commons geograph 1741847, 'Jones and Higgins (8667814865)'; Victorian Society; Southwark News):
# 1 four-storey Venetian-Renaissance store, grey/cream stone (NOT red - photos show pale grey-cream stone, with red brick only on neighbours/back walls)
# 2 rusticated dark-fronted ground floor with big lit shop windows and a cream fascia sign; strong stone string courses between floors
# 3 upper floors: paired round-arched windows with moulded surrounds + pilasters, wide bracketed cornice and parapet
# R2: tower now follows St Mark's Square Torre dell'Orologio: blue+gold dial in arched recess, balustraded terrace, arched belfry, cornice w/ obelisks, dome+finial
# 4 (R1) slim square clock tower rising from the centre of the front roofline: balustraded balcony, clock face (emissive) on 3 faces, cornice, small hipped cap + weathervane
# 5 plan = wedge-shaped corner site (OSM: 13 x 29 m); front (High St) faces -Y, long Rye Lane side faces -X
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
reset()
rng = random.Random(21)
b = B()
stone = mat('Stone', (188, 182, 168), 0.85)
stone_d = mat('Stone_Dark', (140, 134, 124), 0.9)
cream = mat('Cream', (222, 212, 186), 0.8)
brick = mat('Brick_Red', (150, 70, 52), 0.9)
dark = mat('Window_Dark', (16, 20, 30), 0.1, 0.4)
winw = mat('Emit_Window', (255, 205, 120), 0.3, emit=(255, 190, 100), strength=3.5)
shop = mat('Emit_Shopfront', (255, 190, 110), 0.3, emit=(255, 170, 90), strength=3.2)
shopdark = mat('Shopfront_Dark', (30, 28, 30), 0.5)
clockm = mat('Emit_Clock', (255, 250, 230), 0.4, emit=(255, 245, 215), strength=4.5)
hand = mat('Clock_Hands', (20, 20, 22), 0.5)
roofm = mat('Roof_Lead', (84, 92, 96), 0.5, 0.5)
signm = mat('Emit_Sign', (250, 240, 210), 0.4, emit=(255, 235, 190), strength=3.0)
steel = mat('Metal', (40, 42, 46), 0.5, 0.7)
dial = mat('Emit_Dial_Blue', (24, 52, 150), 0.4, emit=(40, 80, 220), strength=2.6)
gold = mat('Emit_Gold', (230, 180, 60), 0.3, 0.8, emit=(255, 190, 60), strength=3.2)
dome_m = mat('Dome_Copper', (96, 150, 130), 0.4, 0.5)
P = [(7.16, -8.1), (-5.77, -16.42), (-3.67, 12.18), (0.13, 12.6), (2.15, -0.26)]
cx = sum(p[0] for p in P) / 5; cy = sum(p[1] for p in P) / 5
H0, H1, H2, H3 = 4.6, 4.0, 3.8, 3.4
ZE = H0 + H1 + H2 + H3
b.prism(stone, P, 0, ZE)
b.prism(cream, [(p[0], p[1]) for p in P], ZE, ZE + 0.5, bottom=False)        # cornice cap slab (flat roof)

def facade(i, bayw, pairs=True, sign=False, lit=0.45):
    p = P[i]; q = P[(i + 1) % len(P)]
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); u = (dx / L, dy / L)
    n = (u[1], -u[0])
    if (cx - p[0]) * n[0] + (cy - p[1]) * n[1] > 0: n = (-n[0], -n[1])
    nb = max(1, round(L / bayw)); bw = L / nb
    for k in range(nb):
        bx, by = p[0] + u[0] * bw * k, p[1] + u[1] * bw * k
        # ground floor shopfront
        b.wrect(shopdark, (bx + u[0] * 0.3, by + u[1] * 0.3, 0.3), u, n, bw - 0.6, H0 - 1.2, off=0.08)
        b.wrect(shop if rng.random() < 0.85 else dark, (bx + u[0] * 0.5, by + u[1] * 0.5, 0.5), u, n, bw - 1.0, H0 - 1.9, off=0.12)
        # pilasters (rusticated strips)
        b.wrect(stone_d, (bx - u[0] * 0.15, by - u[1] * 0.15, 0), u, n, 0.5, ZE, off=0.12)
        for fl, z0, hh in ((1, H0 + 0.55, H1 - 1.2), (2, H0 + H1 + 0.5, H2 - 1.1), (3, H0 + H1 + H2 + 0.35, H3 - 1.55)):
            if pairs:
                ww = (bw - 1.5) / 2
                for j in range(2):
                    ox = 0.75 + j * (ww + 0.0) + (0.0 if j == 0 else 0.0)
                    xx = bx + u[0] * (0.7 + j * (ww + 0.1)); yy = by + u[1] * (0.7 + j * (ww + 0.1))
                    b.warch(cream, (xx, yy, z0 - 0.15), u, n, ww, hh + 0.3, rise=ww / 2, off=0.06)
                    b.warch(winw if rng.random() < lit else dark, (xx + u[0] * 0.12, yy + u[1] * 0.12, z0), u, n, ww - 0.24, hh, rise=(ww - 0.24) / 2, off=0.1)
            else:
                ww = bw - 1.4
                xx = bx + u[0] * 0.7; yy = by + u[1] * 0.7
                b.warch(cream, (xx, yy, z0 - 0.15), u, n, ww, hh + 0.3, rise=ww / 2, off=0.06)
                b.warch(winw if rng.random() < lit else dark, (xx + u[0] * 0.12, yy + u[1] * 0.12, z0), u, n, ww - 0.24, hh, rise=(ww - 0.24) / 2, off=0.1)
    # string courses + cornice
    for z, h in ((H0 - 0.45, 0.6), (H0 + H1 - 0.3, 0.45), (H0 + H1 + H2 - 0.3, 0.45)):
        b.wrect(cream, (p[0], p[1], z), u, n, L, h, off=0.16)
    b.wrect(cream, (p[0], p[1], ZE - 0.9), u, n, L, 0.9, off=0.3)          # bracketed cornice band
    nbr = int(L / 0.8)
    for k in range(nbr):
        b.wrect(stone_d, (p[0] + u[0] * (0.2 + k * 0.8), p[1] + u[1] * (0.2 + k * 0.8), ZE - 1.15), u, n, 0.3, 0.5, off=0.32)
    # balustraded parapet: rail + posts, pinnacles at bay ends
    b.wrect(cream, (p[0], p[1], ZE + 0.5), u, n, L, 0.25, off=0.05)
    b.wrect(cream, (p[0], p[1], ZE + 1.1), u, n, L, 0.2, off=0.05)
    npost = int(L / 0.4)
    for k in range(npost):
        b.wrect(stone, (p[0] + u[0] * (0.1 + k * 0.4), p[1] + u[1] * (0.1 + k * 0.4), ZE + 0.7), u, n, 0.18, 0.4, off=0.05)
    nb = max(1, round(L / bayw)); bw = L / nb
    for k in range(nb + 1):
        fx, fy = p[0] + u[0] * bw * k, p[1] + u[1] * bw * k
        b.box(cream, fx - 0.3, fx + 0.3, fy - 0.3, fy + 0.3, ZE + 0.5, ZE + 1.5)
        b.pyramid(cream, fx - 0.25, fx + 0.25, fy - 0.25, fy + 0.25, ZE + 1.5, ZE + 2.4)
    # balcony bands under 2nd-floor windows + keystone blocks over arches
    b.wrect(cream, (p[0], p[1], H0 + 0.1), u, n, L, 0.3, off=0.2)
    for k in range(nb):
        for j in range(2 if pairs else 1):
            ww = (bw - 1.5) / 2 if pairs else bw - 1.4
            xx = p[0] + u[0] * (bw * k + 0.7 + j * (ww + 0.1) + ww / 2 - 0.12) 
            yy = p[1] + u[1] * (bw * k + 0.7 + j * (ww + 0.1) + ww / 2 - 0.12)
            for z in (H0 + H1 - 0.7, H0 + H1 + H2 - 0.7):
                b.wrect(cream, (xx, yy, z), u, n, 0.24, 0.3, off=0.2)
    return p, u, n, L

fa = facade(0, 3.9, pairs=True, sign=True)        # front (High Street) facade A->B
fw = facade(1, 3.8, pairs=True)                   # long west (Rye Lane) facade B->C
fe = facade(4, 3.6, pairs=False)                  # short east return E->A
# rear walls: red brick with plain windows
for i in (2, 3):
    p = P[i]; q = P[(i + 1) % 5]
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); u = (dx / L, dy / L)
    n = (u[1], -u[0])
    if (cx - p[0]) * n[0] + (cy - p[1]) * n[1] > 0: n = (-n[0], -n[1])
    b.wrect(brick, (p[0], p[1], 0), u, n, L, ZE, off=0.04)
    for k in range(max(1, int(L // 3.2))):
        for z0 in (1.0, 5.6, 9.6, 13.4):
            b.wrect(winw if rng.random() < 0.3 else dark, (p[0] + u[0] * (0.8 + k * 3.2), p[1] + u[1] * (0.8 + k * 3.2), z0), u, n, 1.2, 1.9, off=0.06)
# fascia sign on front above shopfront
pf, uf, nf, Lf = fa
yaw = math.atan2(uf[1], uf[0])
sx = pf[0] + uf[0] * Lf * 0.5 + nf[0] * 0.35; sy = pf[1] + uf[1] * Lf * 0.5 + nf[1] * 0.35
# --- Jarvis clock tower (after St Mark's, Venice) on the roof, centred on the front facade
tcx = pf[0] + uf[0] * Lf * 0.5 - nf[0] * 1.9; tcy = pf[1] + uf[1] * Lf * 0.5 - nf[1] * 1.9
ang = math.degrees(yaw)
b.frame(tcx, tcy, ang)
tw = 3.6; h = tw / 2
z0 = ZE + 0.5
FACES = ((0, -h, 1, 0, 0, -1), (0, h, -1, 0, 0, 1), (-h, 0, 0, -1, -1, 0), (h, 0, 0, 1, 1, 0))
b.box(stone, -h - 0.5, h + 0.5, -h - 0.5, h + 0.5, z0, z0 + 0.8)                    # plinth
b.box(cream, -h - 0.65, h + 0.65, -h - 0.65, h + 0.65, z0 + 0.8, z0 + 1.0)
b.box(stone, -h, h, -h, h, z0 + 1.0, z0 + 8.0)                                       # stage 1 shaft
# corner quoins
for sx in (-1, 1):
    for sy in (-1, 1):
        for q in range(7):
            b.box(cream, sx * h - 0.2 * (1 if sx > 0 else 1) - (0.2 if sx > 0 else 0) + (0.0 if sx > 0 else 0.0), sx * h + (0.2 if sx < 0 else 0.0) , sy * h - (0.2 if sy > 0 else 0), sy * h + (0.2 if sy < 0 else 0), z0 + 1.0 + q * 1.1, z0 + 1.0 + q * 1.1 + 0.6) if False else None
cz = z0 + 4.9; cr = 1.0
def dial_face(cx_, cy_, ux, uy, nx, ny):
    def Pn(a, z, off): return (cx_ + ux * a + nx * off, cy_ + uy * a + ny * off, z)
    def disc(m, r, off, seg=20):
        pts = [Pn(r * math.cos(2 * math.pi * i / seg), cz + r * math.sin(2 * math.pi * i / seg), off) for i in range(seg)]
        e1 = Vector(pts[1]) - Vector(pts[0]); e2 = Vector(pts[2]) - Vector(pts[1])
        if e1.cross(e2).dot(Vector((nx, ny, 0))) < 0: pts = pts[::-1]
        b.poly(m, pts)
    # blue arched panel with stone surround
    b.warch(cream, (cx_ + ux * -1.5 + nx * 0.06, cy_ + uy * -1.5 + ny * 0.06, z0 + 1.6) if False else Pn(-1.5, z0 + 1.6, 0.05), (ux, uy), (nx, ny), 3.0, 5.9, rise=1.5, off=0.0)
    b.warch(dial, Pn(-1.3, z0 + 1.8, 0.08), (ux, uy), (nx, ny), 2.6, 5.6, rise=1.3, off=0.0)
    disc(gold, cr + 0.12, 0.12); disc(dial, cr, 0.14); 
    for k in range(12):                       # gold hour ticks
        a = 2 * math.pi * k / 12
        r0, r1 = cr * 0.78, cr * 0.95
        ca, sa = math.cos(a), math.sin(a)
        w = 0.05
        pts = [Pn(r0 * ca - w * sa, cz + r0 * sa + w * ca, 0.16), Pn(r1 * ca - w * sa, cz + r1 * sa + w * ca, 0.16), Pn(r1 * ca + w * sa, cz + r1 * sa - w * ca, 0.16), Pn(r0 * ca + w * sa, cz + r0 * sa - w * ca, 0.16)]
        e1 = Vector(pts[1]) - Vector(pts[0]); e2 = Vector(pts[2]) - Vector(pts[1])
        if e1.cross(e2).dot(Vector((nx, ny, 0))) < 0: pts = pts[::-1]
        b.poly(gold, pts)
    for (ax, az, bx_, bz) in ((0, 0, 0.1, 0.75), (0, 0, 0.55, -0.2)):         # hands (gold)
        pts = [Pn(ax - 0.05, cz + az, 0.18), Pn(bx_ - 0.05, cz + bz, 0.18), Pn(bx_ + 0.05, cz + bz, 0.18), Pn(ax + 0.05, cz + az, 0.18)]
        e1 = Vector(pts[1]) - Vector(pts[0]); e2 = Vector(pts[2]) - Vector(pts[1])
        if e1.cross(e2).dot(Vector((nx, ny, 0))) < 0: pts = pts[::-1]
        b.poly(gold, pts)
    rr = random.Random(int(cx_ * 7 + cy_ * 13 + 5))
    for k in range(9):                        # gold stars on blue field above and below dial
        a = rr.uniform(-0.9, 0.9); zz = rr.choice([z0 + 2.4 + rr.uniform(0, 0.5), z0 + 6.9 + rr.uniform(0, 0.6)])
        if zz > cz - 1.3 and zz < cz + 1.3: zz = z0 + 7.3
        pts = [Pn(a - 0.08, zz, 0.16), Pn(a + 0.08, zz, 0.16), Pn(a + 0.08, zz + 0.16, 0.16), Pn(a - 0.08, zz + 0.16, 0.16)]
        e1 = Vector(pts[1]) - Vector(pts[0]); e2 = Vector(pts[2]) - Vector(pts[1])
        if e1.cross(e2).dot(Vector((nx, ny, 0))) < 0: pts = pts[::-1]
        b.poly(gold, pts)
for f in FACES: dial_face(*f)
# cornice, terrace with balustrade
zc = z0 + 8.0
b.box(cream, -h - 0.6, h + 0.6, -h - 0.6, h + 0.6, zc, zc + 0.5)
b.box(stone, -h - 0.45, h + 0.45, -h - 0.45, h + 0.45, zc + 0.5, zc + 0.8)
for k in range(8):
    for (a_, b_) in ((-h - 0.35 + k * 0.5, -h - 0.35), (-h - 0.35 + k * 0.5, h + 0.2), (-h - 0.35, -h - 0.35 + k * 0.5), (h + 0.2, -h - 0.35 + k * 0.5)):
        b.box(cream, a_, a_ + 0.15, b_, b_ + 0.15, zc + 0.8, zc + 1.5)
b.box(cream, -h - 0.5, h + 0.5, -h - 0.5, -h - 0.35, zc + 1.5, zc + 1.65); b.box(cream, -h - 0.5, h + 0.5, h + 0.35, h + 0.5, zc + 1.5, zc + 1.65)
b.box(cream, -h - 0.5, -h - 0.35, -h - 0.5, h + 0.5, zc + 1.5, zc + 1.65); b.box(cream, h + 0.35, h + 0.5, -h - 0.5, h + 0.5, zc + 1.5, zc + 1.65)
# the bell + two small figures on the terrace
b.cyl(gold, 0, 0, zc + 0.8, zc + 2.0, 0.55, r1=0.3, n=10)
b.box(gold, -1.2, -0.9, -0.15, 0.15, zc + 0.8, zc + 1.9); b.box(gold, 0.9, 1.2, -0.15, 0.15, zc + 0.8, zc + 1.9)
# arched belfry stage
zb = zc + 0.8; hb = 1.35
b.box(stone, -hb, hb, -hb, hb, zb, zb + 3.4)
for (cx_, cy_, ux, uy, nx, ny) in FACES:
    sc = hb / h
    ox, oy = cx_ * sc, cy_ * sc
    b.warch(cream, (ox - ux * 0.85, oy - uy * 0.85, zb + 0.5), (ux, uy), (nx, ny), 1.7, 3.0, rise=0.85, off=0.03) if False else None
    b.warch(cream, (ox - ux * 0.75 , oy - uy * 0.75, zb + 0.5), (ux, uy), (nx, ny), 1.5, 3.0, rise=0.75, off=0.04)
    b.warch(winw, (ox - ux * 0.6, oy - uy * 0.6, zb + 0.6), (ux, uy), (nx, ny), 1.2, 2.8, rise=0.6, off=0.08)
for sx in (-1, 1):
    for sy in (-1, 1):
        b.box(cream, sx * hb - 0.2, sx * hb + 0.2, sy * hb - 0.2, sy * hb + 0.2, zb, zb + 3.4)
b.box(cream, -hb - 0.4, hb + 0.4, -hb - 0.4, hb + 0.4, zb + 3.4, zb + 3.9)
b.box(stone, -hb - 0.25, hb + 0.25, -hb - 0.25, hb + 0.25, zb + 3.9, zb + 4.2)
for sx in (-1, 1):
    for sy in (-1, 1):
        b.pyramid(cream, sx * (hb + 0.1) - 0.2, sx * (hb + 0.1) + 0.2, sy * (hb + 0.1) - 0.2, sy * (hb + 0.1) + 0.2, zb + 4.2, zb + 5.1)
zd = zb + 4.2
b.ellipsoid(dome_m, 0, 0, zd, 1.55, 1.55, 1.9, nu=14, nv=7, zmin=0.0)
b.beam(gold, (0, 0, zd + 1.9), (0, 0, zd + 3.0), w=0.07, n=5)
b.ellipsoid(gold, 0, 0, zd + 3.0, 0.2, 0.2, 0.28, nu=8, nv=4)
b.beam(gold, (-0.5, 0, zd + 2.55), (0.5, 0, zd + 2.55), w=0.05, h=0.4)
objs = b.build('clock')
text_mesh('JONES & HIGGINS', 0.85, signm, (sx, sy, H0 - 0.95), rot=(math.radians(90), 0, yaw), extrude=0.08, name='clock_sign')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
export('clock', 'Jones & Higgins store: 4-storey grey-cream stone Venetian-Renaissance corner block (wedge footprint from OSM), lit shopfronts, paired round-arched windows, '
       'bracketed cornice, slim square clock tower (clock on 4 faces, balcony, hipped cap + weathervane) ~31 m. Built directly in OSM footprint coords.')
shoot = setup_preview('clock', (0, -2), 62, 30, ground_size=200)
for nm, az, dm, el in (('front34', -25, 0.9, 0.3), ('rear34', 150, 1.0, 0.3), ('side', 90, 0.85, 0.12), ('front', -5, 0.85, 0.12)):
    shoot(nm, az, dm, el)
