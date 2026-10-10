# Jones & Higgins store + Jarvis clock tower (Rye Lane / Peckham High St corner). Cues (Commons geograph 1741847, 'Jones and Higgins (8667814865)'; Victorian Society; Southwark News):
# 1 four-storey Venetian-Renaissance store, grey/cream stone (NOT red - photos show pale grey-cream stone, with red brick only on neighbours/back walls)
# 2 rusticated dark-fronted ground floor with big lit shop windows and a cream fascia sign; strong stone string courses between floors
# 3 upper floors: paired round-arched windows with moulded surrounds + pilasters, wide bracketed cornice and parapet
# 4 slim square clock tower rising from the centre of the front roofline: balustraded balcony, clock face (emissive) on 3 faces, cornice, small hipped cap + weathervane
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
    # parapet balusters band
    b.wrect(cream, (p[0], p[1], ZE + 0.5), u, n, L, 0.8, off=0.0)
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
# --- clock tower on the roof, centred on the front facade, set back 3.4 m
tcx = pf[0] + uf[0] * Lf * 0.5 - nf[0] * 3.6; tcy = pf[1] + uf[1] * Lf * 0.5 - nf[1] * 3.6
ang = math.degrees(yaw)
b.frame(tcx, tcy, ang)
tw = 3.9; h = tw / 2
z0 = ZE + 0.5
b.box(stone, -h - 0.4, h + 0.4, -h - 0.4, h + 0.4, z0, z0 + 0.7)                     # plinth
b.box(stone, -h, h, -h, h, z0 + 0.7, z0 + 11.0)                                      # shaft
# quoin / panel lines
for zz in (z0 + 3.6, z0 + 9.2):
    b.box(cream, -h - 0.15, h + 0.15, -h - 0.15, h + 0.15, zz, zz + 0.4)
# balcony (balustrade) on the front face
bz = z0 + 2.2
b.box(cream, -1.7, 1.7, -h - 1.0, -h, bz, bz + 0.35)
for k in range(7):
    b.box(cream, -1.55 + k * 0.5, -1.4 + k * 0.5, -h - 0.95, -h - 0.8, bz + 0.35, bz + 1.15)
b.box(cream, -1.7, 1.7, -h - 1.0, -h - 0.8, bz + 1.15, bz + 1.3)
b.warch(dark, (-0.6, -h, bz + 0.35), (1, 0), (0, -1), 1.2, 2.2, rise=0.6, off=0.05)   # door/window behind balcony
# clock stage
cz = z0 + 6.4; cr = 1.05
for (cx_, cy_, ux, uy, nx, ny) in ((0, -h, 1, 0, 0, -1), (0, h, -1, 0, 0, 1), (-h, 0, 0, -1, -1, 0), (h, 0, 0, 1, 1, 0)):
    seg = 16
    pts = [(cx_ + nx * 0.06 + ux * cr * math.cos(2 * math.pi * i / seg), cy_ + ny * 0.06 + uy * cr * math.cos(2 * math.pi * i / seg), cz + cr * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    e1 = Vector(pts[1]) - Vector(pts[0]); e2 = Vector(pts[2]) - Vector(pts[1])
    # winding must give outward normal in WORLD; local frame is rotated but handedness preserved -> test in local
    if e1.cross(e2).dot(Vector((nx, ny, 0))) < 0: pts = pts[::-1]
    b.poly(clockm, pts)
    b.quad(hand, (cx_ + nx * 0.1, cy_ + ny * 0.1, cz), (cx_ + nx * 0.1, cy_ + ny * 0.1, cz + 1.0), (cx_ + nx * 0.1 + ux * 0.09, cy_ + ny * 0.1 + uy * 0.09, cz + 1.0), (cx_ + nx * 0.1 + ux * 0.09, cy_ + ny * 0.1 + uy * 0.09, cz))
    b.quad(hand, (cx_ + nx * 0.1, cy_ + ny * 0.1, cz), (cx_ + nx * 0.1 + ux * 0.8, cy_ + ny * 0.1 + uy * 0.8, cz), (cx_ + nx * 0.1 + ux * 0.8, cy_ + ny * 0.1 + uy * 0.8, cz + 0.09), (cx_ + nx * 0.1, cy_ + ny * 0.1, cz + 0.09))
# arched louvred belfry slots above clock on 4 faces
for (cx_, cy_, ux, uy, nx, ny) in ((0, -h, 1, 0, 0, -1), (0, h, -1, 0, 0, 1), (-h, 0, 0, -1, -1, 0), (h, 0, 0, 1, 1, 0)):
    b.warch(dark, (cx_ + ux * -0.45 * 1 + 0, cy_ + uy * -0.45, z0 + 8.3), (ux, uy), (nx, ny), 0.9, 1.9, rise=0.45, off=0.06)
# top cornice + cap
b.box(cream, -h - 0.5, h + 0.5, -h - 0.5, h + 0.5, z0 + 11.0, z0 + 11.5)
b.box(stone, -h - 0.3, h + 0.3, -h - 0.3, h + 0.3, z0 + 11.5, z0 + 11.9)
b.pyramid(roofm, -h - 0.3, h + 0.3, -h - 0.3, h + 0.3, z0 + 11.9, z0 + 14.0)
b.beam(steel, (0, 0, z0 + 14.0), (0, 0, z0 + 16.0), w=0.08, n=5)
b.beam(steel, (-0.6, 0, z0 + 15.4), (0.6, 0, z0 + 15.4), w=0.06, h=0.5)
objs = b.build('clock')
text_mesh('JONES & HIGGINS', 0.85, signm, (sx, sy, H0 - 0.95), rot=(math.radians(90), 0, yaw), extrude=0.08, name='clock_sign')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
export('clock', 'Jones & Higgins store: 4-storey grey-cream stone Venetian-Renaissance corner block (wedge footprint from OSM), lit shopfronts, paired round-arched windows, '
       'bracketed cornice, slim square clock tower (clock on 4 faces, balcony, hipped cap + weathervane) ~31 m. Built directly in OSM footprint coords.')
shoot = setup_preview('clock', (0, -2), 62, 30, ground_size=200)
for nm, az, dm, el in (('front34', -25, 0.9, 0.3), ('rear34', 150, 1.0, 0.3), ('side', 90, 0.85, 0.12), ('front', -5, 0.85, 0.12)):
    shoot(nm, az, dm, el)
