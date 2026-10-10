"""Aventador-style Lamborghini V12, Japanese-tuned drift build. Run: blender -b --python lambo.py"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carlib import *
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
M = make_materials('#ff2f9a', rim='#e3b12e', rim_rough=0.22, rim_metal=0.95)   # hot pink, gold 3-piece rims

L, W, H, WB, WR = 4.78, 2.03, 1.14, 2.70, 0.34
YF, YR = -1.35, 1.35
TRK_F, TRK_R = 0.835, 0.835
ARCH_R = 0.405

# --------------------------------------------------------------- body loft
# y, hw, zb, zc, zt, nu, nl, k, kb
ST = [
    (-2.250, 0.70, 0.13, 0.29, 0.405, 4.0, 4.0, 0.95, 0.95),
    (-2.225, 0.84, 0.095, 0.31, 0.43, 4.5, 5.0, 0.95, 0.95),
    (-2.120, 0.925, 0.09, 0.37, 0.465, 5.0, 6.0, 0.95, 0.95),
    (-1.900, 0.965, 0.10, 0.46, 0.56, 5.0, 6.0, 0.95, 0.94),
    (-1.350, 1.005, 0.12, 0.66, 0.815, 5.0, 6.0, 0.94, 0.94),
    (-0.950, 0.975, 0.13, 0.72, 0.845, 5.0, 6.0, 0.93, 0.94),
    (-0.450, 0.968, 0.13, 0.76, 0.900, 5.0, 6.0, 0.90, 0.94),
    (-0.100, 0.962, 0.13, 0.78, 1.035, 5.5, 6.0, 0.72, 0.94),
    (0.300, 0.960, 0.13, 0.80, 1.125, 6.0, 6.0, 0.62, 0.94),
    (0.650, 0.970, 0.13, 0.80, 1.130, 6.0, 6.0, 0.64, 0.94),
    (1.000, 0.985, 0.14, 0.81, 1.095, 5.5, 6.0, 0.80, 0.94),
    (1.350, 1.012, 0.15, 0.82, 1.040, 6.0, 6.0, 0.90, 0.94),
    (1.700, 1.012, 0.17, 0.83, 1.010, 6.0, 6.0, 0.92, 0.94),
    (2.000, 1.000, 0.18, 0.84, 0.985, 6.0, 6.0, 0.94, 0.94),
    (2.330, 0.975, 0.20, 0.83, 0.950, 6.0, 5.0, 0.94, 0.93),
    (2.400, 0.930, 0.24, 0.81, 0.925, 5.0, 4.5, 0.94, 0.92),
    (2.420, 0.82, 0.30, 0.77, 0.895, 4.0, 3.5, 0.94, 0.92),
]

body, at = loft_body('body', ST, 32, 0.055, lambda *a: 'Paint', 'body', extra_ys=(YF, YR))

# --------------------------------------------------------------- wheel arches (boolean)
cut = Mesh('cutter')
for sx in (1, -1):
    for y in (YF, YR):
        add_cyl(cut, (sx * 0.46, y, WR), (sx * 1.3, y, WR), ARCH_R, ARCH_R, 40, 'Trim')
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
surf = Surf(body)

P = {}
def part(name, group=None):
    if name not in P:
        P[name] = Mesh(name, group or name)
    return P[name]

trim = part('trim')
lights = part('lights')
glass = part('glass')
body_extra = part('body_extra', 'body')
spoiler = part('spoiler')
mirrors = part('mirrors')

# --------------------------------------------------------------- glass
sym(glass, surf, 'S', quad_grid([(-0.36, 0.90), (0.62, 0.985), (0.44, 1.06), (0.10, 1.06)], 16, 4), 'Glass', lift=0.005, sdepth=0.02)
patch(glass, surf, 'F', quad_grid([(-0.64, 0.915), (0.64, 0.915), (0.50, 1.085), (-0.50, 1.085)], 20, 9), 'Glass', lift=0.005, sdepth=0.02)
patch(glass, surf, 'R', quad_grid([(-0.40, 1.025), (0.40, 1.025), (0.34, 1.10), (-0.34, 1.10)], 10, 3), 'Glass', lift=0.005, sdepth=0.02) if False else None

# --------------------------------------------------------------- panel lines
for ribs in (
    [(-0.62, 0.28), (-0.68, 0.46), (-0.54, 0.80), (-0.34, 0.905)],        # door front edge
    [(-0.62, 0.28), (0.20, 0.28), (0.52, 0.33), (0.58, 0.58)],              # door sill
    [(0.58, 0.58), (0.56, 0.84), (0.48, 0.99)],                             # door rear
):
    sym(trim, surf, 'S', ribbon_grid(ribs, 0.007, 0.03), 'Trim', lift=0.002, skirt=False)
sym(trim, surf, 'S', quad_grid([(-0.55, 0.12), (0.60, 0.12), (0.60, 0.20), (-0.55, 0.20)], 20, 1), 'Trim', lift=0.008)   # sill
# bonnet creases (Y shaped) and panel lines
for sx in (1, -1):
    patch(trim, surf, 'T', ribbon_grid([(sx * 0.10, -2.17), (sx * 0.30, -1.55), (sx * 0.34, -0.80)], 0.006, 0.06), 'Trim', lift=0.002, skirt=False)
    patch(trim, surf, 'T', ribbon_grid([(sx * 0.93, -1.95), (sx * 0.84, -1.40), (sx * 0.74, -0.52)], 0.006, 0.06), 'Trim', lift=0.002, skirt=False)
    patch(trim, surf, 'T', ribbon_grid([(sx * 0.68, 1.60), (sx * 0.60, 2.0), (sx * 0.62, 2.35)], 0.006, 0.06), 'Trim', lift=0.002, skirt=False)
patch(trim, surf, 'T', ribbon_grid([(-0.74, -0.52), (0.0, -0.50), (0.74, -0.52)], 0.006, 0.06), 'Trim', lift=0.002, skirt=False)
# hood vents (angular slots) near windscreen
for sx in (1, -1):
    patch(trim, surf, 'T', quad_grid([(sx * 0.40, -1.05), (sx * 0.62, -1.00), (sx * 0.62, -0.84), (sx * 0.40, -0.90)], 6, 4), 'Trim', lift=0.004)
    patch(trim, surf, 'T', quad_grid([(sx * 0.10, -1.05), (sx * 0.30, -1.05), (sx * 0.30, -0.90), (sx * 0.10, -0.90)], 6, 4), 'Trim', lift=0.004) if False else None

# --------------------------------------------------------------- hexagonal engine-cover vents (honeycomb)
def hexv(cx, cy, r, lift=0.006):
    patch(trim, surf, 'T', ellipse_grid(cx, cy, r, r, 2, 6, 0.0, math.radians(30)), 'Trim', lift=lift)
for (cx, cy) in [(0.0, 1.15), (0.0, 1.45), (0.0, 1.75), (0.26, 1.30), (-0.26, 1.30), (0.26, 1.60), (-0.26, 1.60), (0.0, 2.05),
                 (0.50, 1.45), (-0.50, 1.45)]:
    hexv(cx, cy, 0.125)
for (cx, cy) in [(0.0, 1.15), (0.0, 1.45), (0.0, 1.75), (0.26, 1.30), (-0.26, 1.30), (0.26, 1.60), (-0.26, 1.60)]:
    patch(trim, surf, 'T', ellipse_grid(cx, cy, 0.07, 0.07, 2, 6, 0.0, math.radians(30)), 'Chrome', lift=0.010, skirt=False)

# --------------------------------------------------------------- side intakes
for z0, z1 in ((0.42, 0.74),):
    sym(trim, surf, 'S', quad_grid([(0.58, 0.46), (0.98, 0.34), (0.98, 0.72), (0.58, 0.80)], 10, 5), 'Trim', lift=0.006)
    for k in range(4):
        t = 0.2 + k * 0.2
        zz = lerp(0.50, 0.40, 0.0)
        sym(trim, surf, 'S', quad_grid([(0.60, 0.49 + k * 0.07), (0.96, 0.375 + k * 0.07), (0.96, 0.385 + k * 0.07), (0.60, 0.50 + k * 0.07)], 6, 1), 'Chrome', lift=0.009, skirt=False)
# small front intake in front of the door
sym(trim, surf, 'S', quad_grid([(-0.98, 0.32), (-0.72, 0.30), (-0.72, 0.46), (-0.98, 0.50)], 6, 3), 'Trim', lift=0.005)
# fender vent gills
for k in range(4):
    yy = -1.00 + k * 0.045
    sym(trim, surf, 'S', quad_grid([(yy, 0.58), (yy + 0.02, 0.58), (yy + 0.02, 0.70), (yy, 0.70)], 1, 2), 'Trim', lift=0.003, skirt=False)

# --------------------------------------------------------------- front fascia
for sx in (1, -1):
    # angular headlight cluster: dark bezel, slim lens, Y-shaped DRL (placed from above on the nose)
    patch(trim, surf, 'T', quad_grid([(sx * 0.30, -2.19), (sx * 0.90, -2.10), (sx * 0.90, -1.90), (sx * 0.30, -2.00)], 12, 4), 'Trim', lift=0.004)
    patch(lights, surf, 'T', quad_grid([(sx * 0.52, -2.14), (sx * 0.86, -2.085), (sx * 0.86, -2.03), (sx * 0.52, -2.075)], 10, 2), 'HeadLight', lift=0.008)
    stem = [(sx * 0.33, -2.15), (sx * 0.50, -2.115)]
    armA = [(sx * 0.50, -2.115), (sx * 0.85, -2.02)]
    armB = [(sx * 0.50, -2.115), (sx * 0.84, -1.95)] if False else [(sx * 0.50, -2.115), (sx * 0.80, -1.96)]
    for pts in (stem, armA, armB):
        patch(lights, surf, 'T', ribbon_grid(pts, 0.017, 0.03), 'HeadLight', lift=0.008, skirt=False)
    # lower side intakes (angular)
    c = [(sx * 0.58, 0.15), (sx * 0.82, 0.165), (sx * 0.82, 0.31), (sx * 0.62, 0.29)]
    if sx < 0:
        c = [c[1], c[0], c[3], c[2]]
    patch(trim, surf, 'F', quad_grid(c, 8, 4), 'Trim', lift=0.005)
patch(trim, surf, 'F', quad_grid([(-0.52, 0.14), (0.52, 0.14), (0.58, 0.29), (-0.58, 0.29)], 14, 4), 'Trim', lift=0.005)   # central mouth
for k in range(3):
    zz = 0.175 + k * 0.045
    patch(trim, surf, 'F', quad_grid([(-0.50, zz), (0.50, zz), (0.50, zz + 0.01), (-0.50, zz + 0.01)], 14, 1), 'Chrome', lift=0.008, skirt=False)
# front splitter with canards
add_box(trim, (0, -2.245, 0.105), (1.80, 0.12, 0.02), 'Trim')
for sx in (1, -1):
    add_box(trim, (sx * 0.84, -2.17, 0.20), (0.02, 0.12, 0.15), 'Trim')

# --------------------------------------------------------------- rear
for sx in (1, -1):
    # Y-shaped tail lights
    stem = [(sx * 0.30, 0.775), (sx * 0.52, 0.790)]
    armA = [(sx * 0.52, 0.790), (sx * 0.84, 0.860)]
    armB = [(sx * 0.52, 0.790), (sx * 0.82, 0.715)]
    for pts in (stem, armA, armB):
        patch(lights, surf, 'R', ribbon_grid(pts, 0.036, 0.03), 'TailLight', lift=0.010, skirt=True)
patch(trim, surf, 'R', quad_grid([(-0.90, 0.66), (0.90, 0.66), (0.92, 0.90), (-0.92, 0.90)], 24, 5), 'Trim', lift=0.003) if False else None
# hexagonal exhaust housing with quad tips
patch(trim, surf, 'R', ellipse_grid(0, 0.55, 0.25, 0.20, 2, 6, 0.0, 0.0), 'Trim', lift=0.008)
for (dx, dz) in ((-0.075, 0.075), (0.075, 0.075), (-0.075, -0.075), (0.075, -0.075)):
    add_cyl(trim, (dx, 2.33, 0.55 + dz), (dx, 2.46, 0.55 + dz), 0.05, 0.05, 14, 'Chrome')
    add_cyl(trim, (dx, 2.45, 0.55 + dz), (dx, 2.462, 0.55 + dz), 0.038, 0.038, 14, 'Trim')
patch(trim, surf, 'R', quad_grid([(-0.55, 0.36), (0.55, 0.36), (0.60, 0.46), (-0.60, 0.46)], 10, 2), 'Trim', lift=0.004)
patch(trim, surf, 'R', quad_grid([(-0.26, 0.72), (0.26, 0.72), (0.26, 0.83), (-0.26, 0.83)], 8, 2), 'Plate', lift=0.010) if False else None
# aggressive diffuser
add_hex(trim, [(-0.80, 2.15, 0.20), (0.80, 2.15, 0.20), (0.80, 2.33, 0.20), (-0.80, 2.33, 0.20),
               (-0.80, 2.15, 0.23), (0.80, 2.15, 0.23), (0.80, 2.44, 0.40), (-0.80, 2.44, 0.40)], 'Trim')
for k in range(-5, 6):
    add_hex(trim, [(k * 0.15 - 0.008, 2.20, 0.22), (k * 0.15 + 0.008, 2.20, 0.22), (k * 0.15 + 0.008, 2.44, 0.37), (k * 0.15 - 0.008, 2.44, 0.37),
                   (k * 0.15 - 0.008, 2.20, 0.30), (k * 0.15 + 0.008, 2.20, 0.30), (k * 0.15 + 0.008, 2.44, 0.12), (k * 0.15 - 0.008, 2.44, 0.12)], 'Trim') if False else None
    add_box(trim, (k * 0.15, 2.36, 0.30), (0.016, 0.16, 0.20), 'Trim')

# --------------------------------------------------------------- wide fender flares (body is widened at the axles; lips + flare lines here)
for y in (YF, YR):
    sidelip = (50, 102)
    for off in ((0.05, 0.085) if y > 0 else (0.05,)):
        for a0, a1 in ((-sidelip[1], -sidelip[0]), (sidelip[0], sidelip[1])):
            sym(trim, surf, 'S', ribbon_grid(arc_pts(y, WR, ARCH_R + off, a0, a1, 12), 0.008, 0.02), 'Trim', lift=0.002, skirt=False)
    for a0, a1 in ((-sidelip[1], -sidelip[0]), (sidelip[0], sidelip[1])):
        sym(body_extra, surf, 'S', arc_band(y, WR, ARCH_R + 0.002, ARCH_R + (0.04 if y < 0 else 0.06), a0, a1, 12), 'Paint', lift=0.014)

# mirrors
for sx in (1, -1):
    add_box(mirrors, (sx * 0.84, -0.40, 0.90), (0.10, 0.05, 0.03), 'Paint')
    add_hex(mirrors, [(sx * 0.86, -0.30, 0.87), (sx * 1.00, -0.31, 0.87), (sx * 1.00, -0.50, 0.87), (sx * 0.86, -0.49, 0.87),
                      (sx * 0.87, -0.31, 0.935), (sx * 0.995, -0.32, 0.935), (sx * 0.995, -0.49, 0.935), (sx * 0.87, -0.48, 0.935)], 'Paint')
    mirrors.fix()
    add_box(mirrors, (sx * 0.935, -0.298, 0.90), (0.10, 0.012, 0.05), 'Chrome')

# --------------------------------------------------------------- big GT wing on swan-neck stays
WY, WZ = 2.20, 1.14
prof = [(-0.20, -0.02), (-0.12, 0.03), (0.0, 0.055), (0.14, 0.035), (0.22, 0.012), (0.21, -0.006), (0.0, -0.014), (-0.16, -0.03)]
add_prism(spoiler, [(WY + a, WZ + b) for a, b in prof], 'YZ', -0.92, 0.92, 'Paint')
for sx in (1, -1):
    add_prism(spoiler, [(WY - 0.24, WZ - 0.12), (WY + 0.26, WZ - 0.12), (WY + 0.27, WZ + 0.09), (WY + 0.10, WZ + 0.075), (WY - 0.22, WZ + 0.07)],
              'YZ', sx * 0.92, sx * 0.935, 'Paint')
    path = [(1.97, 0.96), (2.02, 1.02), (2.10, 1.07), (2.21, 1.095), (2.30, 1.105)]
    secs = []
    for (py, pz) in path:
        secs.append([(sx * 0.46 - 0.018, py, pz - 0.012), (sx * 0.46 + 0.018, py, pz - 0.012),
                     (sx * 0.46 + 0.018, py, pz + 0.012), (sx * 0.46 - 0.018, py, pz + 0.012)])
    add_loft_sections(spoiler, secs, 'Paint')
spoiler.fix()

# --------------------------------------------------------------- wheels (3-piece, big bright lip, rivets)
def tp_spokes(rin, xf):
    out = []
    for i in range(10):
        a = 2 * math.pi * i / 10
        out.append((0.05, rin, a, a + 0.12, 0.034, 0.030, 0.024, 0.020, xf, xf + 0.035))
    return out


def rivets(m, side, xf):
    for i in range(14):
        a = 2 * math.pi * i / 14
        r = 0.2175
        c = Vector((0, r * math.cos(a), r * math.sin(a)))
        add_cyl(m, (side * 0.145, c.y, c.z), (side * 0.158, c.y, c.z), 0.008, 0.007, 5, 'Chrome')


wheels = []
for nm, sx, y, w, trk, xf in (('wheel_fl', -1, YF, 0.265, TRK_F, 0.045), ('wheel_fr', 1, YF, 0.265, TRK_F, 0.045),
                              ('wheel_rl', -1, YR, 0.335, TRK_R, 0.06), ('wheel_rr', 1, YR, 0.335, TRK_R, 0.06)):
    style = dict(x_face=xf, spokes=tp_spokes, hub_r=0.055, disc=(0.125, 0.185), lip_mat='Chrome', extra=rivets)
    wm = build_wheel(nm, sx, WR, w, 0.2413, style)       # 19" rims
    smooth_edges(wm, 40)
    wo = wm.to_obj(M, nm)
    wo.location = (sx * trk, y, WR)
    wheels.append(wo)

# --------------------------------------------------------------- finalize + export
parts = [body] + list(P.values())
dests = finalize(parts, smooth_deg=30)
objs = []
tot = 0
for nm, d in dests.items():
    o = d.to_obj(M, nm)
    objs.append(o)
    tot += d.tris()
    print(nm, 'tris', d.tris())
objs += wheels
for w_ in wheels:
    tot += sum(len(p.vertices) - 2 for p in w_.data.polygons)
print('TOTAL tris', tot)
glb = export_car('lambo', objs)
size = verify_and_render('lambo', glb)
