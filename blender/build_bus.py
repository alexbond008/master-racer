"""London double-decker (Dennis Trident 2 / Alexander ALX400, 2004). Run: blender -b --python build_bus.py"""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mr_lib import *

OUT = os.path.expanduser('~/Projects/master-racer/public/models/cars/bus.glb')
reset()

L, W, H = 10.2, 2.55, 4.35
WB = 5.6
WR = 0.5
YF, YR = -WB / 2, WB / 2
HW = 1.19
ARCH_R = 0.60
RED = (0.50, 0.012, 0.02, 1)
mat('Paint', RED)


def f_end(t):
    return 1 - math.sqrt(max(0.0, 1 - (1 - t) ** 2))


# ----------------------------------------------------------------- stations
lower_bays = [(-3.65, -2.55), (-2.45, -1.35), (-1.25, -0.15), (-0.05, 1.05), (1.15, 2.25), (2.35, 3.45), (3.55, 4.75)]
upper_bays = [(-4.15, -3.05), (-2.95, -1.85), (-1.75, -0.65), (-0.55, 0.55), (0.65, 1.75), (1.85, 2.95), (3.05, 4.15),
              (4.25, 4.75)]
FRONT_DOOR = (-4.75, -3.80)
EXIT_DOOR = (-0.05, 1.05)
ADVERT = (-2.80, 4.50)
ys = set()
for a, b in lower_bays + upper_bays + [FRONT_DOOR, ADVERT]:
    ys.add(round(a, 3)); ys.add(round(b, 3))
ts = [0, 0.04, 0.12, 0.25, 0.45, 0.7, 1.0]
RY = 0.25
YEND = 5.0
for t in ts:
    ys.add(round(-YEND + RY * t, 3)); ys.add(round(YEND - RY * t, 3))
for y in (-4.45, -0.35, 0.8, 1.7, 2.8, 3.9):
    ys.add(y)
ys = sorted(ys)
IDX = {y: i for i, y in enumerate(ys)}


def st_of(y):
    d = YEND - abs(y)
    if d < RY:
        t = d / RY
        k = f_end(t)
        return dict(y=y, ix=0.25 * k, iz=0.14 * k)
    return dict(y=y, ix=0, iz=0)


stations = [st_of(y) for y in ys]

# right-half ring (bottom centre -> top centre); indices used for window patches
def ring(hw, z):
    return [(0, 0.80), (hw - 0.15, 0.80), (hw, 0.90), (hw, 1.15), (hw, 1.83), (hw, 2.02), (hw, 2.20), (hw, 2.88),
            (hw - 0.003, 3.00), (hw - 0.010, 3.68), (hw - 0.020, 3.86), (hw - 0.06, 4.04), (hw - 0.18, 4.21),
            (hw - 0.50, 4.325), (0, 4.35)]


ZC, HH = (0.80 + 4.35) / 2, (4.35 - 0.80) / 2


def hull_prof(st):
    ix, iz = st['ix'], st['iz']
    return [(x * (HW - ix) / HW, ZC + (z - ZC) * (HH - iz) / HH) for (x, z) in ring(HW, None)]


def deform(x, y, z):
    s = (max(z - 2.30, 0) / 2.05)
    wf = 1 - smoothstep(-4.4, -2.5, y)
    wr = smoothstep(2.6, 4.6, y)
    return (x, y + 0.50 * wf * s ** 1.6 - 0.22 * wr * s ** 1.5, z)


hull = Loft(stations, hull_prof, deform=deform)


def skirt_prof(st):
    ix, iz = st['ix'], st['iz']
    hw = HW + 0.004
    pts = [(0, 0.30), (hw - 0.10, 0.30), (hw - 0.01, 0.40), (hw, 0.55), (hw, 0.91), (hw - 0.08, 0.91), (0, 0.91)]
    zc, hh = 0.605, 0.305
    return [(x * (hw - ix * 0.9) / hw, zc + (z - zc) * (hh - iz * 0.5) / hh) for (x, z) in pts]


sk_st = [dict(y=s['y'] * 1.0012, ix=s['ix'], iz=s['iz']) for s in stations]
skirt = Loft(sk_st, skirt_prof)

# ----------------------------------------------------------------- window patches
GOFF = 0.006
glass_b, emit_b, trim_b = [], [], []


