"""Ferrari F40 (1987). Run: blender -b --python f40.py"""
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from carlib import *
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)
M = make_materials('#c8100e', rim='#b9bdc4')   # Rosso Corsa

L, W, H, WB, WR = 4.36, 1.97, 1.13, 2.45, 0.33
YF, YR = -1.225, 1.225
TRK_F, TRK_R = 0.797, 0.803
ARCH_R = 0.388

# --------------------------------------------------------------- body loft
# y, hw, zb, zc, zt, nu, nl, k, kb
ST = [
    (-2.175, 0.62, 0.17, 0.33, 0.455, 3.0, 3.0, 0.95, 0.92),
    (-2.150, 0.76, 0.12, 0.35, 0.49, 3.0, 3.5, 0.95, 0.92),
    (-2.050, 0.86, 0.11, 0.41, 0.54, 3.2, 4.0, 0.95, 0.93),
    (-1.800, 0.925, 0.11, 0.52, 0.64, 3.4, 4.5, 0.95, 0.93),
    (-1.225, 0.950, 0.13, 0.68, 0.795, 3.6, 5.0, 0.93, 0.93),
    (-0.900, 0.945, 0.14, 0.72, 0.835, 3.6, 5.0, 0.92, 0.93),
    (-0.560, 0.940, 0.14, 0.76, 0.875, 3.6, 5.0, 0.90, 0.93),
    (-0.250, 0.935, 0.14, 0.77, 0.985, 4.5, 5.0, 0.72, 0.93),
    (0.120, 0.930, 0.14, 0.78, 1.112, 5.5, 5.0, 0.62, 0.93),
    (0.450, 0.935, 0.14, 0.78, 1.124, 5.5, 5.0, 0.62, 0.93),
    (0.800, 0.955, 0.14, 0.79, 1.070, 5.0, 5.0, 0.70, 0.93),
    (1.100, 0.965, 0.15, 0.80, 1.005, 5.0, 5.0, 0.90, 0.93),
    (1.500, 0.972, 0.17, 0.80, 0.985, 6.0, 5.0, 0.95, 0.93),
    (2.000, 0.965, 0.20, 0.78, 0.962, 6.0, 5.0, 0.95, 0.93),
    (2.150, 0.930, 0.24, 0.76, 0.940, 5.0, 4.0, 0.94, 0.92),
    (2.183, 0.800, 0.30, 0.72, 0.900, 3.5, 3.0, 0.93, 0.92),
]
SC = 0.985
ST = [(s[0] * SC,) + s[1:] for s in ST]

body, at = loft_body('body', ST, 40, 0.05, lambda *a: 'Paint', 'body', extra_ys=(YF, YR))
surf0 = Surf(body)           # intact skin (before cutting the engine bay)

# --------------------------------------------------------------- arches + engine bay (boolean)
cut = Mesh('cutter')
for sx in (1, -1):
    for y, xi in ((YF, 0.44), (YR, 0.46)):
        add_cyl(cut, (sx * xi, y, WR), (sx * 1.25, y, WR), ARCH_R, ARCH_R, 40, 'Trim')
BAY_Y0, BAY_Y1, BAY_X = 0.84, 1.90, 0.385
add_box(cut, (0, (BAY_Y0 + BAY_Y1) / 2, 0.80), (BAY_X * 2, BAY_Y1 - BAY_Y0, 0.62), 'Trim')
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
sym(glass, surf, 'S', quad_grid([(-0.42, 0.82), (0.50, 0.82), (0.40, 1.07), (0.04, 1.07)], 16, 5), 'Glass', lift=0.005, sdepth=0.02)
patch(glass, surf, 'F', quad_grid([(-0.65, 0.885), (0.65, 0.885), (0.47, 1.10), (-0.47, 1.10)], 22, 9), 'Glass', lift=0.005, sdepth=0.02)
patch(glass, surf0, 'T', quad_grid([(-0.44, 0.52), (0.44, 0.52), (0.40, 0.80), (-0.40, 0.80)], 14, 6), 'Glass', lift=0.005, sdepth=0.02)
# transparent plexiglass engine cover (engine visible through it) + louvres
patch(glass, surf0, 'T', quad_grid([(-0.44, 0.80), (0.44, 0.80), (0.44, 1.92), (-0.44, 1.92)], 16, 22, 0.0), 'GlassClear', lift=0.006, sdepth=0.03)
for k in range(9):
    y0 = 0.92 + k * 0.118
    patch(trim, surf0, 'T', quad_grid([(-0.44, y0), (0.44, y0), (0.44, y0 + 0.032), (-0.44, y0 + 0.032)], 12, 1), 'Trim', lift=0.016, sdepth=0.012)
