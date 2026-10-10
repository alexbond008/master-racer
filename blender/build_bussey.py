# Bussey Building (Copeland Park, 133 Rye Lane). Cues (Commons photos geograph 5086244 + 'Bussey Rooftop Bar' photo; Copeland Park / Peckham Vision text):
# 1 Victorian factory-warehouse of dark London stock brick (brown-yellow), 5 storeys (~22 m), very long and narrow (~119 x 11 m per OSM, with a slight bend ~ x=12)
# 2 dense regular grid of segmental-arched windows on every floor, cream stone string courses/cornice, ground floor big arched loading openings
# 3 roofline: repeated slate gables (sawtooth-like) along the west range, brick chimney stacks, a projecting hoist bay with jib
# 4 east range has a flat roof carrying the rooftop bar: timber deck, glazed bar shack, festoon lights, brick plant housing
# 5 big painted 'BUSSEY BUILDING' lettering across the front upper storeys, lit windows scattered (studios/venues)
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
reset()
rng = random.Random(5)
b = B()
brick = mat('Brick', (150, 106, 68), 0.9)
brick_d = mat('Brick_Dark', (118, 80, 52), 0.9)
stone = mat('Stone', (206, 190, 156), 0.8)
slate = mat('Slate', (62, 66, 76), 0.7)
dark = mat('Window_Dark', (16, 20, 30), 0.1, 0.4)
winw = mat('Emit_Window', (255, 200, 120), 0.3, emit=(255, 190, 100), strength=3.5)
doorg = mat('Door_Dark', (20, 18, 16), 0.8)
steel = mat('Steel', (40, 42, 48), 0.5, 0.7)
deck = mat('Timber', (140, 100, 62), 0.7)
glow = mat('Emit_Bar', (255, 170, 110), 0.3, emit=(255, 150, 90), strength=4.0)
fest = mat('Emit_Festoon', (255, 220, 150), 0.3, emit=(255, 200, 110), strength=7.0)
signm = mat('Emit_Sign', (255, 245, 220), 0.5, emit=(255, 240, 200), strength=1.6)
pink = mat('Furniture_Pink', (230, 90, 140), 0.6, emit=(230, 60, 120), strength=0.8)
NF = 5; FH = 4.3; ZE = NF * FH          # eaves 21.5
A = [(-65.34, 10.83), (11.45, 5.09), (13.96, -6.13), (-66.19, -0.21)]
Bq = [(11.45, 5.09), (53.23, -1.21), (52.89, -8.37), (13.96, -6.13)]

def centroid(P): return (sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P))

def facade(P, i, lit=0.3, bayw=3.4, windows=True, ground=True):
    p = P[i]; q = P[(i + 1) % len(P)]
    cx, cy = centroid(P)
    dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); u = (dx / L, dy / L)
    n = (u[1], -u[0])
    if (cx - p[0]) * n[0] + (cy - p[1]) * n[1] > 0: n = (-n[0], -n[1])
    nb = max(1, round(L / bayw)); bw = L / nb
    for k in range(nb):
        bx = p[0] + u[0] * bw * k; by = p[1] + u[1] * bw * k
        # piers: thin darker brick strips between bays
        b.wrect(brick_d, (bx, by, 0), u, n, 0.5, ZE, off=0.06)
        if ground:
            b.warch(doorg, (bx + u[0] * 0.55, by + u[1] * 0.55, 0.0), u, n, bw - 1.1, 3.4, rise=bw * 0.22, off=0.09)
            b.warch(stone, (bx + u[0] * 0.40, by + u[1] * 0.40, 0.0), u, n, bw - 0.8, 3.7, rise=bw * 0.25, off=0.04)
        for f in range(1, NF) if ground else range(0, NF):
            z = f * FH + 0.8
            m = winw if rng.random() < lit else dark
            b.warch(stone, (bx + u[0] * 0.45, by + u[1] * 0.45, z - 0.15), u, n, bw - 0.9, 2.65, rise=bw * 0.25, off=0.04)
            b.warch(m, (bx + u[0] * 0.65, by + u[1] * 0.65, z), u, n, bw - 1.3, 2.35, rise=bw * 0.22, off=0.09)
    for f in range(1, NF + 1):     # string courses
        b.wrect(stone, (p[0], p[1], f * FH - 0.35), u, n, L, 0.35, off=0.11)
    b.wrect(stone, (p[0], p[1], ZE), u, n, L, 0.7, off=0.18)  # cornice

for P in (A, Bq):
    b.prism(brick, P, 0, ZE)
    b.prism(stone, [(x, y) for x, y in P], ZE, ZE + 0.25)
facade(A, 0); facade(A, 2); facade(A, 3, bayw=3.7)       # west range: back, front, west gable end
facade(Bq, 0); facade(Bq, 2); facade(Bq, 1, bayw=3.7)      # east range
# interior edge of A / B shared: none drawn. 
# ---- west range roof: gables across the width (ridge perpendicular to the long axis)
ang = math.degrees(math.atan2(-5.92, 80.15))
b.frame(-66.19, -0.21, ang)
Lx = math.hypot(80.15, 5.92); n_g = 10; gw = Lx / n_g; D = 11.4
for i in range(n_g):
    b.gable(slate, i * gw, (i + 1) * gw, -0.1, D, ZE + 0.25, ZE + 0.25 + 3.4, along='y')
    # brick gable parapet face stone cap line
    # (small chimney every few bays)
for ci in (1.5, 4.5, 7.5):
    cxl = ci * gw + gw / 2
    b.box(brick_d, cxl - 0.6, cxl + 0.6, 5.0, 6.2, ZE + 1.5, ZE + 7.0)
    b.box(stone, cxl - 0.75, cxl + 0.75, 4.85, 6.35, ZE + 7.0, ZE + 7.3)