def I(y):
    return IDX[round(y, 3)]


for side in (1, -1):
    for (a, b) in lower_bays:
        if side == 1 and (a, b) == EXIT_DOOR:
            glass_b.append(hull.extract(hull.patch(I(a), I(b), 2, 5, side), GOFF))
        else:
            emit_b.append(hull.extract(hull.patch(I(a), I(b), 3, 4, side), GOFF))
            glass_b.append(hull.extract(hull.patch(I(a), I(b), 4, 5, side), GOFF))
    for (a, b) in upper_bays:
        emit_b.append(hull.extract(hull.patch(I(a), I(b), 8, 9, side), GOFF))
        glass_b.append(hull.extract(hull.patch(I(a), I(b), 9, 10, side), GOFF))
    a, b = FRONT_DOOR
    glass_b.append(hull.extract(hull.patch(I(a), I(b), 2 if side == 1 else 3, 5, side), GOFF))
    trim_b.append(hull.extract(hull.patch(I(ADVERT[0]), I(ADVERT[1]), 6, 7, side), 0.004))

# end panes: front (y=-5.0) and rear (y=+5.0) planes pass through the same deform
FY = -YEND
glass_b.append(cap_pane(FY, (-0.93, 0.93), (1.20, 2.05), deform, -0.012, nx=6, nz=2))   # lower windscreen
glass_b.append(cap_pane(FY, (-0.90, 0.90), (3.02, 3.86), deform, -0.012, nx=6, nz=3))   # upper windscreen
sign_b = [cap_pane(FY, (-0.52, 0.52), (2.36, 2.70), deform, -0.014, nx=2, nz=1)]           # destination blind
route_b = [cap_pane(FY, (0.56, 0.90), (2.36, 2.70), deform, -0.014, nx=1, nz=1)]           # route number box
glass_b.append(cap_pane(YEND, (-0.70, 0.70), (3.05, 3.80), deform, +0.012, nx=4, nz=2))   # rear window upper

# ----------------------------------------------------------------- bodies
def loft_obj(l, name, matname):
    me = bpy.data.meshes.new(name)
    l.bm.to_mesh(me)
    me.materials.append(mat(matname))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


hull_ob = loft_obj(hull, 'hull', 'Paint')
skirt_ob = loft_obj(skirt, 'skirt', 'Trim')
for yc, xin, xout, sx_list in ((YF, 0.55, 1.35, (1, -1)), (YR, 0.55, 1.35, (1, -1))):
    for sx in sx_list:
        for target in (hull_ob, skirt_ob):
            c = cutter_cyl('cut', (yc, WR), ARCH_R, sx * xin, sx * xout)
            boolean_cut(target, c)
            bpy.data.objects.remove(c)

body = Part('body', ['Paint'])
bh = bmesh.new(); bh.from_mesh(hull_ob.data); body.merge(bh, 'Paint'); bh.free()
bpy.data.objects.remove(hull_ob)
# roof details (painted)
box(body, (0, 3.9, 4.33), (1.3, 1.1, 0.04), 'Paint', bevel=0.015)
box(body, (0, 1.2, 4.33), (0.9, 0.7, 0.04), 'Paint', bevel=0.015)
body_ob = body.to_object(smooth_angle=40)

glass = Part('glass', ['Glass'])
for b in glass_b:
    glass.merge(b, 'Glass'); b.free()
glass_ob = glass.to_object()

emit = Part('emit_window', ['Emit_Window'])
for b in emit_b:
    emit.merge(b, 'Emit_Window'); b.free()
emit_ob = emit.to_object()

# ----------------------------------------------------------------- trim object
trim = Part('trim', ['Trim', 'Chrome', 'Plate'])
tb = bmesh.new(); tb.from_mesh(skirt_ob.data); trim.merge(tb, 'Trim'); tb.free()
bpy.data.objects.remove(skirt_ob)
for b in trim_b:
    trim.merge(b, 'Trim'); b.free()
# bumpers
for yy, sg in ((-5.04, -1), (5.04, 1)):
    box(trim, (0, yy, 0.47), (1.95, 0.12, 0.34), 'Trim', bevel=0.05, segs=2)
    for sx in (1, -1):
        box(trim, (sx * 1.0, yy - sg * 0.10, 0.47), (0.36, 0.12, 0.34), 'Trim', bevel=0.05, segs=2,
            rot=Matrix.Rotation(math.radians(-sg * sx * 35), 3, 'Z'))