for sx in (1, -1):
    patch(trim, surf0, 'T', quad_grid([(sx * 0.44, 0.80), (sx * 0.47, 0.80), (sx * 0.47, 1.92), (sx * 0.44, 1.92)], 1, 22), 'Trim', lift=0.012)

# --------------------------------------------------------------- engine in the bay
def eng():
    add_box(trim, (0, 1.40, 0.76), (0.50, 0.90, 0.12), 'Interior')                 # sump/gearbox area
    for sx in (1, -1):
        R = rotz(0) @ roty(sx * 0.42)
        add_box(trim, (sx * 0.15, 1.30, 0.86), (0.17, 0.62, 0.11), 'Rim', roty(-sx * 0.42))   # cylinder heads
        add_box(trim, (sx * 0.19, 1.30, 0.915), (0.13, 0.52, 0.04), 'Chrome', roty(-sx * 0.42))     # cam covers
        add_box(trim, (sx * 0.31, 1.22, 0.93), (0.16, 0.50, 0.07), 'Rim')   # intercoolers
        add_cyl(trim, (sx * 0.17, 1.72, 0.86), (sx * 0.33, 1.72, 0.86), 0.075, 0.06, 14, 'Chrome')  # turbos
        add_cyl(trim, (sx * 0.09, 1.52, 0.80), (sx * 0.09, 1.78, 0.80), 0.03, 0.03, 8, 'Trim')
    add_box(trim, (0, 1.12, 0.93), (0.12, 0.35, 0.05), 'Chrome')               # plenum
    add_box(trim, (0, 1.86, 0.80), (0.46, 0.08, 0.20), 'Trim')
eng()
for m_ in (trim,):
    pass

# --------------------------------------------------------------- panel lines and vents
door = [(-0.46, 0.84), (-0.52, 0.76), (-0.54, 0.30), (-0.50, 0.26), (0.50, 0.26), (0.54, 0.30), (0.53, 0.82)]
sym(trim, surf, 'S', ribbon_grid(door, 0.007, 0.03), 'Trim', lift=0.002, skirt=False)
sym(trim, surf, 'S', quad_grid([(-0.50, 0.15), (0.60, 0.15), (0.60, 0.22), (-0.50, 0.22)], 20, 1), 'Trim', lift=0.006)   # sill
# NACA duct in the doors
sym(trim, surf, 'S', quad_grid([(-0.36, 0.47), (0.20, 0.40), (0.20, 0.56), (-0.36, 0.50)], 8, 3), 'Trim', lift=0.004)
# big split side intakes ahead of the rear wheel
for z0, z1 in ((0.56, 0.72), (0.37, 0.52)):
    sym(trim, surf, 'S', quad_grid([(0.50, z0), (0.80, z0), (0.80, z1), (0.50, z1)], 8, 3), 'Trim', lift=0.005)
    for k in range(3):
        zz = z0 + 0.03 + k * 0.04
        sym(trim, surf, 'S', quad_grid([(0.51, zz), (0.79, zz), (0.79, zz + 0.012), (0.51, zz + 0.012)], 6, 1), 'Chrome', lift=0.008, skirt=False)
# front fender gills
for k in range(4):
    yy = -0.88 + k * 0.05
    sym(trim, surf, 'S', quad_grid([(yy, 0.52), (yy + 0.022, 0.52), (yy + 0.022, 0.70), (yy, 0.70)], 1, 3), 'Trim', lift=0.003)
# bonnet NACA ducts, hinge lines
for sx in (1, -1):
    patch(trim, surf, 'T', quad_grid([(sx * 0.36 - 0.025, -1.55), (sx * 0.36 + 0.025, -1.55), (sx * 0.36 + 0.115, -1.12), (sx * 0.36 - 0.115, -1.12)], 4, 8), 'Trim', lift=0.004)
    patch(trim, surf, 'T', ribbon_grid([(sx * 0.93, -1.70), (sx * 0.88, -1.15), (sx * 0.83, -0.60)], 0.006, 0.05), 'Trim', lift=0.002, skirt=False)
