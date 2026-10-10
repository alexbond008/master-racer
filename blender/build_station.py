# Peckham Rye station (Charles Henry Driver 1865-66, Grade II). Cues (Historic England text, Commons photos 'Peckham Rye station.jpg', geograph 4439432, 3003526):
# 1 pale buff/yellow-grey London stock brick with cream stone dressings, 'continental renaissance' H-plan station building, 3 storeys, boldly moulded bracket cornice
# 2 ground floor arcade of round arches (green-glazed, lit ticket hall), upper floors round-headed windows with stone surrounds and string courses
# 3 curved/mansard roof over the centre with dormers; a tall square clock/entrance block above the central bay
# 4 canopied forecourt (glazed cast-iron canopy, PECKHAM RYE fascia sign)
# 5 platforms on TWO brick viaducts on arches (~8.6 m) with platform canopies on slim posts, parapets, rails, lamps; long arched front range (west arm of OSM footprint)
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
reset()
rng = random.Random(9)
b = B()
brick = mat('Brick_Buff', (186, 166, 120), 0.9)
brick_d = mat('Brick_Arch', (150, 120, 82), 0.9)
stone = mat('Stone', (228, 218, 192), 0.8)
slate = mat('Slate', (66, 70, 80), 0.6)
dark = mat('Window_Dark', (14, 20, 28), 0.1, 0.4)
winw = mat('Emit_Window', (255, 205, 120), 0.3, emit=(255, 190, 100), strength=3.5)
arch_g = mat('Emit_Arch_Glass', (110, 190, 150), 0.2, emit=(150, 220, 160), strength=2.4)
steel = mat('Steel', (46, 52, 54), 0.5, 0.7)
canopy_m = mat('Canopy_Teal', (34, 84, 80), 0.5, 0.3)
glass = mat('Glass_Canopy', (70, 110, 112), 0.1, 0.1, emit=(90, 140, 140), strength=0.3)
concrete = mat('Platform', (150, 150, 146), 0.9)
ballast = mat('Ballast', (70, 66, 62), 1.0)
rail = mat('Rail', (120, 100, 90), 0.5, 0.8)
lamp = mat('Emit_Lamp', (255, 235, 190), 0.3, emit=(255, 225, 170), strength=6.0)
clockm = mat('Emit_Clock', (255, 250, 230), 0.4, emit=(255, 245, 210), strength=4.0)
signm = mat('Emit_Sign', (235, 245, 255), 0.4, emit=(220, 235, 255), strength=3.5)
hand = mat('Clock_Hands', (20, 20, 22), 0.5)
ZV = 8.6   # viaduct deck height

def lerp(a, b_, t): return (a[0] + (b_[0] - a[0]) * t, a[1] + (b_[1] - a[1]) * t)
class Via:
    def __init__(s, F0, F1, K0, K1): s.F0, s.F1, s.K0, s.K1 = F0, F1, K0, K1
    def P(s, t, sv):
        F = lerp(s.F0, s.F1, t); K = lerp(s.K0, s.K1, t); return lerp(F, K, sv)
    def L(s): return math.hypot(s.F1[0] - s.F0[0], s.F1[1] - s.F0[1])
    def strip(s, m, t0, t1, s0, s1, z):
        pts = [s.P(t0, s0), s.P(t1, s0), s.P(t1, s1), s.P(t0, s1)]
        b.poly(m, [(p[0], p[1], z) for p in pts])
    def slab(s, m, t0, t1, s0, s1, z0, z1):
        pts = [s.P(t0, s0), s.P(t1, s0), s.P(t1, s1), s.P(t0, s1)]
        b.prism(m, pts, z0, z1)
    def line(s, m, t0, t1, sv, z, w=0.12, h=None):
        a = s.P(t0, sv); c = s.P(t1, sv); b.beam(m, (a[0], a[1], z), (c[0], c[1], z), w=w, h=h)

