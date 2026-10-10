"""London black cab (LTI TX1/TX2 style, 2004). Run: blender -b --python build_blackcab.py"""
import bpy, bmesh, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mr_lib import *

OUT = os.path.expanduser('~/Projects/master-racer/public/models/cars/blackcab.glb')

reset()
bpy.context.scene.unit_settings.system = 'METRIC'

L, W, H = 4.58, 1.80, 1.83
WB = 2.87
WR = 0.33
YF, YR = -WB / 2, WB / 2  # axle positions
HW = 0.85  # body half width
Z0 = 0.25  # underbody
BELT = 1.09
ROOF = 1.70
TRACK_X = 0.74

# ---------------------------------------------------------------- lower hull (Paint)
def f_end(t):  # rounded-end falloff, t 0 (extreme) .. 1 (full section)
    return 1 - math.sqrt(max(0.0, 1 - (1 - t) ** 2))


def zt_of(y):
    if y < -1.2:
        return lerp(0.93, 1.06, smoothstep(-2.25, -1.2, y))
    if y < -0.9:
        return lerp(1.06, BELT, smoothstep(-1.2, -0.9, y))
    return BELT


def hull_prof(st):
    zt, z0 = st['zt'], Z0
    hw = HW
    pts = [(0, z0), (hw - 0.14, z0), (hw - 0.04, z0 + 0.05), (hw, z0 + 0.16), (hw, zt - 0.30), (hw - 0.005, zt - 0.12),
           (hw - 0.06, zt - 0.03), (hw - 0.2, zt), (0, zt + 0.012)]
    ix, iz = st['ix'], st['iz']
    zc = (z0 + zt) / 2
    hh = (zt - z0) / 2
    return [(x * (hw - ix) / hw, zc + (z - zc) * (hh - iz) / hh) for (x, z) in pts]


ts = [0, 0.04, 0.12, 0.25, 0.45, 0.7, 1.0]
HY0 = 2.22
RY = 0.38
stations = []
for t in ts:
    y = -HY0 + RY * t
    stations.append(dict(y=y, zt=zt_of(y), ix=0.34 * f_end(t), iz=0.12 * f_end(t)))
for y in [-1.6, -1.2, -0.6, 0.2, 1.0, 1.6]:
    stations.append(dict(y=y, zt=zt_of(y), ix=0, iz=0))
for t in reversed(ts):
    y = HY0 - RY * t
    stations.append(dict(y=y, zt=zt_of(y), ix=0.30 * f_end(t), iz=0.12 * f_end(t)))
hull = Loft(stations, hull_prof)

# ---------------------------------------------------------------- cabin / glasshouse (Paint + glass patches)
CAB_BASE = [(0, 0.95), (0.78, 0.95), (0.835, BELT), (0.825, 1.17), (0.775, 1.57), (0.745, 1.63), (0.64, 1.675),
            (0.30, 1.695), (0, ROOF)]
CZC, CHH = 1.325, 0.375


def cab_prof(st):
    ix, iz = st['ix'], st['iz']
    return [(x * (0.835 - ix) / 0.835, CZC + (z - CZC) * (CHH - iz) / CHH) for (x, z) in CAB_BASE]


def cab_deform(x, y, z):
    wf = 1 - smoothstep(-1.1, 0.2, y)
    wr = smoothstep(1.0, 1.9, y)
    dz = max(z - BELT, 0)
    return (x, y + 0.90 * wf * dz - 0.14 * wr * dz, z)


FRONT_Y = -1.25
REAR_Y = 2.0
cst = []
IDX = {}
for t in ts:
    cst.append(dict(y=FRONT_Y + 0.20 * t, ix=0.14 * f_end(t), iz=0.06 * f_end(t)))
for name, y in [('wA', -0.85), ('m1', -0.55), ('m2', -0.25), ('wB', -0.05), ('pB', 0.10), ('wC', 1.20), ('pC', 1.36),
                ('wD', 1.80)]:
    IDX[name] = len(cst)
    cst.append(dict(y=y, ix=0, iz=0))
for t in reversed(ts[1:]):  # rear rounding from 1.80 to 2.0
    cst.append(dict(y=REAR_Y - 0.20 * t, ix=0.20 * f_end(t), iz=0.06 * f_end(t)))
