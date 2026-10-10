"""Fiat 126p 'Maluch' (1973-2000). L3.05 W1.38 H1.34 WB1.84 wheel R0.26. Default Paint: Polish red.
Run: blender -b --python fiat126.py
Signature cues: upright boxy two-door; flat sheer nose, round corner headlights, tiny grille slot;
near-vertical rear window over a louvred engine lid; thin chrome bumpers; small round-ish tail lights;
narrow door glass + small quarter window; steel wheels with chrome hubcaps; rear-engine louvres.
"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import small_cars_lib as L
importlib.reload(L)
from mathutils import Vector, Matrix

L.reset_scene()
WB, R_W, W_T = 1.84, 0.26, 0.135
TRACK = 1.15
YF, YR = -(WB / 2 + 0.53), WB / 2 + 0.62            # body ends -1.45 .. 1.54; bumpers add 0.03 each => L = 3.05
HW = 0.683

car = L.Car()
car.mats = L.standard_materials('#c0141c', rim='#a9acb0', rim_metal=0.6, rim_rough=0.4, plate='#efe9d2')

keys = dict(
    zb=0.19,
    zt=[(YF, 0.77), (-1.35, 0.80), (-1.0, 0.83), (-0.82, 0.85), (-0.74, 0.87), (-0.52, 1.10), (-0.30, 1.31),
        (-0.15, 1.338), (0.2, 1.345), (0.55, 1.34), (0.85, 1.30), (1.0, 1.15), (1.12, 1.02), (1.24, 0.95),
        (1.36, 0.92), (1.46, 0.88), (YR, 0.82)],
    zs=[(YF, 0.64), (-1.0, 0.68), (-0.85, 0.74), (-0.6, 0.82), (0.9, 0.84), (1.2, 0.80), (YR, 0.72)],
    hw=[(YF, 0.665), (-1.2, HW), (1.2, HW), (YR, 0.675)],
    tw=[(YF, 0.58), (-1.1, 0.59), (-0.75, 0.60), (-0.35, 0.575), (0.5, 0.57), (1.0, 0.585), (1.3, 0.60), (YR, 0.59)],
    bw=0.93,
    rt=[(YF, 0.08), (-0.9, 0.08), (-0.6, 0.08), (1.1, 0.08), (1.3, 0.10), (YR, 0.10)],
    rs=0.10, rb=0.05,
)
body = L.loft_body(keys, YF, YR, 0.04, 0.045, step=0.04, k=4)

# wheel arches
R_ARCH = R_W + 0.045
hubs_cut = [(s, y, R_W) for s in (1, -1) for y in (-WB / 2, WB / 2)]
cut = L.wheel_cutter(hubs_cut, R_ARCH, 0.40, 1.3)
body = L.boolean_cut(body, cut)
car.set_bm('body', body.copy(), 'Paint')
surf = body
SF = L.Surf(body)
for s_ in (1, -1):
    for y_ in (-WB / 2, WB / 2):
        L.flare_lip(car, SF, s_, y_, R_W, R_ARCH, depth=0.016, width=0.03)

# ---------------------------------------------------------------- arch liners (trim)
for s in (1, -1):
    for y in (-WB / 2, WB / 2):
        L.arch_liner(car, 'trim', 'Trim', s, y, R_W, R_ARCH - 0.004, 0.405, 0.655, 0.215)

# ---------------------------------------------------------------- glass (windows are real openings)
wins = []


def win(pts, frame):
    wins.append((pts, frame))
    car.decal('glass', 'Glass', surf, pts, frame, 0.001)


win([(-0.47, 0.905), (0.47, 0.905), (0.455, 1.285), (-0.455, 1.285)], L.front(0.3))
win([(-0.46, 0.99), (0.46, 0.99), (0.45, 1.255), (-0.45, 1.255)], L.rear(0.7))
for s in (1, -1):
    door = [(-0.67, 0.895), (-0.37, 1.275), (-0.29, 1.30), (0.12, 1.30), (0.14, 1.27), (0.14, 0.895)]
    quarter = [(0.26, 0.895), (0.26, 1.29), (0.84, 1.295), (0.95, 1.22), (1.10, 1.04), (1.23, 0.935), (1.23, 0.895)]
    win(door, L.side(s))
    win(quarter, L.side(s))
    # door shut lines + handle
    car.strip('trim', 'Trim', surf, [(-0.725, 0.24), (-0.725, 0.85)], 0.006, L.side(s), 0.004)
    car.strip('trim', 'Trim', surf, [(0.20, 0.24), (0.20, 0.9)], 0.006, L.side(s), 0.004)
    car.strip('trim', 'Trim', surf, [(-0.725, 0.24), (0.20, 0.24)], 0.006, L.side(s), 0.004)
    car.decal('trim', 'Chrome', surf, L.rrect_pts(0.06, 0.79, 0.075, 0.022, 0.008), L.side(s), 0.012, 1)
    # thin chrome belt moulding
    car.strip('trim', 'Chrome', surf, [(-0.62, 0.855), (1.0, 0.86)], 0.009, L.side(s), 0.004)

# ---------------------------------------------------------------- front face
for sx in (1, -1):
    x = sx * 0.455
    car.decal('trim', 'Chrome', surf, L.circle_pts(x, 0.60, 0.082, n=24), L.front(-1.3), 0.004, 2)
    car.decal('trim', 'Trim', surf, L.circle_pts(x, 0.60, 0.072, n=24), L.front(-1.3), 0.007, 2)
    car.decal('lights', 'HeadLight', surf, L.circle_pts(x, 0.60, 0.064, n=24), L.front(-1.3), 0.010, 2)
    # indicator below
    car.decal('trim', 'Chrome', surf, L.rrect_pts(sx * 0.52, 0.47, 0.07, 0.035, 0.012), L.front(-1.3), 0.005, 1)
car.decal('trim', 'Chrome', surf, L.rrect_pts(0, 0.64, 0.40, 0.085, 0.02), L.front(-1.3), 0.004, 2)
car.decal('trim', 'Trim', surf, L.rrect_pts(0, 0.64, 0.38, 0.065, 0.015), L.front(-1.3), 0.007, 2)
for dz in (-0.018, 0.0, 0.018):
    car.strip('trim', 'Chrome', surf, [(-0.17, 0.64 + dz), (0.17, 0.64 + dz)], 0.007, L.front(-1.3), 0.010, 0.05)
car.decal('trim', 'Chrome', surf, L.circle_pts(0, 0.725, 0.028, n=16), L.front(-1.3), 0.005, 1)   # badge
car.decal('trim', 'Plate', surf, L.rrect_pts(0, 0.455, 0.52, 0.11, 0.008), L.front(-1.3), 0.005, 2)
car.decal('trim', 'Trim', surf, L.rrect_pts(0, 0.455, 0.50, 0.09, 0.006), L.front(-1.3), 0.0058, 1)  # border-ish
car.decal('trim', 'Plate', surf, L.rrect_pts(0, 0.455, 0.49, 0.082, 0.005), L.front(-1.3), 0.0066, 2)

# ---------------------------------------------------------------- rear face
for sx in (1, -1):
    x = sx * 0.50
    car.decal('trim', 'Chrome', surf, L.rrect_pts(x, 0.66, 0.15, 0.10, 0.04), L.rear(1.45), 0.004, 2)
    car.decal('lights', 'TailLight', surf, L.rrect_pts(x, 0.66, 0.135, 0.085, 0.035), L.rear(1.45), 0.008, 2)
car.decal('trim', 'Trim', surf, L.rrect_pts(0, 0.635, 0.62, 0.16, 0.02), L.rear(1.45), 0.005, 3)
for i in range(6):
    z = 0.575 + i * 0.03
    car.strip('body', 'Paint', surf, [(-0.28, z), (0.28, z)], 0.011, L.rear(1.45), 0.0085, 0.05)
car.decal('trim', 'Plate', surf, L.rrect_pts(0, 0.43, 0.52, 0.11, 0.008), L.rear(1.45), 0.005, 2)
car.decal('trim', 'Chrome', surf, L.circle_pts(0.30, 0.43, 0.012, n=8), L.rear(1.45), 0.005, 0)
# louvres on the engine lid (sloping part)
car.decal('trim', 'Trim', surf, L.rrect_pts(0, 1.37, 0.62, 0.15, 0.02), L.top(0.6), 0.004, 3)
for i in range(4):
    y = 1.325 + i * 0.033
    car.strip('body', 'Paint', surf, [(-0.27, y), (0.27, y)], 0.012, L.top(0.6), 0.0075, 0.05)

# ---------------------------------------------------------------- bumpers (chrome, thin)
bsec = [(-0.006, -0.026), (0.014, -0.030), (0.030, -0.018), (0.032, 0.0), (0.030, 0.018), (0.014, 0.030), (-0.006, 0.026)]
# front: ends curl back toward +y (into the car)
fp = []
half, wrap, tb = 0.52, 0.10, 0.11
for i in range(-6, 7):
    fp.append((i / 6 * half, YF + 0.002, 0.305))
for side in (1, -1):
    seg = []
    for j in range(1, 7):
        a = math.radians(90 * j / 6)
        seg.append((side * (half + wrap * math.sin(a)), YF + 0.002 + tb * (1 - math.cos(a)), 0.305))
    fp = fp + seg if side == 1 else list(reversed(seg)) + fp
car.sweep('trim', 'Chrome', fp, bsec, (0, -1, 0))
rp = []
for i in range(-6, 7):
    rp.append((i / 6 * half, YR - 0.002, 0.335))
for side in (1, -1):
    seg = []
    for j in range(1, 7):
        a = math.radians(90 * j / 6)
        seg.append((side * (half + wrap * math.sin(a)), YR - 0.002 - tb * (1 - math.cos(a)), 0.335))
    rp = rp + seg if side == 1 else list(reversed(seg)) + rp
car.sweep('trim', 'Chrome', rp, bsec, (0, 1, 0))

# ---------------------------------------------------------------- interior (windows are open, so it is visible)
L.cut_openings(car.objs['body'][0], wins)
shell = L.interior_shell(keys, -0.70, 1.08, 0.30, 0.04, wins, cutter=L.wheel_cutter(hubs_cut, R_ARCH + 0.01, 0.40, 1.3))
car.add_bm('interior', 'Interior', shell)
L.furnish(car, dict(dside=+1, sx=0.28, floor=0.30, dash=(-0.70, 0.27, 0.82, 0.60), wheel=(-0.42, 0.82, 0.20, 0.75),
                    seat=(-0.05, 0.46), rear=(0.62, 0.86, 0.98, 0.36), shelf=(1.02, 0.88, 0.22, 0.90)))

# ---------------------------------------------------------------- wheels
objs_hub = {}
for nm, sx, sy in (('wheel_fl', +1, -1), ('wheel_fr', -1, -1), ('wheel_rl', +1, +1), ('wheel_rr', -1, +1)):
    L.build_wheel(car, nm, sx, R_W, W_T, 0.1524, 'steel', seg=28)
    objs_hub[nm] = (sx * TRACK / 2, sy * WB / 2, R_W)

objs = car.build_objects()
for nm, p in objs_hub.items():
    objs[nm].location = Vector(p)

print('TRIANGLES', L.tri_count(objs))
L.export_glb(os.path.join(L.CARS_OUT, 'fiat126.glb'))
print('exported fiat126')
