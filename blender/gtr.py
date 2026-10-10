"""Nissan Skyline GT-R R34 V-spec. Run: blender -b --python gtr.py"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carlib import *
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
M = make_materials('#5b86c4', rim='#a9aeb7')   # Bayside-blue-ish silver blue

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


body, at = loft_body('body', ST, 40, 0.05, lambda *a: 'Paint', 'body', extra_ys=(YF, YR))

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

# --------------------------------------------------------------- details (conformal patches)
body_extra = part('body_extra', 'body')
glass = part('glass')
spoiler = part('spoiler')
mirrors = part('mirrors')

# glass
sym(glass, surf, 'S', quad_grid([(-0.62, 0.995), (0.50, 0.995), (0.46, 1.305), (-0.20, 1.305)], 28, 8), 'Glass', lift=0.006, sdepth=0.02)
sym(glass, surf, 'S', quad_grid([(0.64, 0.995), (1.22, 1.005), (1.00, 1.19), (0.64, 1.305)], 14, 6), 'Glass', lift=0.006, sdepth=0.02)
patch(glass, surf, 'F', quad_grid([(-0.70, 0.985), (0.70, 0.985), (0.585, 1.30), (-0.585, 1.30)], 28, 12), 'Glass', lift=0.006, sdepth=0.02)
patch(glass, surf, 'R', quad_grid([(-0.66, 1.075), (0.66, 1.075), (0.58, 1.285), (-0.58, 1.285)], 26, 10), 'Glass', lift=0.006, sdepth=0.02)

# panel lines (door, bonnet, boot)
door = [(-0.78, 0.97), (-0.80, 0.90), (-0.80, 0.30), (-0.77, 0.27), (0.53, 0.27), (0.56, 0.30), (0.56, 0.96)]
sym(trim, surf, 'S', ribbon_grid(door, 0.007, 0.03), 'Trim', lift=0.002, skirt=False)
sym(trim, surf, 'S', ribbon_grid([(-0.95, 0.80), (-0.82, 0.90)], 0.007, 0.03), 'Trim', lift=0.002, skirt=False)
# sill strip
sym(trim, surf, 'S', quad_grid([(-0.70, 0.19), (0.50, 0.19), (0.50, 0.25), (-0.70, 0.25)], 20, 1), 'Trim', lift=0.006)
# bonnet shut lines + boot line (from above)
for sx in (1, -1):
    patch(trim, surf, 'T', ribbon_grid([(sx * 0.84, -1.95), (sx * 0.80, -1.45), (sx * 0.78, -0.95)], 0.006, 0.05), 'Trim', lift=0.002, skirt=False)
patch(trim, surf, 'T', ribbon_grid([(-0.80, -0.95), (0.0, -0.93), (0.80, -0.95)], 0.006, 0.05), 'Trim', lift=0.002, skirt=False)
patch(trim, surf, 'T', ribbon_grid([(-0.78, 1.70), (0.0, 1.69), (0.78, 1.70)], 0.006, 0.05), 'Trim', lift=0.002, skirt=False)

# bonnet NACA ducts + heat vents (V-spec II carbon bonnet)
for sx in (1, -1):
    c = [(sx * 0.37 - 0.03, -1.55), (sx * 0.37 + 0.03, -1.55), (sx * 0.37 + 0.13, -1.12), (sx * 0.37 - 0.13, -1.12)]
    patch(trim, surf, 'T', quad_grid(c, 4, 8), 'Trim', lift=0.004)
    for k in range(5):
        y0 = -1.06 + k * 0.045
        patch(trim, surf, 'T', quad_grid([(sx * 0.58, y0), (sx * 0.78, y0 + 0.02), (sx * 0.78, y0 + 0.035), (sx * 0.58, y0 + 0.015)], 6, 1), 'Trim', lift=0.003, skirt=False)

# front fascia
for sx in (1, -1):
    hl = [(sx * 0.46, 0.625), (sx * 0.86, 0.640), (sx * 0.86, 0.765), (sx * 0.46, 0.745)]
    if sx < 0:
        hl = [hl[1], hl[0], hl[3], hl[2]]
    patch(trim, surf, 'F', quad_grid(hl, 10, 4), 'Trim', lift=0.003)               # bezel
    hl2 = [(sx * 0.475, 0.640), (sx * 0.845, 0.652), (sx * 0.845, 0.752), (sx * 0.475, 0.735)]
    if sx < 0:
        hl2 = [hl2[1], hl2[0], hl2[3], hl2[2]]
    patch(lights, surf, 'F', quad_grid(hl2, 10, 4, 0.1), 'HeadLight', lift=0.007)
    for cxx in (0.57, 0.73):                                                          # round projector lamps
        patch(trim, surf, 'F', ellipse_grid(sx * cxx, 0.695, 0.052, 0.046, 3, 18), 'Chrome', lift=0.011)
        patch(trim, surf, 'F', ellipse_grid(sx * cxx, 0.695, 0.034, 0.030, 2, 16), 'Trim', lift=0.013)
    # side marker / indicator
    patch(lights, surf, 'F', quad_grid([(sx * 0.80, 0.585), (sx * 0.86, 0.585), (sx * 0.86, 0.62), (sx * 0.80, 0.62)] if sx > 0 else [(sx * 0.86, 0.585), (sx * 0.80, 0.585), (sx * 0.80, 0.62), (sx * 0.86, 0.62)], 3, 2), 'HeadLight', lift=0.006)
    # round fog / intercooler openings in the lower bumper
    patch(trim, surf, 'F', ellipse_grid(sx * 0.70, 0.30, 0.125, 0.085, 3, 22), 'Chrome', lift=0.006)
    patch(trim, surf, 'F', ellipse_grid(sx * 0.70, 0.30, 0.105, 0.068, 3, 22), 'Trim', lift=0.009)
    patch(lights, surf, 'F', ellipse_grid(sx * 0.70, 0.30, 0.04, 0.04, 2, 14), 'HeadLight', lift=0.011)
patch(trim, surf, 'F', quad_grid([(-0.50, 0.17), (0.50, 0.17), (0.54, 0.45), (-0.54, 0.45)], 18, 5), 'Trim', lift=0.005)   # wide lower intake
for k in range(3):
    zz = 0.24 + k * 0.08
    patch(trim, surf, 'F', quad_grid([(-0.50, zz), (0.50, zz), (0.50, zz + 0.012), (-0.50, zz + 0.012)], 16, 1), 'Chrome', lift=0.008, skirt=False)
patch(trim, surf, 'F', quad_grid([(-0.46, 0.545), (0.46, 0.545), (0.46, 0.615), (-0.46, 0.615)], 16, 2), 'Trim', lift=0.004)  # upper grille
patch(trim, surf, 'F', quad_grid([(-0.26, 0.10), (0.26, 0.10), (0.26, 0.15), (-0.26, 0.15)], 6, 1), 'Plate', lift=0.012) if False else None
patch(trim, surf, 'F', quad_grid([(-0.26, 0.32), (0.26, 0.32), (0.26, 0.43), (-0.26, 0.43)], 8, 2), 'Plate', lift=0.012)  # front plate
add_box(trim, (0, -2.30, 0.12), (1.40, 0.06, 0.02), 'Trim')            # splitter lip

# rear
for sx in (1, -1):
    for cxx, rr in ((0.66, 0.088), (0.465, 0.074)):
        patch(trim, surf, 'R', ellipse_grid(sx * cxx, 0.80, rr * 1.12, rr * 1.12, 2, 22, 0.0), 'Chrome', lift=0.006)
        patch(lights, surf, 'R', ellipse_grid(sx * cxx, 0.80, rr, rr, 3, 22), 'TailLight', lift=0.012, crown=0.5)
    patch(lights, surf, 'R', ellipse_grid(sx * 0.465, 0.80, 0.03, 0.03, 2, 14), 'HeadLight', lift=0.016) if False else None
patch(trim, surf, 'R', quad_grid([(-0.42, 0.74), (0.42, 0.74), (0.42, 0.865), (-0.42, 0.865)], 14, 2), 'Trim', lift=0.004)   # tail garnish
patch(trim, surf, 'R', quad_grid([(-0.26, 0.45), (0.26, 0.45), (0.26, 0.56), (-0.26, 0.56)], 8, 2), 'Plate', lift=0.01)      # rear plate
patch(trim, surf, 'R', quad_grid([(-0.62, 0.30), (0.62, 0.30), (0.66, 0.40), (-0.66, 0.40)], 14, 2), 'Trim', lift=0.004)   # lower valance
for sx in (1, -1):                                                     # twin exhausts
    add_cyl(trim, (sx * 0.36, 2.18, 0.285), (sx * 0.36, 2.355, 0.285), 0.052, 0.052, 18, 'Chrome')
    add_cyl(trim, (sx * 0.36, 2.34, 0.285), (sx * 0.36, 2.357, 0.285), 0.040, 0.040, 18, 'Trim')
# diffuser
dif = [m for m in ()]
add_hex(trim, [(-0.62, 2.12, 0.20), (0.62, 2.12, 0.20), (0.62, 2.30, 0.20), (-0.62, 2.30, 0.20),
               (-0.62, 2.12, 0.225), (0.62, 2.12, 0.225), (0.62, 2.34, 0.25), (-0.62, 2.34, 0.25)], 'Trim')
for k in range(-3, 4):
    add_box(trim, (k * 0.17, 2.255, 0.255), (0.015, 0.15, 0.075), 'Trim')

# fender flares (arch lips)
for y in (YF, YR):
    sym(body_extra, surf, 'S', arc_band(y, WR, ARCH_R + 0.002, ARCH_R + 0.055, -100, 100, 36), 'Paint', lift=0.016)

# door handles, fuel flap, badges
sym(trim, surf, 'S', quad_grid([(0.12, 0.90), (0.27, 0.90), (0.27, 0.925), (0.12, 0.925)], 4, 1), 'Trim', lift=0.008)
sym(trim, surf, 'S', quad_grid([(1.35, 0.93), (1.50, 0.93), (1.50, 0.99), (1.35, 0.99)], 4, 1), 'Trim', lift=0.002, skirt=False) if False else None

# mirrors
for sx in (1, -1):
    base = Vector((sx * 0.76, -0.52, 1.00))
    add_box(mirrors, (sx * 0.79, -0.50, 1.02), (0.10, 0.07, 0.05), 'Paint')
    add_hex(mirrors, [(sx * 0.82, -0.40, 1.00), (sx * 1.00, -0.40, 1.00), (sx * 1.00, -0.62, 1.00), (sx * 0.82, -0.60, 1.00),
                      (sx * 0.83, -0.40, 1.12), (sx * 0.99, -0.41, 1.12), (sx * 0.99, -0.59, 1.12), (sx * 0.83, -0.58, 1.12)], 'Paint')
    mirrors.fix()
    add_box(mirrors, (sx * 0.915, -0.395, 1.06), (0.15, 0.012, 0.09), 'Trim')

# rear wing (V-spec adjustable GT wing on twin uprights)
WING_Y, WING_Z = 2.00, 1.255
prof = [(-0.15, -0.015), (-0.10, 0.02), (0.0, 0.035), (0.10, 0.02), (0.17, 0.0), (0.15, -0.012), (0.0, -0.01), (-0.12, -0.02)]
add_prism(spoiler, [(WING_Y + a, WING_Z + b) for a, b in prof], 'YZ', -0.72, 0.72, 'Paint')
for sx in (1, -1):
    add_prism(spoiler, [(WING_Y - 0.16 + a, WING_Z - 0.035 + b) for a, b in ((0, 0), (0.34, 0), (0.34, 0.09), (0.22, 0.09), (0.10, 0.07), (0, 0.04))], 'YZ', sx * 0.72, sx * 0.735, 'Paint')
    add_prism(spoiler, [(WING_Y - 0.03, 1.02), (WING_Y + 0.03, 1.02), (WING_Y + 0.025, WING_Z - 0.01), (WING_Y - 0.035, WING_Z - 0.01)], 'YZ', sx * 0.40, sx * 0.44, 'Trim')
add_prism(spoiler, [(WING_Y + 0.18, WING_Z + 0.005), (WING_Y + 0.23, WING_Z - 0.01), (WING_Y + 0.23, WING_Z + 0.07), (WING_Y + 0.18, WING_Z + 0.07)], 'YZ', -0.72, 0.72, 'Paint') if False else None
spoiler.fix()

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