patch(trim, surf, 'T', ribbon_grid([(-0.86, -0.60), (0.0, -0.58), (0.86, -0.60)], 0.006, 0.05), 'Trim', lift=0.002, skirt=False)
# bonnet air outlet slats behind the windscreen edge? (none on F40) ; rear fender gills over the arches
for sx in (1, -1):
    for k in range(5):
        yy = 1.80 + k * 0.05 - 0.15
        patch(trim, surf, 'T', quad_grid([(sx * 0.62, yy), (sx * 0.84, yy), (sx * 0.84, yy + 0.02), (sx * 0.62, yy + 0.02)], 4, 1), 'Trim', lift=0.003, skirt=False) if False else None

# --------------------------------------------------------------- front fascia
for sx in (1, -1):
    c = [(sx * 0.50, 0.395), (sx * 0.86, 0.405), (sx * 0.86, 0.465), (sx * 0.50, 0.455)]
    if sx < 0:
        c = [c[1], c[0], c[3], c[2]]
    patch(trim, surf, 'F', quad_grid(c, 10, 2), 'Trim', lift=0.004)
    c2 = [(sx * 0.52, 0.405), (sx * 0.84, 0.413), (sx * 0.84, 0.455), (sx * 0.52, 0.447)]
    if sx < 0:
        c2 = [c2[1], c2[0], c2[3], c2[2]]
    patch(lights, surf, 'F', quad_grid(c2, 10, 2, 0.15), 'HeadLight', lift=0.008)
    # pop-up headlight lids (flush) outlines on the leading edge of the wings
    patch(trim, surf, 'T', ribbon_grid([(sx * 0.48, -2.08), (sx * 0.82, -2.06), (sx * 0.82, -1.86), (sx * 0.48, -1.88), (sx * 0.48, -2.08)], 0.006, 0.03), 'Trim', lift=0.002, skirt=False)
    # side intakes
    patch(trim, surf, 'F', ellipse_grid(sx * 0.70, 0.27, 0.13, 0.065, 3, 20), 'Trim', lift=0.005)
patch(trim, surf, 'F', quad_grid([(-0.52, 0.19), (0.52, 0.19), (0.50, 0.345), (-0.50, 0.345)], 18, 4), 'Trim', lift=0.005)  # radiator intake
for k in range(3):
    zz = 0.22 + k * 0.045
    patch(trim, surf, 'F', quad_grid([(-0.50, zz), (0.50, zz), (0.50, zz + 0.01), (-0.50, zz + 0.01)], 16, 1), 'Chrome', lift=0.008, skirt=False)
add_box(trim, (0, -2.150, 0.115), (1.50, 0.05, 0.02), 'Trim')   # lip

# --------------------------------------------------------------- rear
patch(trim, surf, 'R', quad_grid([(-0.78, 0.52), (0.78, 0.52), (0.80, 0.86), (-0.80, 0.86)], 22, 5), 'Trim', lift=0.004)          # black louvred rear panel
for k in range(5):
    zz = 0.55 + k * 0.065
    patch(trim, surf, 'R', quad_grid([(-0.75, zz), (0.75, zz), (0.75, zz + 0.012), (-0.75, zz + 0.012)], 18, 1), 'Chrome', lift=0.007, skirt=False)
for sx in (1, -1):
    for cxx, rr in ((0.66, 0.062), (0.48, 0.056)):
        patch(trim, surf, 'R', ellipse_grid(sx * cxx, 0.745, rr * 1.18, rr * 1.18, 2, 20), 'Chrome', lift=0.009)
        patch(lights, surf, 'R', ellipse_grid(sx * cxx, 0.745, rr, rr, 3, 20), 'TailLight', lift=0.014, crown=0.5)
    add_cyl(trim, (sx * 0.17, 2.00, 0.33), (sx * 0.17, 2.19, 0.33), 0.048, 0.048, 16, 'Chrome')
    add_cyl(trim, (sx * 0.17, 2.18, 0.33), (sx * 0.17, 2.192, 0.33), 0.036, 0.036, 16, 'Trim')
