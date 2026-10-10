"""Subaru Impreza 22B STI (1998, two-door coupe, widebody). L4.37 W1.77 H1.39 WB2.52 wheel R0.32.
Default Paint: WR Blue Mica.  Run: blender -b --python impreza.py
Signature cues: bulging flared front/rear fenders over a narrower door section; big bonnet scoop with
black intake + bonnet vents; 2-door coupe roofline with long doors and a sloping C-pillar; tall GT rear wing
on two struts with endplates; gold 5-spoke wheels in tight arches; twin round multi-reflector headlights
with a big black lower bumper intake and round fog lamps; low rally-car stance.
"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import small_cars_lib as L
importlib.reload(L)
from mathutils import Vector, Matrix

L.reset_scene()
WB, R_W, W_T, R_RIM = 2.52, 0.32, 0.235, 0.2159
TRACK_F, TRACK_R = 1.48, 1.50
YF, YR = -(WB / 2 + 0.89), WB / 2 + 0.935          # -2.15 .. 2.195 (decals add ~1cm each end) => L = 4.365

car = L.Car()
car.mats = L.standard_materials('#1d3f8f', rim='#c9a227', rim_metal=0.9, rim_rough=0.28, plate='#efe9d2')

keys = dict(
    zb=[(YF, 0.15), (-1.9, 0.125), (1.9, 0.125), (YR, 0.15)],
    zt=[(YF, 0.70), (-2.0, 0.715), (-1.6, 0.745), (-1.2, 0.815), (-0.95, 0.875), (-0.80, 0.925),
        (-0.55, 1.05), (-0.30, 1.205), (-0.12, 1.31), (0.05, 1.368), (0.25, 1.388), (0.55, 1.390),
        (0.80, 1.378), (1.05, 1.335), (1.20, 1.25), (1.35, 1.14), (1.50, 1.04), (1.60, 1.005),
        (1.80, 0.995), (2.0, 0.99), (YR, 0.975)],
    zs=[(YF, 0.58), (-1.6, 0.66), (-1.2, 0.72), (-0.95, 0.80), (-0.7, 0.90), (-0.4, 0.935),
        (1.3, 0.945), (1.7, 0.95), (YR, 0.89)],
    hw=[(YF, 0.80), (-1.9, 0.855), (-1.5, 0.885), (-1.26, 0.888), (-0.95, 0.86), (-0.6, 0.84), (0.6, 0.84),
        (0.95, 0.86), (1.26, 0.888), (1.6, 0.885), (2.0, 0.86), (YR, 0.82)],
    tw=[(YF, 0.64), (-1.8, 0.69), (-1.2, 0.73), (-0.9, 0.72), (-0.6, 0.66), (-0.2, 0.60), (0.3, 0.58),
        (1.0, 0.58), (1.5, 0.63), (1.8, 0.69), (YR, 0.70)],
    bw=0.95,
    rt=[(YF, 0.15), (-0.9, 0.16), (-0.6, 0.10), (1.3, 0.10), (1.6, 0.14), (YR, 0.14)],
    rs=0.09, rb=0.05,
)
body = L.loft_body(keys, YF, YR, 0.10, 0.08, step=0.06, k=4)

R_ARCH = R_W + 0.04
hubs_cut = [(s, y, R_W) for s in (1, -1) for y in (-WB / 2, WB / 2)]
body = L.boolean_cut(body, L.wheel_cutter(hubs_cut, R_ARCH, 0.54, 1.3, seg=56))
car.set_bm('body', body.copy(), 'Paint')
S = body
SF = L.Surf(body)

for s in (1, -1):
    for y in (-WB / 2, WB / 2):
        L.arch_liner(car, 'trim', 'Trim', s, y, R_W, R_ARCH - 0.004, 0.545, 0.79, 0.17, seg=32)

# ---------------------------------------------------------------- flared arch lips (the 22B's blister fenders)
def flare_lip(sx, cy, cz, R0, depth=0.03, a0=14, a1=166, n=22):
    rings = []
    for i in range(n + 1):
        th = math.radians(a0 + (a1 - a0) * i / n)
        c, sn = math.cos(th), math.sin(th)
        pts = []
        # section: (rho offset from arch edge, x offset from the surface)
        for rho, dx in ((-0.004, -0.012), (-0.004, depth), (0.020, depth * 0.85), (0.046, 0.0), (0.046, -0.012)):
            r = R0 + rho
            y, z = cy + r * c, cz + r * sn
            # surface x at the lip's outer edge (use a reference radius just outside the arch)
            rr = R0 + 0.046
            xs = SF.surf_x(sx, cy + rr * c, cz + rr * sn)
            if xs is None:
                xs = 0.87
            pts.append(Vector((sx * (xs + dx), y, z)))
        rings.append(pts)
    L.loft_rings(car, 'body', 'Paint', rings)


for sx in (1, -1):
    for y in (-WB / 2, WB / 2):
        flare_lip(sx, y, R_W, R_ARCH)

# ---------------------------------------------------------------- glass
car.decal('glass', 'Glass', S, [(-0.66, 0.97), (0.66, 0.97), (0.56, 1.35), (-0.56, 1.35)], L.front(0.0), 0.004)
car.decal('glass', 'Glass', S, [(-0.52, 1.045), (0.52, 1.045), (0.45, 1.285), (-0.45, 1.285)], L.rear(0.9), 0.004)
for s in (1, -1):
    door = [(-0.60, 0.975), (-0.12, 1.352), (0.0, 1.362), (0.42, 1.362), (0.60, 1.31), (0.64, 0.975)]
    quarter = [(0.74, 0.975), (0.72, 1.30), (0.93, 1.28), (1.12, 1.19), (1.25, 1.07), (1.33, 0.975)]
    car.decal('glass', 'Glass', S, door, L.side(s, 0.5), 0.004)
    car.decal('glass', 'Glass', S, quarter, L.side(s, 0.5), 0.004)
    # shut lines
    car.strip('trim', 'Trim', S, [(-0.62, 0.22), (-0.64, 0.93)], 0.006, L.side(s), 0.004)
    car.strip('trim', 'Trim', S, [(0.70, 0.22), (0.68, 0.96)], 0.006, L.side(s), 0.004)
    car.strip('trim', 'Trim', S, [(-0.62, 0.22), (0.70, 0.22)], 0.006, L.side(s), 0.004)
    # chrome beltline + door handle + sill trim
    car.strip('trim', 'Chrome', S, [(-0.55, 0.965), (1.35, 0.965)], 0.008, L.side(s), 0.0045)
    car.decal('trim', 'Trim', S, L.rrect_pts(0.50, 0.89, 0.11, 0.028, 0.012), L.side(s), 0.008)
    car.strip('trim', 'Trim', S, [(-0.85, 0.20), (0.95, 0.20)], 0.04, L.side(s), 0.004)
    # side vents behind front arch (fender gill)
    for i in range(3):
        car.strip('trim', 'Trim', S, [(-0.84 + i * 0.045, 0.60), (-0.80 + i * 0.045, 0.72)], 0.012, L.side(s, 0.7), 0.004)

# ---------------------------------------------------------------- nose / front
FR = L.front(-1.85)
for sx in (1, -1):
    housing = [(sx * a, b) for a, b in [(0.30, 0.52), (0.32, 0.66), (0.55, 0.715), (0.84, 0.725), (0.88, 0.64), (0.83, 0.54), (0.50, 0.50)]]
    car.decal('trim', 'Trim', S, housing, FR, 0.004)
    car.decal('trim', 'Chrome', S, [(sx * a, b) for a, b in [(0.335, 0.535), (0.35, 0.65), (0.55, 0.702), (0.83, 0.712), (0.862, 0.64), (0.815, 0.552), (0.50, 0.517)]], FR, 0.006)
    for cx_, cz_ in ((0.50, 0.615), (0.72, 0.625)):
        car.decal('trim', 'Trim', S, L.circle_pts(sx * cx_, cz_, 0.060, n=20), FR, 0.008)
        car.decal('lights', 'HeadLight', S, L.circle_pts(sx * cx_, cz_, 0.048, n=18), FR, 0.010)
        car.decal('trim', 'Chrome', S, L.circle_pts(sx * cx_, cz_, 0.020, n=12), FR, 0.010)
    # side lamp wrapping the fender
    car.decal('trim', 'Chrome', S, [(-2.15, 0.56), (-2.15, 0.68), (-2.02, 0.715), (-1.90, 0.70), (-1.88, 0.60)], L.side(sx, 0.82), 0.006)
    # fog lamps in the bumper
    car.decal('trim', 'Chrome', S, L.circle_pts(sx * 0.60, 0.31, 0.058, n=20), FR, 0.004)
    car.decal('lights', 'HeadLight', S, L.circle_pts(sx * 0.60, 0.31, 0.046, n=18), FR, 0.007)
    car.decal('trim', 'Trim', S, L.rrect_pts(sx * 0.80, 0.30, 0.10, 0.12, 0.03), FR, 0.004)    # corner intake
car.decal('trim', 'Trim', S, L.rrect_pts(0, 0.585, 0.40, 0.075, 0.02), FR, 0.004)             # grille
car.decal('trim', 'Chrome', S, L.rrect_pts(0, 0.585, 0.40, 0.012, 0.004), FR, 0.007)
car.decal('trim', 'Chrome', S, L.circle_pts(0, 0.585, 0.026, n=14), FR, 0.008)
car.decal('trim', 'Trim', S, L.rrect_pts(0, 0.255, 0.70, 0.105, 0.03), FR, 0.004)             # lower intake
for i in range(3):
    car.strip('trim', 'Chrome', S, [(-0.30, 0.225 + i * 0.03), (0.30, 0.225 + i * 0.03)], 0.006, FR, 0.007)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.405, 0.52, 0.11, 0.008), FR, 0.004)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.405, 0.505, 0.097, 0.006), FR, 0.0055)

# ---------------------------------------------------------------- bonnet: scoop, vents, seams
y_f, y_r = -1.66, -1.02
rings = []
n_rows = 12
for j in range(n_rows + 1):
    t = j / n_rows
    y = y_f + (y_r - y_f) * t
    w = 0.275 * (1 - 0.10 * t)
    h = max(0.078 * (1 - t ** 1.7), 0.005)
    top, base = [], []
    na = 14
    for i in range(na + 1):
        a = math.pi - math.pi * i / na
        x = w * math.cos(a)
        zh = SF.top_z(x, y)
        top.append(Vector((x, y, zh + h * (max(math.sin(a), 0.0) ** 0.5))))
    for i in range(1, 6):
        x = w - 2 * w * i / 6
        zh = SF.top_z(x, y)
        base.append(Vector((x, y, zh - 0.012)))
    rings.append(top + base)
L.loft_rings(car, 'body', 'Paint', rings)
# intake opening (black) on the front wall of the scoop
r0 = rings[0]
cen = sum(r0, Vector()) / len(r0)
verts = [tuple(cen + (p - cen) * 0.80 + Vector((0, -0.004, 0.0))) for p in r0]
car.add('trim', 'Trim', verts, [list(range(len(verts)))])
for sx in (1, -1):
    for dx in (0.44, 0.52):
        car.strip('trim', 'Trim', S, [(sx * dx, -1.50), (sx * dx, -1.10)], 0.028, L.top(0.5), 0.004)
car.strip('trim', 'Trim', S, [(-0.70, -0.85), (0.70, -0.85)], 0.005, L.top(0.5), 0.004)

# ---------------------------------------------------------------- tail
RR = L.rear(1.9)
for sx in (1, -1):
    car.decal('trim', 'Chrome', S, L.rrect_pts(sx * 0.62, 0.80, 0.44, 0.14, 0.03), RR, 0.004)
    car.decal('lights', 'TailLight', S, L.rrect_pts(sx * 0.62, 0.80, 0.425, 0.125, 0.028), RR, 0.007)
    car.decal('trim', 'Trim', S, L.rrect_pts(sx * 0.62, 0.80, 0.03, 0.12, 0.01), RR, 0.010)
    car.decal('lights', 'TailLight', S, [(2.205, 0.75), (2.205, 0.86), (2.10, 0.88), (1.98, 0.85), (1.96, 0.76)], L.side(sx, 0.78), 0.007)
car.decal('trim', 'Trim', S, L.rrect_pts(0, 0.30, 1.22, 0.16, 0.04), RR, 0.004)              # rear valance
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.62, 0.52, 0.11, 0.008), RR, 0.004)
car.decal('trim', 'Plate', S, L.rrect_pts(0, 0.62, 0.505, 0.097, 0.006), RR, 0.0055)
car.decal('trim', 'Chrome', S, L.circle_pts(-0.46, 0.27, 0.055, n=18), RR, 0.007)
car.decal('trim', 'Trim', S, L.circle_pts(-0.46, 0.27, 0.040, n=16), RR, 0.010)
car.strip('trim', 'Trim', S, [(-0.84, 0.935), (0.84, 0.935)], 0.005, RR, 0.004)            # boot seam

# ---------------------------------------------------------------- GT wing
yc, zc, ang = 1.985, 1.325, math.radians(9)
blade = [(-0.17, 0.0), (-0.14, -0.017), (0.0, -0.024), (0.13, -0.014), (0.17, 0.0), (0.13, 0.017), (0.0, 0.024), (-0.14, 0.015)]
poly = [(yc + u * math.cos(ang) - w * math.sin(ang), zc + u * math.sin(ang) + w * math.cos(ang)) for u, w in blade]
v, f = L.prism(poly, -0.74, 0.74)
car.add('spoiler', 'Paint', v, f)
for sx in (1, -1):
    ep = [(yc - 0.20, zc - 0.075), (yc + 0.20, zc - 0.045), (yc + 0.20, zc + 0.065), (yc - 0.18, zc + 0.035)]
    v, f = L.prism(ep, sx * 0.738, sx * 0.752)
    car.add('spoiler', 'Paint', v, f)
    st = [(1.945, 0.97), (2.04, 0.97), (2.005, zc - 0.015), (1.975, zc - 0.015)]
    v, f = L.prism(st, sx * 0.44, sx * 0.47)
    car.add('spoiler', 'Trim', v, f)

# ---------------------------------------------------------------- mirrors (body colour)
for sx in (1, -1):
    car.ellipsoid('mirrors', 'Paint', (sx * 0.945, -0.60, 1.03), (0.035, 0.085, 0.055), 12, 8)
    car.box('mirrors', 'Paint', (sx * 0.855, -0.62, 1.00), (0.17, 0.05, 0.022), 0.008)
    car.ellipsoid('mirrors', 'Chrome', (sx * 0.9795, -0.60, 1.03), (0.004, 0.07, 0.043), 10, 6)

# ---------------------------------------------------------------- interior
car.box('interior', 'Interior', (0, 0.1, 0.30), (1.4, 2.4, 0.02))
for sx in (-0.34, 0.34):
    car.box('interior', 'Interior', (sx, 0.0, 0.50), (0.48, 0.55, 0.14), 0.03)
    car.box('interior', 'Interior', (sx, 0.22, 0.82), (0.48, 0.12, 0.62), 0.03)
car.box('interior', 'Interior', (0, 0.95, 0.60), (1.3, 0.5, 0.16), 0.03)
car.box('interior', 'Interior', (0, 1.15, 0.90), (1.3, 0.10, 0.4), 0.03)
car.box('interior', 'Interior', (0, -0.50, 0.80), (1.4, 0.28, 0.12), 0.03)
car.box('interior', 'Interior', (-0.34, -0.30, 0.88), (0.32, 0.025, 0.32), 0.01, rot=Matrix.Rotation(0.5, 4, 'X'))

# ---------------------------------------------------------------- wheels
hubs = {}
for nm, sx, sy, tr in (('wheel_fl', +1, -1, TRACK_F), ('wheel_fr', -1, -1, TRACK_F),
                       ('wheel_rl', +1, +1, TRACK_R), ('wheel_rr', -1, +1, TRACK_R)):
    L.build_wheel(car, nm, sx, R_W, W_T, R_RIM, 'alloy', seg=32, spokes=5)
    hubs[nm] = (sx * tr / 2, sy * WB / 2, R_W)

objs = car.build_objects()
for nm, p in hubs.items():
    objs[nm].location = Vector(p)
print('TRIANGLES', L.tri_count(objs))
L.export_glb(os.path.join(L.CARS_OUT, 'impreza.glb'))
print('exported impreza')