def viaduct(V, arches_front=True, arches_back=False, ends=(True, True), bay=5.0, track_t=(0.0, 1.0)):
    # body
    pts = [V.P(0, 0), V.P(1, 0), V.P(1, 1), V.P(0, 1)]
    b.prism(brick, pts, 0, ZV)
    b.prism(stone, pts, ZV, ZV + 0.4)                                  # coping slab
    # arches along front edge
    n = max(1, round(V.L() / bay))
    for sv_edge, nrm in ((0.0, -1),) if arches_front else ():
        pass
    def arch_row(sv, t0=0.0, t1=1.0):
        a = V.P(t0, sv); c = V.P(t1, sv)
        dx, dy = c[0] - a[0], c[1] - a[1]; Ln = math.hypot(dx, dy); u = (dx / Ln, dy / Ln)
        nrm = (u[1], -u[0]) if sv < 0.5 else (-u[1], u[0])
        if sv >= 0.5: u = (-u[0], -u[1]); a = c
        k = max(1, round(Ln / bay)); bw = Ln / k
        for i in range(k):
            bx, by = a[0] + u[0] * bw * i, a[1] + u[1] * bw * i
            ww = bw - 1.3
            b.warch(stone, (bx + u[0] * 0.55, by + u[1] * 0.55, 0.0), u, nrm, bw - 1.1, 6.2, rise=(bw - 1.1) / 2, off=0.04)
            m = arch_g if rng.random() < 0.35 else dark
            b.warch(m, (bx + u[0] * 0.75, by + u[1] * 0.75, 0.0), u, nrm, ww, 5.9, rise=ww / 2, off=0.08)
        # impost band
        b.wrect(stone, (a[0], a[1], ZV - 0.9), u, nrm, Ln, 0.5, off=0.1)
    if arches_front: arch_row(0.0)
    if arches_back: arch_row(1.0)
    # parapet walls (both long edges)
    for sv in (0.0, 1.0):
        a, c = V.P(0, sv), V.P(1, sv)
        b.beam(brick_d, (a[0], a[1], ZV + 0.4 + 0.6), (c[0], c[1], ZV + 0.4 + 0.6), w=0.35, h=1.2)
    # platform + ballast + tracks
    zt = ZV + 0.4
    V.strip(concrete, track_t[0], track_t[1], 0.07, 0.42, zt + 0.12) if False else V.slab(concrete, track_t[0], track_t[1], 0.07, 0.42, zt, zt + 0.9)
    V.strip(ballast, track_t[0], track_t[1], 0.46, 0.93, zt + 0.05)
    for sv in (0.58, 0.64, 0.80, 0.86):
        V.line(rail, track_t[0], track_t[1], sv, zt + 0.16, w=0.1, h=0.16)
    # canopy: posts + roof + lamps
    nposts = max(2, int(V.L() // 8))
    for i in range(nposts + 1):
        t = 0.02 + 0.96 * i / nposts
        p = V.P(t, 0.32)
        b.beam(steel, (p[0], p[1], zt + 0.9), (p[0], p[1], zt + 5.2), w=0.16)
        q = V.P(t, 0.30)
        if i < nposts: b.quad(lamp, (q[0] - 0.2, q[1] - 0.2, zt + 4.6), (q[0] + 0.2, q[1] - 0.2, zt + 4.6), (q[0] + 0.2, q[1] + 0.2, zt + 4.6), (q[0] - 0.2, q[1] + 0.2, zt + 4.6))
    V.slab(canopy_m, 0.02, 0.98, 0.12, 0.52, zt + 5.2, zt + 5.45)
    V.slab(glass, 0.03, 0.97, 0.16, 0.48, zt + 5.45, zt + 5.55)

# --- west arm = long arched viaduct #1 (south range)
VA = Via((-82.48, -30.0), (7.73, -25.51), (-82.64, -14.37), (7.28, -14.51))
viaduct(VA, arches_front=True, arches_back=False, bay=5.2)
# --- north viaduct #2 (platforms 3-4), polygon C
VC = Via((-21.84, 9.59), (-0.43, 10.62), (-22.59, 25.37), (1.0, 26.8))
viaduct(VC, arches_front=True, arches_back=False, bay=5.0)
VC2 = Via((-0.43, 10.62), (24.3, 13.96), (1.0, 26.8), (26.2, 27.77))
viaduct(VC2, arches_front=False, arches_back=False, bay=5.0)

# --- main station building (frame along its front)
ang = math.degrees(math.atan2(0.72, 19.54))
b.frame(7.28, -14.51, ang)
W = 19.6; Dp = 11.2
H1, H2, H3 = 5.0, 4.4, 3.9; ZE = H1 + H2 + H3
b.box(brick, 0, W, 0, Dp, 0, ZE)
b.box(stone, -0.15, W + 0.15, -0.35, Dp + 0.15, ZE - 0.1, ZE + 0.2)                     # cornice slab
nb = 7; bw = W / nb
for i in range(nb):
    x = i * bw
    b.box(stone, x - 0.0, x + 0.55, -0.12, 0.0, 0.0, H1)                              # pier
    b.warch(stone, (x + 0.6, 0, 0.0), (1, 0), (0, -1), bw - 0.65, 4.4, rise=(bw - 0.65) / 2, off=0.03)
    b.warch(arch_g if i != 3 else winw, (x + 0.8, 0, 0.0), (1, 0), (0, -1), bw - 1.05, 4.2, rise=(bw - 1.05) / 2, off=0.07)
    for fl, z0, hh in ((1, H1 + 0.7, 2.9), (2, H1 + H2 + 0.5, 2.6)):
        b.warch(stone, (x + 0.55, 0, z0 - 0.15), (1, 0), (0, -1), bw - 0.55, hh + 0.3, rise=(bw - 0.55) / 2, off=0.04)
        b.warch(winw if rng.random() < 0.55 else dark, (x + 0.8, 0, z0), (1, 0), (0, -1), bw - 1.05, hh, rise=(bw - 1.05) / 2, off=0.08)
b.box(stone, 0, W, -0.25, 0.0, H1 - 0.1, H1 + 0.35)                                   # string courses
b.box(stone, 0, W, -0.25, 0.0, H1 + H2 - 0.1, H1 + H2 + 0.3)
# brackets under cornice
for i in range(int(W / 0.9)):
    b.box(stone, 0.2 + i * 0.9, 0.5 + i * 0.9, -0.3, 0, ZE - 0.7, ZE - 0.1)
# side elevations: simple windows
for xs, nx in ((0, -1), (W, 1)):
    for k in range(3):
        for fl, z0, hh in ((0, 0.8, 3.0), (1, H1 + 0.7, 2.6), (2, H1 + H2 + 0.5, 2.4)):
            y0 = 1.2 + k * 3.2
            b.wrect(winw if rng.random() < 0.4 else dark, (xs, y0, z0), (0, 1), (nx, 0), 1.6, hh, off=0.05)
# mansard roof (frustum) + dormers
zb = ZE + 0.2; inset = 2.2; hrf = 3.6
def frustum(m, x0, x1, y0, y1, z0, z1, ins):
    A_ = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
    Bq_ = [(x0 + ins, y0 + ins, z1), (x1 - ins, y0 + ins, z1), (x1 - ins, y1 - ins, z1), (x0 + ins, y1 - ins, z1)]
    for i in range(4):
        j = (i + 1) % 4
        b.poly(m, [A_[i], A_[j], Bq_[j], Bq_[i]])
    b.poly(m, Bq_)
frustum(slate, 0.0, W, 0.0, Dp, zb, zb + hrf, inset)
b.box(slate, inset + 0.3, W - inset - 0.3, inset + 0.3, Dp - inset - 0.3, zb + hrf, zb + hrf + 0.5)
for i in range(6):
    dx = 2.0 + i * 3.1
    if abs(dx - W / 2) < 2.0: continue
    t = 0.35
    b.box(slate, dx, dx + 1.1, 0.3, 1.0, zb + 0.6, zb + 2.3)
    b.wrect(winw, (dx + 0.15, -0.0, zb + 0.9), (1, 0), (0, -1), 0.8, 1.0, off=0.0) if False else \
        b.quad(winw, (dx + 0.15, 0.28, zb + 0.9), (dx + 0.95, 0.28, zb + 0.9), (dx + 0.95, 0.28, zb + 1.9), (dx + 0.15, 0.28, zb + 1.9))
# --- clock / entrance tower (centre front)
tw = 6.4; tx0 = W / 2 - tw / 2; tx1 = W / 2 + tw / 2; ty0 = -0.6; ty1 = 5.2
ZT0 = ZE; ZT1 = ZE + 9.2
b.box(brick, tx0, tx1, ty0, ty1, 0, ZT1)                                              # projecting central bay & tower shaft
b.box(stone, tx0 - 0.15, tx1 + 0.15, ty0 - 0.15, ty1 + 0.15, ZT1, ZT1 + 0.5)
b.box(stone, tx0 - 0.1, tx1 + 0.1, ty0 - 0.1, ty1 + 0.1, ZE - 0.1, ZE + 0.2)
# entrance arch on the projecting bay
b.warch(stone, (tx0 + 0.9, ty0, 0), (1, 0), (0, -1), tw - 1.8, 5.2, rise=(tw - 1.8) / 2, off=0.04)
b.warch(winw, (tx0 + 1.2, ty0, 0), (1, 0), (0, -1), tw - 2.4, 4.9, rise=(tw - 2.4) / 2, off=0.08)
for fl, z0, hh in ((1, H1 + 0.7, 2.9), (2, H1 + H2 + 0.5, 2.6)):
    for k in range(2):
        xx = tx0 + 0.9 + k * 2.7
        b.warch(stone, (xx, ty0, z0 - 0.15), (1, 0), (0, -1), 1.9, hh + 0.3, rise=0.95, off=0.04)
        b.warch(winw, (xx + 0.2, ty0, z0), (1, 0), (0, -1), 1.5, hh, rise=0.75, off=0.08)
# clock stage with faces on 4 sides
cz = ZE + 3.6; cr = 1.55
for (cx_, cy_, ux, uy, nx, ny) in ((W / 2, ty0, 1, 0, 0, -1), (W / 2, ty1, -1, 0, 0, 1), (tx0, (ty0 + ty1) / 2, 0, -1, -1, 0), (tx1, (ty0 + ty1) / 2, 0, 1, 1, 0)):
    seg = 16
    pts = [(cx_ + nx * 0.05 + ux * cr * math.cos(2 * math.pi * i / seg), cy_ + ny * 0.05 + uy * cr * math.cos(2 * math.pi * i / seg), cz + cr * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    # winding so normal points outward
    e1 = Vector(pts[1]) - Vector(pts[0]); e2 = Vector(pts[2]) - Vector(pts[1])
    if e1.cross(e2).dot(Vector((nx, ny, 0))) < 0: pts = pts[::-1]
    b.poly(clockm, pts)
    b.quad(hand, (cx_ + nx * 0.09, cy_ + ny * 0.09, cz), (cx_ + nx * 0.09, cy_ + ny * 0.09, cz + 1.2), (cx_ + nx * 0.09 + ux * 0.1, cy_ + ny * 0.09 + uy * 0.1, cz + 1.2), (cx_ + nx * 0.09 + ux * 0.1, cy_ + ny * 0.09 + uy * 0.1, cz))
    b.quad(hand, (cx_ + nx * 0.09, cy_ + ny * 0.09, cz), (cx_ + nx * 0.09 + ux * 0.9, cy_ + ny * 0.09 + uy * 0.9, cz), (cx_ + nx * 0.09 + ux * 0.9, cy_ + ny * 0.09 + uy * 0.9, cz + 0.1), (cx_ + nx * 0.09, cy_ + ny * 0.09, cz + 0.1))
# tower cap: pyramid + finial
b.pyramid(slate, tx0 - 0.4, tx1 + 0.4, ty0 - 0.4, ty1 + 0.4, ZT1 + 0.5, ZT1 + 4.2)
b.beam(steel, (W / 2, (ty0 + ty1) / 2, ZT1 + 4.2), (W / 2, (ty0 + ty1) / 2, ZT1 + 6.2), w=0.12, n=5)
# --- forecourt canopy (cast iron + glass), 4 m deep in front of main building
cy0 = -4.2
b.box(canopy_m, -1.5, W + 1.5, cy0, -0.4, 5.6, 5.9)
b.box(glass, -1.2, W + 1.2, cy0 + 0.2, -0.6, 5.9, 6.0)
b.box(canopy_m, -1.5, W + 1.5, cy0 - 0.15, cy0 + 0.0, 4.9, 5.9)   # fascia
for i in range(6):
    xx = -1.0 + i * (W + 2.0) / 5
    b.beam(steel, (xx, cy0 + 0.2, 0.0), (xx, cy0 + 0.2, 5.6), w=0.18)
# ticket-hall wing M2 (2 storey, behind/west of M1) in world coords
b.frame(0, 0, 0)
def wing(x0, x1, y0, y1, h):
    b.box(brick, x0, x1, y0, y1, 0, h)
    b.box(stone, x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, h, h + 0.3)
    b.gable(slate, x0 - 0.2, x1 + 0.2, y0 - 0.2, y1 + 0.2, h + 0.3, h + 3.6, along='x')
    nbw = max(1, int((x1 - x0) / 3.0)); w_ = (x1 - x0) / nbw
    for i in range(nbw):
        for z0_, hh in ((0.9, 3.3), (h / 2 + 0.7, 2.6)):
            b.warch(stone, (x0 + i * w_ + 0.5, y0, z0_ - 0.15), (1, 0), (0, -1), w_ - 1.0, hh + 0.3, rise=(w_ - 1.0) / 2, off=0.04)
            b.warch(winw if rng.random() < 0.5 else dark, (x0 + i * w_ + 0.7, y0, z0_), (1, 0), (0, -1), w_ - 1.4, hh, rise=(w_ - 1.4) / 2, off=0.08)
wing(1.6, 19.0, -3.4, 10.4, 9.0)
wing(1.6, 7.0, -10.5, -3.4, 5.5)
objs = b.build('station')
# PECKHAM RYE on the forecourt canopy fascia
fx, fy, fz = Frame(7.28, -14.51, ang).p(W / 2, cy0 - 0.2, 5.15)
text_mesh('PECKHAM RYE', 0.75, signm, (fx, fy, fz), rot=(math.radians(90), 0, math.radians(ang)), extrude=0.08, name='station_sign')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
export('peckham_station', 'Peckham Rye station: H-plan 3-storey buff stock-brick station (round-arch arcade, bracket cornice, mansard, clock tower) with glazed forecourt canopy '
       'PECKHAM RYE, ticket-hall wing, and two brick viaducts (8.6 m) with canopied platforms and rails. Built directly in OSM footprint coords.')
shoot = setup_preview('peckham_station', (-28, 0), 105, 28, ground_size=400)
for nm, az, dm, el in (('front34', -30, 0.95, 0.3), ('rear34', 150, 0.95, 0.3), ('side', 90, 0.8, 0.15), ('top', -20, 0.9, 1.1)):
    shoot(nm, az, dm, el)
shoot2 = setup_preview('peckham_station_close', (14, -2), 40, 20, ground=False)
for nm, az, dm, el in (('front34', -30, 1.0, 0.25), ('front', 0, 0.8, 0.1), ('rear34', 150, 1.1, 0.4)):
    shoot2(nm, az, dm, el)