patch(trim, surf, 'R', quad_grid([(-0.26, 0.33), (0.26, 0.33), (0.26, 0.44), (-0.26, 0.44)], 8, 2), 'Plate', lift=0.012) if False else None
# number plate hidden under the lower panel: put it on the rear panel centre
patch(trim, surf, 'R', quad_grid([(-0.26, 0.42), (0.26, 0.42), (0.26, 0.52), (-0.26, 0.52)], 8, 2), 'Plate', lift=0.012) if False else None
add_hex(trim, [(-0.74, 1.98, 0.22), (0.74, 1.98, 0.22), (0.74, 2.12, 0.22), (-0.74, 2.12, 0.22),
               (-0.74, 1.98, 0.245), (0.74, 1.98, 0.245), (0.74, 2.15, 0.28), (-0.74, 2.15, 0.28)], 'Trim')  # diffuser
for k in range(-4, 5):
    add_box(trim, (k * 0.16, 2.065, 0.28), (0.014, 0.16, 0.08), 'Trim')

# --------------------------------------------------------------- fender flares
for y in (YF, YR):
    a0, a1 = (-58, 62) if y < 0 else (-88, 88)
    sym(body_extra, surf, 'S', arc_band(y, WR, ARCH_R + 0.002, ARCH_R + (0.04 if y < 0 else 0.06), a0, a1, 30), 'Paint', lift=0.011)

# mirrors
for sx in (1, -1):
    add_box(mirrors, (sx * 0.80, -0.38, 0.915), (0.08, 0.05, 0.03), 'Paint')
    add_hex(mirrors, [(sx * 0.82, -0.30, 0.88), (sx * 0.94, -0.31, 0.88), (sx * 0.94, -0.44, 0.88), (sx * 0.82, -0.43, 0.88),
                      (sx * 0.83, -0.31, 0.95), (sx * 0.935, -0.32, 0.95), (sx * 0.935, -0.43, 0.95), (sx * 0.83, -0.42, 0.95)], 'Paint')
    mirrors.fix()
    add_box(mirrors, (sx * 0.885, -0.298, 0.915), (0.09, 0.012, 0.052), 'Chrome')

# rear wing, integrated into the rear fenders
WY, WZ = 1.99, 1.025
prof = [(-0.14, -0.02), (-0.09, 0.022), (0.0, 0.040), (0.11, 0.028), (0.17, 0.012), (0.165, -0.006), (0.0, -0.012), (-0.12, -0.025)]
add_prism(spoiler, [(WY + a, WZ + b) for a, b in prof], 'YZ', -0.95, 0.95, 'Paint')
for sx in (1, -1):
    add_prism(spoiler, [(1.80, 0.88), (2.14, 0.91), (2.17, 1.06), (2.12, 1.115), (1.90, 1.115), (1.82, 0.99)], 'YZ', sx * 0.935, sx * 0.965, 'Paint')
    add_prism(spoiler, [(WY - 0.03, 0.94), (WY + 0.03, 0.94), (WY + 0.02, WZ - 0.01), (WY - 0.03, WZ - 0.01)], 'YZ', sx * 0.55, sx * 0.60, 'Paint')
spoiler.fix()

# --------------------------------------------------------------- wheels (five-spoke, centre lock)
def five_spokes(rin, xf):
    out = []
    for i in range(5):
        a = 2 * math.pi * i / 5 + math.pi / 2
        out.append((0.05, rin, a, a, 0.070, 0.100, 0.026, 0.024, xf, xf + 0.02))
    return out


def centre_lock(m, side, xf):
    add_cyl(m, (side * (xf + 0.02), 0, 0), (side * (xf + 0.075), 0, 0), 0.036, 0.034, 8, 'Chrome')
    add_cyl(m, (side * (xf + 0.07), 0, 0), (side * (xf + 0.08), 0, 0), 0.026, 0.026, 6, 'Trim')

wheels = []
for nm, sx, y, w, trk, xf in (('wheel_fl', -1, YF, 0.245, TRK_F, 0.035), ('wheel_fr', 1, YF, 0.245, TRK_F, 0.035),
                              ('wheel_rl', -1, YR, 0.335, TRK_R, 0.055), ('wheel_rr', 1, YR, 0.335, TRK_R, 0.055)):
    style = dict(x_face=xf, spokes=five_spokes, hub_r=0.05, disc=(0.125, 0.17), extra=centre_lock)
    wm = build_wheel(nm, sx, WR, w, 0.2159, style)
    smooth_edges(wm, 40)
    wo = wm.to_obj(M, nm)
    wo.location = (sx * trk, y, WR)
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
for w_ in wheels:
    tot += sum(len(p.vertices) - 2 for p in w_.data.polygons)
print('TOTAL tris', tot)
glb = export_car('f40', objs)
size = verify_and_render('f40', glb)