# front: grille / vents under the windscreen, wipers
box(trim, (0, -5.0, 1.00), (1.15, 0.03, 0.12), 'Trim', bevel=0.01)
for sx in (1, -1):
    box(trim, (sx * 0.45, -5.012, 1.27), (0.95, 0.02, 0.02), 'Trim', rot=Matrix.Rotation(math.radians(sx * 6), 3, 'Y'))
# door seams (front entrance double door + centre exit) and frames (left side), rubber posts between bays
sx = 1
xs = HW + 0.003
for (y0, y1) in (FRONT_DOOR, EXIT_DOOR):
    ym = (y0 + y1) / 2
    for yy in (y0, y1):
        box(trim, (xs + 0.002, yy, 1.45), (0.012, 0.035, 1.18), 'Trim')
    box(trim, (xs + 0.004, ym, 1.45), (0.014, 0.03, 1.18), 'Trim')           # double door centre seam
    box(trim, (xs + 0.002, ym, 2.035), (0.012, y1 - y0, 0.03), 'Trim')
    box(trim, (xs + 0.002, ym, 0.90), (0.012, y1 - y0, 0.03), 'Trim')
# wheel arch lips + liners
for yc in (YF, YR):
    for sxx in (1, -1):
        po = arc_pts(yc, WR, ARCH_R + 0.05, 0, 180, 20)
        pi = arc_pts(yc, WR, ARCH_R - 0.002, 0, 180, 20)
        for i in range(len(po) - 1):
            xo = sxx * (HW + 0.014)
            xi = sxx * (HW + 0.0005)
            trim.poly([(xi, pi[i][0], pi[i][1]), (xi, pi[i + 1][0], pi[i + 1][1]), (xo, po[i + 1][0], po[i + 1][1]),
                       (xo, po[i][0], po[i][1])], 'Trim')
        arch_liner(trim, yc, WR, ARCH_R - 0.003, 0.30, sxx * 0.62, sxx * HW)
# rear plate, rear bumper detail
box(trim, (0, 5.062, 0.80), (0.56, 0.012, 0.13), 'Plate', bevel=0.004)
box(trim, (0, 4.995, 1.20), (1.7, 0.03, 0.30), 'Trim', bevel=0.01)      # engine vent
for k in range(5):
    box(trim, (0, 5.012, 1.12 + 0.05 * k), (1.6, 0.01, 0.012), 'Chrome')
# side grab / emergency exit outline on right side rear upper? (skip)  front entrance step light etc.
trim_ob = trim.to_object(smooth_angle=45)

# ----------------------------------------------------------------- lights
lights = Part('lights', ['HeadLight', 'TailLight', 'Emit_Sign'])
for sxx in (1, -1):
    for xo in (0.52, 0.88):
        box(lights, (sxx * xo, -5.02, 1.03), (0.28, 0.025, 0.14), 'HeadLight', bevel=0.02, segs=2)
    box(lights, (sxx * 1.10, -4.96, 1.03), (0.12, 0.08, 0.14), 'Emit_Sign', bevel=0.02, rot=Matrix.Rotation(math.radians(sxx * 30), 3, 'Z'))
    # rear: stop/tail clusters, indicators, reverse
    box(lights, (sxx * 0.95, 5.015, 1.45), (0.22, 0.03, 0.50), 'TailLight', bevel=0.02, segs=2)
    box(lights, (sxx * 0.95, 5.015, 1.00), (0.22, 0.03, 0.10), 'Emit_Sign', bevel=0.01)
    box(lights, (sxx * 0.60, 5.015, 1.00), (0.12, 0.03, 0.10), 'HeadLight', bevel=0.01)
    box(lights, (sxx * 0.60, 5.015, 1.20), (0.12, 0.03, 0.10), 'TailLight', bevel=0.01)
lights_ob = lights.to_object(smooth_angle=45)

