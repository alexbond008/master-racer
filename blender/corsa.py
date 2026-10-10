"""Opel/Vauxhall Corsa B three-door (1993-2000). L3.73 W1.61 H1.42 WB2.44 wheel R0.29. Default Paint: white.
Run: blender -b --python corsa.py
Signature cues: rounded 'jelly-mould' egg; short bonnet sloping up to a deep, steeply raked windscreen;
big wrap-around clear-lens headlights; small black bumper bar + tiny grille slot; 3 doors (long door,
black B-pillar, small quarter window); upright-ish hatch with horizontal tail lights wrapping the corners;
body-colour mirrors; round arches with slotted wheel trims.
"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import small_cars_lib as L
importlib.reload(L)
from mathutils import Vector, Matrix

L.reset_scene()
WB, R_W, W_T, R_RIM = 2.44, 0.29, 0.155, 0.1651
TRACK_F, TRACK_R = 1.38, 1.36
YF, YR = -(WB / 2 + 0.625), WB / 2 + 0.595       # -1.845 .. 1.815; black bumpers add 0.03 each => L = 3.73
HW = 0.80

car = L.Car()
car.mats = L.standard_materials('#f2f2f0', rim='#b6b9bd', rim_metal=0.6, rim_rough=0.4, plate='#efe9d2')

keys = dict(
    zb=0.17,
    zt=[(YF, 0.725), (-1.75, 0.745), (-1.4, 0.80), (-1.0, 0.855), (-0.78, 0.885), (-0.72, 0.895),
        (-0.50, 1.05), (-0.30, 1.19), (-0.12, 1.32), (0.05, 1.395), (0.30, 1.419), (0.7, 1.405),
        (0.95, 1.37), (1.1, 1.30), (1.25, 1.19), (1.40, 1.07), (1.55, 0.99), (1.66, 0.955),
        (1.76, 0.935), (YR, 0.915)],
    zs=[(YF, 0.64), (-1.4, 0.69), (-1.0, 0.75), (-0.75, 0.83), (-0.4, 0.89), (1.2, 0.90), (1.55, 0.86), (YR, 0.78)],
    hw=[(YF, 0.73), (-1.4, 0.78), (-1.0, 0.795), (0.2, HW), (1.2, 0.795), (1.55, 0.775), (YR, 0.735)],
    tw=[(YF, 0.52), (-1.4, 0.58), (-0.9, 0.62), (-0.7, 0.62), (-0.3, 0.545), (0.3, 0.525), (1.0, 0.525),
        (1.3, 0.55), (1.6, 0.60), (YR, 0.60)],
    bw=0.92,
    rt=[(YF, 0.22), (-0.8, 0.26), (-0.5, 0.20), (1.2, 0.22), (1.5, 0.24), (YR, 0.24)],
    rs=0.22, rb=0.09,
)
body = L.loft_body(keys, YF, YR, 0.11, 0.09, step=0.04, k=5, end_seg=8)

R_ARCH = R_W + 0.045
hubs_cut = [(s, y, R_W) for s in (1, -1) for y in (-WB / 2, WB / 2)]
body = L.boolean_cut(body, L.wheel_cutter(hubs_cut, R_ARCH, 0.50, 1.3))
car.set_bm('body', body.copy(), 'Paint')
S = body

for s in (1, -1):
    for y in (-WB / 2, WB / 2):
        L.arch_liner(car, 'trim', 'Trim', s, y, R_W, R_ARCH - 0.004, 0.505, 0.745, 0.19)

# ---------------------------------------------------------------- glass (windows are real openings)
wins = []


def win(pts, frame):
    wins.append((pts, frame))
    car.decal('glass', 'Glass', S, pts, frame, 0.001)


win([(-0.56, 0.96), (0.56, 0.96), (0.50, 1.355), (-0.50, 1.355)], L.front(0.0))
win([(-0.54, 1.005), (0.54, 1.005), (0.46, 1.335), (-0.46, 1.335)], L.rear(0.8))
for s in (1, -1):
    door = [(-0.62, 0.945), (-0.16, 1.325), (-0.08, 1.352), (0.50, 1.362), (0.57, 1.34), (0.57, 0.945)]
    quarter = [(0.73, 0.945), (0.73, 1.34), (0.98, 1.335), (1.18, 1.24), (1.38, 1.08), (1.50, 0.97), (1.50, 0.945)]
    win(door, L.side(s, 0.52))
    win(quarter, L.side(s, 0.52))
    # black B-pillar
    car.decal('trim', 'Trim', S, [(0.57, 0.945), (0.57, 1.36), (0.73, 1.35), (0.73, 0.945)], L.side(s, 0.52), 0.0035)
    # door shut lines
    car.strip('trim', 'Trim', S, [(-0.62, 0.30), (-0.64, 0.90)], 0.006, L.side(s), 0.004)
    car.strip('trim', 'Trim', S, [(0.62, 0.30), (0.60, 0.94)], 0.006, L.side(s), 0.004)
    car.strip('trim', 'Trim', S, [(-0.62, 0.30), (0.62, 0.30)], 0.006, L.side(s), 0.004)
    # black body-side rubbing strip & sill
    car.strip('trim', 'Trim', S, [(-0.58, 0.58), (0.58, 0.58)], 0.04, L.side(s), 0.004)
    car.strip('trim', 'Trim', S, [(-0.70, 0.23), (0.70, 0.23)], 0.05, L.side(s), 0.004)
    # door handle
    car.decal('trim', 'Trim', S, L.rrect_pts(0.44, 0.985, 0.10, 0.026, 0.01), L.side(s), 0.008)

# ---------------------------------------------------------------- nose
FR = L.front(-1.66)
for sx in (1, -1):
    lens = [(0.30, 0.56), (0.31, 0.645), (0.45, 0.695), (0.65, 0.71), (0.77, 0.705), (0.805, 0.645), (0.785, 0.56), (0.62, 0.515), (0.42, 0.515)]
    rim = [(0.285, 0.545), (0.295, 0.655), (0.45, 0.71), (0.65, 0.725), (0.785, 0.72), (0.825, 0.65), (0.80, 0.545), (0.62, 0.50), (0.42, 0.50)]
    car.decal('trim', 'Chrome', S, [(sx * a, b) for a, b in rim], FR, 0.004)
    car.decal('lights', 'HeadLight', S, [(sx * a, b) for a, b in lens], FR, 0.008)
    # the lamp sweeps back along the wing
    car.decal('trim', 'Chrome', S, [(-1.845, 0.53), (-1.845, 0.675), (-1.78, 0.715), (-1.62, 0.72), (-1.44, 0.70), (-1.37, 0.655), (-1.52, 0.60), (-1.70, 0.53)], L.side(sx, 0.70), 0.004)
    car.decal('lights', 'HeadLight', S, [(-1.845, 0.545), (-1.845, 0.665), (-1.78, 0.705), (-1.62, 0.71), (-1.45, 0.69), (-1.40, 0.65), (-1.55, 0.60), (-1.70, 0.545)], L.side(sx, 0.70), 0.008)
    for cx_, cz_, rr_ in ((0.45, 0.60, 0.050), (0.65, 0.615, 0.044)):
        car.decal('trim', 'Chrome', S, L.circle_pts(sx * cx_, cz_, rr_, n=18), FR, 0.011)
        car.decal('lights', 'HeadLight', S, L.circle_pts(sx * cx_, cz_, rr_ * 0.55, n=14), FR, 0.014)
car.decal('trim', 'Trim', S, L.rrect_pts(0, 0.605, 0.34, 0.06, 0.02), FR, 0.005)
car.decal('trim', 'Chrome', S, L.circle_pts(0, 0.605, 0.022, n=14), FR, 0.008)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.492, 0.50, 0.095, 0.008), FR, 0.005)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.492, 0.485, 0.082, 0.006), FR, 0.0065)
# bonnet seams
car.strip('trim', 'Trim', S, [(-0.62, -0.77), (0.62, -0.77)], 0.005, L.top(0.5), 0.004)
for sx in (1, -1):
    car.strip('trim', 'Trim', S, [(sx * 0.60, -1.55), (sx * 0.60, -0.77)], 0.005, L.top(0.5), 0.004)

# ---------------------------------------------------------------- tail
RR = L.rear(1.5)
for sx in (1, -1):
    car.decal('trim', 'Chrome', S, L.rrect_pts(sx * 0.585, 0.745, 0.35, 0.145, 0.04), RR, 0.004)
    car.decal('lights', 'TailLight', S, L.rrect_pts(sx * 0.585, 0.745, 0.33, 0.125, 0.035), RR, 0.007)
    car.decal('lights', 'TailLight', S, [(1.84, 0.70), (1.84, 0.80), (1.74, 0.81), (1.64, 0.80), (1.62, 0.72), (1.68, 0.69)], L.side(sx, 0.70), 0.007)
    car.decal('trim', 'Trim', S, L.rrect_pts(sx * 0.585, 0.745, 0.03, 0.115, 0.01), RR, 0.010)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.56, 0.52, 0.11, 0.008), RR, 0.005)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.56, 0.505, 0.097, 0.006), RR, 0.0065)
car.decal('trim', 'Trim', S, L.rrect_pts(0, 0.68, 0.14, 0.03, 0.01), RR, 0.005)      # tailgate handle
car.strip('trim', 'Trim', S, [(-0.70, 0.88), (0.70, 0.88)], 0.005, RR, 0.004)         # tailgate seam

# ---------------------------------------------------------------- bumpers (black bars)
bsec = [(-0.008, -0.058), (0.016, -0.062), (0.032, -0.045), (0.035, 0.0), (0.032, 0.045), (0.016, 0.062), (-0.008, 0.058)]


def bar(y_end, z, sgn):
    half, wrap, tb = 0.52, 0.17, 0.17
    p = []
    for i in range(-6, 7):
        p.append((i / 6 * half, y_end, z))
    for side in (1, -1):
        seg = []
        for j in range(1, 7):
            a = math.radians(90 * j / 6)
            seg.append((side * (half + wrap * math.sin(a)), y_end - sgn * tb * (1 - math.cos(a)), z))
        p = p + seg if side == 1 else list(reversed(seg)) + p
    return p


car.sweep('trim', 'Trim', bar(YF + 0.002, 0.345, -1), bsec, (0, -1, 0))
car.sweep('trim', 'Trim', bar(YR - 0.002, 0.345, 1), bsec, (0, 1, 0))

# ---------------------------------------------------------------- mirrors (body colour)
for sx in (1, -1):
    car.ellipsoid('mirrors', 'Paint', (sx * 0.872, -0.52, 0.985), (0.03, 0.07, 0.05), 10, 6)
    car.box('mirrors', 'Paint', (sx * 0.81, -0.52, 0.95), (0.13, 0.04, 0.022), 0.008)
    car.ellipsoid('mirrors', 'Chrome', (sx * 0.899, -0.52, 0.985), (0.004, 0.058, 0.04), 10, 6)

# ---------------------------------------------------------------- interior (windows are open, so it is visible)
L.cut_openings(car.objs['body'][0], wins)
shell = L.interior_shell(keys, -0.68, 1.52, 0.30, 0.045, wins, cutter=L.wheel_cutter(hubs_cut, R_ARCH + 0.01, 0.50, 1.3))
car.add_bm('interior', 'Interior', shell)
L.furnish(car, dict(dside=-1, sx=0.33, floor=0.30, dash=(-0.70, 0.30, 0.84, 0.68), wheel=(-0.36, 0.86, 0.19, 0.70),
                    seat=(0.12, 0.50), rear=(0.92, 1.17, 1.15, 0.46), shelf=(1.34, 0.93, 0.30, 1.0)))

# ---------------------------------------------------------------- wheels
hubs = {}
for nm, sx, sy, tr in (('wheel_fl', +1, -1, TRACK_F), ('wheel_fr', -1, -1, TRACK_F),
                       ('wheel_rl', +1, +1, TRACK_R), ('wheel_rr', -1, +1, TRACK_R)):
    L.build_wheel(car, nm, sx, R_W, W_T, R_RIM, 'steel_plastic', seg=24)
    hubs[nm] = (sx * tr / 2, sy * WB / 2, R_W)

objs = car.build_objects()
for nm, p in hubs.items():
    objs[nm].location = Vector(p)
print('TRIANGLES', L.tri_count(objs))
L.export_glb(os.path.join(L.CARS_OUT, 'corsa.glb'))
print('exported corsa')