cst.append(dict(y=REAR_Y, ix=0.20, iz=0.06))
# rear stations (t reversed) -> fix first elem to end: rebuild properly
cst = cst[:IDX['wD'] + 1]
for t in reversed(ts[:-1]):
    cst.append(dict(y=REAR_Y - 0.20 * t, ix=0.20 * f_end(t), iz=0.06 * f_end(t)))
cabin = Loft(cst, cab_prof, deform=cab_deform)

# glass patches on the cabin sides
glass_b = []  # list of (bmesh)
GOFF = 0.007
side_windows = [('wA', 'wB'), ('pB', 'wC') if False else ('pB', 'wC'), ('pC', 'wD')]
for side in (1, -1):
    for a, b in [('wA', 'wB'), ('pB', 'wC'), ('pC', 'wD')]:
        # pillar between wB..pB is paint; rear door window = pB..wC ; quarter = pC..wD
        fcs = cabin.patch(IDX[a], IDX[b], 3, 4, side)
        glass_b.append(cabin.extract(fcs, GOFF))


def cap_pane(y_plane, xs, zs, deform, off, nx=4, nz=2):
    b = bmesh.new()
    grid = []
    for i in range(nx + 1):
        row = []
        for j in range(nz + 1):
            x = lerp(xs[0], xs[1], i / nx)
            z = lerp(zs[0], zs[1], j / nz)
            px, py, pz = deform(x, y_plane, z)
            row.append(b.verts.new((px, py + off, pz)))
        grid.append(row)
    for i in range(nx):
        for j in range(nz):
            f = b.faces.new([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
            f.smooth = True
    return b


# windscreen & rear glass (planes at the end caps, sheared like the body)
glass_b.append(cap_pane(FRONT_Y, (-0.60, 0.60), (1.19, 1.53), cab_deform, -0.010))
glass_b[-1].normal_update()
glass_b.append(cap_pane(REAR_Y, (-0.56, 0.56), (1.20, 1.52), cab_deform, +0.010))

# ---------------------------------------------------------------- build body object
def finish_loft(l, name, matname):
    me = bpy.data.meshes.new(name)
    l.bm.to_mesh(me)
    me.materials.append(mat(matname))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


hull_ob = finish_loft(hull, 'hull', 'Paint')
cab_ob = finish_loft(cabin, 'cabin', 'Paint')

# wheel arches: cut hull, add liners later
arch_R = 0.395
for yc in (YF, YR):
    for sx in (1, -1):
        c = cutter_cyl('cut', (yc, WR), arch_R, sx * 0.55, sx * 1.0)
        boolean_cut(hull_ob, c)
        bpy.data.objects.remove(c)

# merge hull + cabin + bumpers into BODY
body = Part('body', ['Paint'])
bh = bmesh.new(); bh.from_mesh(hull_ob.data); body.merge(bh, 'Paint'); bh.free()
bc = bmesh.new(); bc.from_mesh(cab_ob.data); body.merge(bc, 'Paint'); bc.free()
bpy.data.objects.remove(hull_ob)
bpy.data.objects.remove(cab_ob)

# bumpers (painted black on the real cab) -> Paint
for yy, sg in ((-2.215, -1), (2.205, 1)):
    box(body, (0, yy, 0.37), (1.50, 0.15, 0.26), 'Paint', bevel=0.06, segs=3)
    for sx in (1, -1):
        box(body, (sx * 0.77, yy - sg * 0.05, 0.38), (0.22, 0.14, 0.22), 'Paint', bevel=0.06, segs=3,
            rot=Matrix.Rotation(math.radians(-sg * sx * 40), 3, 'Z'))
# side sills
for sx in (1, -1):
    box(body, (sx * 0.84, 0.0, 0.31), (0.04, 2.0, 0.10), 'Paint', bevel=0.012)
body_ob = body.to_object(smooth_angle=38)

# ---------------------------------------------------------------- glass
glass = Part('glass', ['Glass'])
for b in glass_b:
    glass.merge(b, 'Glass')
    b.free()
glass_ob = glass.to_object()

# ---------------------------------------------------------------- trim (black plastic, chrome, plate)
trim = Part('trim', ['Trim', 'Chrome', 'Plate'])
# lower front valance + grille
box(trim, (0, -2.255, 0.285), (1.45, 0.05, 0.10), 'Trim', bevel=0.015)
box(trim, (0, -2.195, 0.82), (0.50, 0.06, 0.15), 'Trim', bevel=0.012)       # small grille
for k in range(4):
    box(trim, (0, -2.228, 0.775 + 0.035 * k), (0.46, 0.012, 0.008), 'Chrome')
box(trim, (0, -2.235, 0.915), (0.52, 0.018, 0.020), 'Chrome', bevel=0.005)  # chrome strip over grille
box(trim, (0, -2.236, 0.52), (0.55, 0.02, 0.09), 'Trim', bevel=0.008)      # lower air intake
# headlight surrounds (chrome ring) behind the lamps
for sx in (1, -1):
    cyl(trim, (sx * 0.60, -2.20, 0.82), 'y', 0.125, 0.05, 'Trim', seg=24)
    cyl(trim, (sx * 0.60, -2.215, 0.82), 'y', 0.115, 0.03, 'Chrome', seg=24)
# rear plate + reverse
box(trim, (0, 2.277, 0.58), (0.52, 0.012, 0.12), 'Plate', bevel=0.004)
box(trim, (0, 2.285, 0.85), (0.50, 0.03, 0.05), 'Trim', bevel=0.01)
# door seams (thin dark grooves) + handles on both sides
for sx in (1, -1):
    xs = sx * (HW + 0.002)
    for ys in (-1.00, 0.04, 1.30):
        box(trim, (xs, ys, 0.70), (0.006, 0.010, 0.70), 'Trim')
    # handles: front door (rear edge) and rear door (front edge, rear-hinged)
    box(trim, (sx * (HW + 0.008), -0.10, 0.99), (0.020, 0.10, 0.022), 'Chrome', bevel=0.005)
    box(trim, (sx * (HW + 0.008), 0.18, 0.99), (0.020, 0.10, 0.022), 'Chrome', bevel=0.005)
    # rear door hinge hint (rear-hinged): dark vertical strip
    box(trim, (xs, 1.29, 0.95), (0.012, 0.035, 0.30), 'Trim')
    # side rubbing strip / wheel flares
    for yc in (YF, YR):
        po = arc_pts(yc, WR, arch_R + 0.045, 0, 180, 18)
        pi = arc_pts(yc, WR, arch_R - 0.002, 0, 180, 18)
        for i in range(len(po) - 1):
            xo = sx * (HW + 0.012)
            xi = sx * (HW + 0.0005)
            trim.poly([(xi, pi[i][0], pi[i][1]), (xi, pi[i + 1][0], pi[i + 1][1]), (xo, po[i + 1][0], po[i + 1][1]),
                       (xo, po[i][0], po[i][1])], 'Trim')
    arch_liner(trim, YF, WR, arch_R - 0.003, Z0, sx * 0.58, sx * HW)
    arch_liner(trim, YR, WR, arch_R - 0.003, Z0, sx * 0.58, sx * HW)
# windscreen wipers (resting)
for sx in (1, -1):
    box(trim, (sx * 0.20, -1.215, 1.115), (0.40, 0.008, 0.008), 'Trim', rot=Matrix.Rotation(math.radians(-6 * sx), 3, 'Y'))
# roof cab-sign bracket + A/B pillars rubber
# chrome TX badge + side repeater
box(trim, (0, -2.237, 0.70), (0.12, 0.006, 0.03), 'Chrome')
for sx in (1, -1):
    box(trim, (sx * 0.845, -1.88, 0.74), (0.012, 0.09, 0.03), 'Trim')
trim_ob = trim.to_object(smooth_angle=45)

# ---------------------------------------------------------------- lights
lights = Part('lights', ['HeadLight', 'TailLight', 'Emit_Sign'])
for sx in (1, -1):
    cyl(lights, (sx * 0.60, -2.223, 0.82), 'y', 0.105, 0.02, 'HeadLight', seg=24)       # round headlamp
    box(lights, (sx * 0.805, -2.14, 0.66), (0.03, 0.18, 0.06), 'Emit_Sign', bevel=0.01)   # side indicator
    box(lights, (sx * 0.42, -2.246, 0.62), (0.14, 0.01, 0.05), 'Emit_Sign', bevel=0.004)  # front indicator
    # tail clusters: red stop/tail + amber indicator + white reverse
    box(lights, (sx * 0.70, 2.19, 0.80), (0.12, 0.030, 0.40), 'TailLight', bevel=0.012, segs=2, rot=Matrix.Rotation(math.radians(sx * 22), 3, 'Z'))
    box(lights, (sx * 0.60, 2.225, 0.58), (0.10, 0.015, 0.06), 'Emit_Sign', bevel=0.004)
    box(lights, (sx * 0.40, 2.277, 0.58), (0.10, 0.012, 0.05), 'HeadLight', bevel=0.004)
lights_ob = lights.to_object(smooth_angle=45)

# ---------------------------------------------------------------- mirrors
mir = Part('mirrors', ['Trim', 'Chrome'])
for sx in (1, -1):
    box(mir, (sx * 0.865, -0.92, 1.10), (0.035, 0.09, 0.025), 'Trim')  # stalk
    box(mir, (sx * 0.875, -0.93, 1.19), (0.05, 0.10, 0.17), 'Trim', bevel=0.015, segs=2)
    box(mir, (sx * 0.9005, -0.93, 1.19), (0.002, 0.085, 0.15), 'Chrome')
mir_ob = mir.to_object(smooth_angle=45)

# ---------------------------------------------------------------- interior (seats, dash, wheel) mostly visible via windows
inte = Part('interior', ['Interior'])
box(inte, (0, 1.40, 0.90), (1.25, 0.55, 0.20), 'Interior', bevel=0.04)       # rear bench
box(inte, (0, 1.72, 1.20), (1.25, 0.14, 0.50), 'Interior', bevel=0.04)       # bench back
box(inte, (0.0, 0.55, 0.62), (1.0, 0.18, 0.26), 'Interior', bevel=0.03)       # folding seats
box(inte, (-0.38, -0.35, 0.95), (0.50, 0.50, 0.16), 'Interior', bevel=0.04)  # driver seat
box(inte, (-0.38, 0.0, 1.22), (0.50, 0.12, 0.50), 'Interior', bevel=0.04)
box(inte, (0.0, 0.05, 1.12), (1.62, 0.04, 0.40), 'Interior')                # partition
box(inte, (0, -0.90, 1.12), (1.5, 0.30, 0.14), 'Interior', bevel=0.04)       # dash
cyl(inte, (-0.38, -0.78, 1.20), 'y', 0.18, 0.025, 'Interior', seg=18)
inte_ob = inte.to_object(smooth_angle=45)

# ---------------------------------------------------------------- TAXI sign (own object)
sign = Part('taxi_sign', ['Emit_Sign', 'Trim'])
SW, SD, SH = 0.76, 0.22, 0.13
SZ = ROOF + SH / 2 - 0.005
SY = -0.45
box(sign, (0, SY, SZ), (SW, SD, SH), 'Emit_Sign', bevel=0.03, segs=2)
box(sign, (0, SY, ROOF - 0.002), (SW * 0.9, SD * 0.86, 0.012), 'Trim')
for ysgn, rz in ((-1, Matrix.Rotation(math.pi / 2, 3, 'X')),
                 (1, Matrix.Rotation(math.pi, 3, 'Z') @ Matrix.Rotation(math.pi / 2, 3, 'X'))):
    text_mesh(sign, 'TAXI', (0, SY + ysgn * (SD / 2 + 0.001), SZ), 0.105, 'Trim', depth=0.008, rot=rz)
sign_ob = sign.to_object(smooth_angle=60)
sign_ob.name = 'taxi_sign'

# ---------------------------------------------------------------- wheels (15 inch)
for nm, yc, sx in (('wheel_fl', YF, 1), ('wheel_fr', YF, -1), ('wheel_rl', YR, 1), ('wheel_rr', YR, -1)):
    wheel_object(nm, (sx * TRACK_X, yc, WR), WR, 0.195, 0.19, sx, style='alloy')

# ---------------------------------------------------------------- finalize
for ob, nm in ((body_ob, 'body'), (glass_ob, 'glass'), (trim_ob, 'trim'), (lights_ob, 'lights'), (mir_ob, 'mirrors'),
               (inte_ob, 'interior')):
    ob.name = nm
    ob.data.name = nm

tris, mn, mx = stats()
print('CAB tris', tris, 'bbox', tuple(round(v, 3) for v in mn), tuple(round(v, 3) for v in mx),
      'size', tuple(round(mx[i] - mn[i], 3) for i in range(3)))
export_glb(OUT)
print('exported', OUT)