# ----------------------------------------------------------------- mirrors
mir = Part('mirrors', ['Trim', 'Chrome'])
for sxx in (1, -1):
    box(mir, (sxx * 1.20, -4.80, 1.62), (0.14, 0.06, 0.06), 'Trim')                          # bracket
    box(mir, (sxx * 1.225, -4.88, 1.30), (0.10, 0.07, 0.62), 'Trim', bevel=0.02, segs=2)   # big housing
    box(mir, (sxx * 1.2755, -4.88, 1.30), (0.002, 0.055, 0.56), 'Chrome')
    box(mir, (sxx * 1.18, -4.84, 2.40), (0.20, 0.05, 0.05), 'Trim')                          # upper deck mirror arm
    box(mir, (sxx * 1.255, -4.88, 2.52), (0.04, 0.07, 0.30), 'Trim', bevel=0.012)
mir_ob = mir.to_object(smooth_angle=45)

# ----------------------------------------------------------------- signs (emissive destination blind, route box + text)
sg = Part('emit_sign', ['Emit_Sign', 'Emit_Route', 'Trim'])
for b in sign_b:
    sg.merge(b, 'Emit_Sign'); b.free()
for b in route_b:
    sg.merge(b, 'Emit_Route'); b.free()
# side blinds + route number box on the left side, near the front
xsd = HW + 0.012
box(sg, (xsd, -4.35, 2.52), (0.012, 0.95, 0.30), 'Emit_Sign')
box(sg, (xsd, -3.55, 2.52), (0.012, 0.50, 0.30), 'Emit_Route')
box(sg, (-xsd, -4.35, 2.52), (0.012, 0.95, 0.30), 'Emit_Sign')
# rear route box on the back of the upper deck
box(sg, (0.0, 5.0, 2.52), (0.6, 0.02, 0.30), 'Emit_Sign')
def yz_rot(sgn):
    return Matrix.Rotation(math.pi / 2, 3, 'Y') if sgn > 0 else Matrix.Rotation(-math.pi / 2, 3, 'Y')
# text: front blind and route number (read from -Y); side route number (left, read from +X)
rotf = Matrix.Rotation(math.pi / 2, 3, 'X')
text_mesh(sg, 'STREATHAM', (0, -5.0 - 0.014 - 0.006, 2.53), 0.150, 'Trim', depth=0.008, rot=rotf)
text_mesh(sg, '159', (0.73, -5.0 - 0.014 - 0.006, 2.53), 0.200, 'Trim', depth=0.008, rot=rotf)
# side: face +X; text lies in XY plane -> rotate X 90 then Z 90 so it reads along -Y... face normal +X, text reads toward the front (-Y)
rots = Matrix.Rotation(math.radians(90), 3, 'Z') @ Matrix.Rotation(math.pi / 2, 3, 'X')
text_mesh(sg, '159', (xsd + 0.007, -3.55, 2.52), 0.17, 'Trim', depth=0.008, rot=rots)
text_mesh(sg, 'STREATHAM', (xsd + 0.007, -4.35, 2.52), 0.12, 'Trim', depth=0.008, rot=rots)
sg_ob = sg.to_object(smooth_angle=60)

# ----------------------------------------------------------------- wheels
FRONT_X, REAR_X = 1.04, 0.96
for nm, yc, sxx, xx, offs, wd in (('wheel_fl', YF, 1, FRONT_X, (0.0,), 0.30), ('wheel_fr', YF, -1, FRONT_X, (0.0,), 0.30),
                                   ('wheel_rl', YR, 1, REAR_X, (-0.145, 0.145), 0.255),
                                   ('wheel_rr', YR, -1, REAR_X, (-0.145, 0.145), 0.255)):
    wheel_object(nm, (sxx * xx, yc, WR), WR, wd, 0.28, sxx, offsets=offs, style='steel')

# ----------------------------------------------------------------- names
for ob, nm in ((body_ob, 'body'), (glass_ob, 'glass'), (emit_ob, 'emit_window'), (trim_ob, 'trim'), (lights_ob, 'lights'),
               (mir_ob, 'mirrors'), (sg_ob, 'emit_sign')):
    ob.name = nm
    ob.data.name = nm

tris, mn, mx = stats()
print('BUS tris', tris, 'bbox', tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx),
      'size', tuple(round(mx[i] - mn[i], 3) for i in range(3)))
export_glb(OUT)
print('exported', OUT)