# hoist bay on the north (back, +y) face
hx0 = 5 * gw + 1.0
b.box(brick, hx0, hx0 + 3.4, D - 0.1, D + 2.0, ZE - 6.0, ZE + 3.0)
b.gable(slate, hx0 - 0.15, hx0 + 3.55, D - 0.1, D + 2.15, ZE + 3.0, ZE + 4.6, along='y')
b.beam(steel, (hx0 + 1.7, D + 0.5, ZE + 2.0), (hx0 + 1.7, D + 3.4, ZE + 2.0), w=0.25)
b.beam(steel, (hx0 + 1.7, D + 3.4, ZE + 2.0), (hx0 + 1.7, D + 3.4, ZE - 1.5), w=0.05, n=4)
b.box(steel, hx0 + 1.4, hx0 + 2.0, D + 3.2, D + 3.6, ZE - 2.3, ZE - 1.5)
b.wrect(winw, (hx0 + 0.6, D + 2.0, ZE - 2.6), (1, 0), (0, 1), 2.2, 2.2, off=0.04)
# ---- east range: flat roof deck = rooftop bar
ang2 = math.degrees(math.atan2(-6.3, 41.8))
b.frame(0, 0, 0)
zr = ZE + 0.25
yb = lambda x: -6.13 + (x - 13.96) * (-2.24 / 38.93)
yt = lambda x: 5.09 + (x - 11.45) * (-6.3 / 41.8)
b.prism(deck, [(15.0, yb(15.0) + 0.6), (52.0, yb(52.0) + 0.6), (52.0, yt(52.0) - 0.6), (15.0, yt(15.0) - 0.6)], zr, zr + 0.1)
b.box(brick_d, 19, 31, yb(25) + 0.6, yb(25) + 4.4, zr, zr + 3.2)                     # bar housing
b.quad(glow, (21, yb(25) + 0.58, zr + 0.5), (29, yb(25) + 0.58 - 0.0, zr + 0.5), (29, yb(25) + 0.58, zr + 2.6), (21, yb(25) + 0.58, zr + 2.6))
b.box(steel, 18.6, 31.4, yb(25) + 0.4, yb(25) + 4.6, zr + 3.2, zr + 3.4)
b.box(brick, 38, 43, yt(40) - 4.0, yt(40) - 0.7, zr, zr + 2.8)                       # stair head
poles = [(x, yy) for x in (17, 24, 31, 38, 45, 51) for yy in ('b', 't')]
def PY(x, k): return yb(x) + 1.0 if k == 'b' else yt(x) - 1.0
for (x, k) in poles:
    b.beam(steel, (x, PY(x, k), zr), (x, PY(x, k), zr + 3.2), w=0.07, n=4)
def fl(p0, p1):
    for i in range(9):
        t = i / 8; x = p0[0] + (p1[0] - p0[0]) * t; y = p0[1] + (p1[1] - p0[1]) * t
        z = zr + 3.2 - 0.55 * math.sin(math.pi * t)
        b.box(fest, x - 0.09, x + 0.09, y - 0.09, y + 0.09, z - 0.18, z)
xs_ = (17, 24, 31, 38, 45, 51)
for i in range(len(xs_) - 1):
    for k in 'bt':
        fl((xs_[i], PY(xs_[i], k)), (xs_[i + 1], PY(xs_[i + 1], k)))
for x in (17, 31, 45, 51): fl((x, PY(x, 'b')), (x, PY(x, 't')))
for (x, y) in ((40, 0.5), (44, -2.0), (47, -4.0), (21, 1.0), (27, 0.0)):
    b.box(pink, x - 0.8, x + 0.8, y - 0.5, y + 0.5, zr + 0.1, zr + 0.95)
for (p0, p1) in ((Bq[1], Bq[2]), (Bq[0], Bq[1]), (Bq[2], Bq[3])):
    b.beam(steel, (p0[0], p0[1], zr + 0.55), (p1[0], p1[1], zr + 0.55), w=0.08, h=1.1)
objs = b.build('bussey')
# painted sign on front (bottom edge of A), upper two storeys
p0, p1 = A[3], A[2]
Lf = math.hypot(p1[0] - p0[0], p1[1] - p0[1]); u = ((p1[0] - p0[0]) / Lf, (p1[1] - p0[1]) / Lf)
yaw = math.atan2(u[1], u[0])
mid = (p0[0] + u[0] * Lf * 0.30, p0[1] + u[1] * Lf * 0.30)
nrm = (u[1], -u[0])   # outward (front, -y)
loc = (mid[0] + nrm[0] * 0.3, mid[1] + nrm[1] * 0.3, 4 * FH + 0.6)
text_mesh('BUSSEY BUILDING', 2.6, signm, loc, rot=(math.radians(90), 0, yaw), extrude=0.12, name='bussey_sign')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
export('bussey', 'Bussey Building: 5-storey Victorian stock-brick factory, ~119 m x 11 m with slight bend; arched-window grid, slate gables, hoist bay, '
       'chimneys, flat east roof with rooftop bar + festoon lights, BUSSEY BUILDING lettering. Footprint built directly from OSM quads (no rotation).')
shoot = setup_preview('bussey', (-6, 0), 120, ZE, ground_size=500)
for nm, az, dm, el in (('front34', -35, 0.85, 0.22), ('rear34', 145, 0.85, 0.22), ('side', 0, 0.75, 0.09), ('top', -20, 0.9, 0.9)):
    shoot(nm, az, dm, el)
