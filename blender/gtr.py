"""Nissan Skyline GT-R R34 V-spec. Run: blender -b --python gtr.py"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carlib import *
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
M = make_materials('#5b86c4', rim='#c9ccd2')   # Bayside-blue-ish silver blue

L, W, H, WB, WR = 4.60, 1.79, 1.36, 2.67, 0.33
YF, YR = -1.335, 1.335          # axle positions
TRK = 0.745                     # wheel centre x
ARCH_R = 0.392

# --------------------------------------------------------------- body loft
# y, hw, zb, zc, zt, nu, nl, k, kb
ST = [
    (-2.300, 0.66, 0.20, 0.50, 0.63, 3.0, 3.0, 0.95, 0.92),
    (-2.275, 0.78, 0.13, 0.52, 0.69, 3.0, 3.5, 0.95, 0.92),
    (-2.200, 0.855, 0.12, 0.60, 0.735, 3.0, 4.0, 0.95, 0.93),
    (-2.000, 0.885, 0.13, 0.70, 0.78, 3.2, 4.5, 0.95, 0.93),
    (-1.500, 0.895, 0.15, 0.80, 0.865, 3.4, 5.0, 0.94, 0.93),
    (-0.950, 0.890, 0.17, 0.86, 0.925, 3.4, 5.0, 0.93, 0.93),
    (-0.620, 0.885, 0.17, 0.88, 1.075, 3.0, 5.0, 0.84, 0.93),
    (-0.300, 0.880, 0.17, 0.89, 1.285, 3.2, 5.0, 0.77, 0.93),
    (-0.050, 0.875, 0.17, 0.90, 1.350, 3.3, 5.0, 0.74, 0.93),
    (0.700, 0.875, 0.17, 0.90, 1.360, 3.3, 5.0, 0.74, 0.93),
    (1.000, 0.882, 0.17, 0.92, 1.300, 3.2, 5.0, 0.76, 0.93),
    (1.400, 0.892, 0.18, 0.96, 1.120, 3.0, 5.0, 0.82, 0.93),
    (1.700, 0.8955, 0.20, 0.98, 1.055, 3.2, 5.0, 0.88, 0.93),
    (2.100, 0.893, 0.22, 0.985, 1.040, 3.5, 5.0, 0.92, 0.93),
    (2.255, 0.875, 0.25, 0.96, 1.030, 3.5, 4.5, 0.92, 0.93),
    (2.290, 0.80, 0.27, 0.92, 1.000, 3.2, 4.0, 0.92, 0.92),
    (2.300, 0.70, 0.32, 0.88, 0.96, 3.0, 3.0, 0.92, 0.92),
]


def gtr_face(cx, cy, cz, nx, ny, nz):
    ax = abs(cx)
    if cz > 1.0:
        if -0.80 < cy < -0.14 and nz > 0.25 and ny < -0.2 and ax < 0.66:
            return 'Glass'
        if 0.98 < cy < 1.55 and nz > 0.1 and ny > 0.15 and ax < 0.64:
            return 'Glass'
        if abs(nx) > 0.5:
            if -0.58 < cy < 0.28 or 0.46 < cy < 1.12:
                return 'Glass'
    return 'Paint'


body, at = loft_body('body', ST, 40, 0.05, gtr_face, 'body', extra_ys=(YF, YR))

# --------------------------------------------------------------- wheel arches (boolean)
cut = Mesh('cutter')
for sx in (1, -1):
    for y in (YF, YR):
        add_cyl(cut, (sx * 0.42, y, WR), (sx * 1.2, y, WR), ARCH_R, ARCH_R, 40, 'Trim')
cut.fix()
bo = body.to_obj(M, 'body_tmp')
co = cut.to_obj(M, 'cutter')
md = bo.modifiers.new('b', 'BOOLEAN')
md.object = co
md.operation = 'DIFFERENCE'
md.solver = 'EXACT'
try:
    md.material_mode = 'TRANSFER'
except Exception:
    pass
body = Mesh.from_obj(bo, 'body', 'body')
bpy.data.objects.remove(bo)
bpy.data.objects.remove(co)
print('slots after boolean', body.slots, 'tris', body.tris())

surf = Surf(body)
P = {}   # extra parts
def part(name, group=None):
    if name not in P:
        P[name] = Mesh(name, group or name)
    return P[name]

trim = part('trim')
lights = part('lights')

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gtr_details.py')).read()) \
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gtr_details.py')) else None

# --------------------------------------------------------------- wheels
def gtr_spokes(rin, xf):
    out = []
    for i in range(5):
        base = 2 * math.pi * i / 5 + 0.3
        for s in (-1, 1):
            out.append((0.055, rin, base + s * 0.12, base + s * 0.20, 0.034, 0.026, 0.024, 0.020, xf, xf + 0.05))
    return out


style = dict(x_face=0.045, spokes=gtr_spokes, hub_r=0.055, disc=(0.115, 0.19))
wheels = []
for nm, sx, y in (('wheel_fl', -1, YF), ('wheel_fr', 1, YF), ('wheel_rl', -1, YR), ('wheel_rr', 1, YR)):
    wm = build_wheel(nm, sx, WR, 0.245, 0.2286, style)
    smooth_edges(wm, 40)
    wo = wm.to_obj(M, nm)
    wo.location = (sx * TRK, y, WR)
    wheels.append(wo)

# --------------------------------------------------------------- finalize + export
parts = [body] + list(P.values())
dests = finalize(parts)
objs = []
tot = 0
for nm, d in dests.items():
    o = d.to_obj(M, nm)
    objs.append(o)
    tot += d.tris()
    print(nm, 'tris', d.tris())
objs += wheels
for w in wheels:
    tot += sum(len(p.vertices) - 2 for p in w.data.polygons)
print('TOTAL tris', tot)
glb = export_car('gtr', objs)
size = verify_and_render('gtr', glb)
