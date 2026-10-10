"""Shared helpers for the Met Police car models (cruiser / interceptor / suv).

Used by blender/police_<id>.py.  Run:  blender -b --python police_cruiser.py
Blender is Z-up, front of car = -Y, left of car = +X.  Units = metres.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HOME = os.path.expanduser('~/Projects/master-racer')
OUT_DIR = HOME + '/public/models/cars'
PREV_DIR = HOME + '/blender/previews'


FLAT_GROUPS = ('plates', 'lights', 'chrome', 'strobes')
CUT_Z = None


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, a, b):
    return max(a, min(b, v))


# ---------------------------------------------------------------- curves
def pchip(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = 0
        while xs[i + 1] < x:
            i += 1
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def chaikin(pts, it=2, closed=True):
    for _ in range(it):
        out = []
        n = len(pts)
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            p, q = pts[i], pts[(i + 1) % n]
            out.append((0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]))
            out.append((0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]))
        pts = out
    return pts


def rect(a0, a1, b0, b1):
    return [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]


def rrect(a0, a1, b0, b1, it=2):
    return chaikin(rect(a0, a1, b0, b1), it)


def ellipse(ca, cb, ra, rb, n=16):
    return [(ca + ra * math.cos(2 * math.pi * i / n), cb + rb * math.sin(2 * math.pi * i / n)) for i in range(n)]


def mirror_x(pts):
    return [(-a, b) for a, b in reversed(pts)]


# ---------------------------------------------------------------- materials
def make_materials(paint=(0.92, 0.93, 0.95), paint_rough=0.25, paint_metal=0.5):
    mats = {}

    def mk(name, col, rough=0.5, metal=0.0, emit=None, strength=0.0, alpha=1.0):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if emit is not None:
            b.inputs['Emission Color'].default_value = (emit[0], emit[1], emit[2], 1)
            b.inputs['Emission Strength'].default_value = strength
        m.diffuse_color = (col[0], col[1], col[2], 1)
        mats[name] = m
        return m
    mk('Paint', paint, paint_rough, paint_metal)
    g = mk('Glass', (0.03, 0.045, 0.06), 0.04, 0.4)
    g.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.3
    g.diffuse_color = (0.03, 0.045, 0.06, 0.3)
    try:
        g.surface_render_method = 'BLENDED'
    except Exception:
        pass
    try:
        g.blend_method = 'BLEND'
    except Exception:
        pass
    mk('Tyre', (0.025, 0.025, 0.027), 0.85, 0.0)
    mk('Rim', (0.72, 0.73, 0.76), 0.3, 0.9)
    mk('Chrome', (0.9, 0.9, 0.92), 0.12, 1.0)
    mk('Trim', (0.025, 0.025, 0.028), 0.6, 0.0)
    mk('Interior', (0.07, 0.07, 0.075), 0.8, 0.0)
    mk('Emit_Dash', (0.2, 1.0, 0.7), 0.4, 0.0, (0.2, 1.0, 0.7), 2.5)
    mk('Driver', (0.62, 0.43, 0.33), 0.7, 0.0)
    mk('HeadLight', (1.0, 0.95, 0.8), 0.1, 0.0, (1.0, 0.92, 0.72), 3.0)
    mk('TailLight', (0.8, 0.02, 0.02), 0.2, 0.0, (1.0, 0.04, 0.03), 2.5)
    mk('Plate', (0.93, 0.9, 0.82), 0.5, 0.0)
    mk('Livery_Blue', (0.0, 0.07, 0.42), 0.35, 0.0)
    mk('Livery_Yellow', (1.0, 0.72, 0.0), 0.35, 0.0, (1.0, 0.7, 0.0), 0.25)
    mk('Livery_Dark', (0.012, 0.02, 0.09), 0.4, 0.0)
    mk('Light_Red', (1.0, 0.05, 0.03), 0.2, 0.0, (1.0, 0.03, 0.01), 3.5)
    mk('Light_Blue', (0.05, 0.2, 1.0), 0.2, 0.0, (0.0, 0.08, 1.0), 4.0)
    return mats


# ---------------------------------------------------------------- the Car builder
class Car:
    def __init__(self, spec):
        self.s = spec
        self.name = spec['name']
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.mats = make_materials(**spec.get('paint_kw', {}))
        self.groups = {}      # name -> (bmesh, [matnames])
        self.surf = None
        self.mid = spec['fo'] + spec['wb'] / 2.0   # yy of origin
        self.warn = 0

    # y_b (blender y) from distance-from-front
    def Y(self, yy):
        return yy - self.mid

    def group(self, name):
        if name not in self.groups:
            self.groups[name] = (bmesh.new(), [])
        return self.groups[name]

    def mat_index(self, gname, mat):
        bm, ml = self.group(gname)
        if mat not in ml:
            ml.append(mat)
        return ml.index(mat)

    # ------------------------------------------------------------ body loft
    def build_loft(self):
        s = self.s
        f_ztop = pchip(s['ztop'])
        f_zs = pchip(s['zs'])
        f_zb = pchip(s['zb'])
        L = s['L']
        deck_fh = [0.26, 0.5, 0.71, 0.87, 0.97, 1.0]
        deck_fw = [0.034, 0.134, 0.293, 0.5, 0.741, 1.0]
        cab_fh = [0.2, 0.4, 0.6, 0.8, 0.93, 1.0]
        cab_fw = [0.2, 0.4, 0.6, 0.78, 0.88, 0.93]
        Rf, Rr = s.get('plan_rf', 0.42), s.get('plan_rr', 0.42)
        pf, pr = s.get('plan_minf', 0.62), s.get('plan_minr', 0.62)

        def plan(yy):
            sc = 1.0
            if yy < Rf:
                t = 1 - yy / Rf
                sc = min(sc, pf + (1 - pf) * (1 - t ** 3.5) ** (1 / 3.5))
            if yy > L - Rr:
                t = 1 - (L - yy) / Rr
                sc = min(sc, pr + (1 - pr) * (1 - t ** 3.5) ** (1 / 3.5))
            return sc

        bm = bmesh.new()
        rings = []
        self.ring_data = []
        for yy in s['stations']:
            ztop = f_ztop(yy)
            zs = min(f_zs(yy), ztop - 0.06)
            zb = f_zb(yy)
            hw = s['hw'] * plan(yy)
            hwb = hw - s['tumble']
            h = ztop - zs
            c = clamp((h - 0.12) / 0.2, 0, 1)
            inset = lerp(s['inset'], s['lean'], c)
            hwr = max(hwb - inset, 0.2)
            zw = zb + (zs - zb) * 0.42
            crown = s.get('crown', 0.02) + 0.015 * (1 - c)
            pts = [(0, zb), (hw * 0.86, zb), (hw * 0.97, zb + 0.025), (hw, zb + 0.08), (hw, zw),
                   (lerp(hw, hwb, 0.45), lerp(zw, zs, 0.55))]
            for i in range(6):
                fh = lerp(deck_fh[i], cab_fh[i], c)
                fw = lerp(deck_fw[i], cab_fw[i], c)
                z = zs + h * fh - (crown if i == 5 else 0)
                pts.append((hwb + (hwr - hwb) * fw, z))
            x6 = pts[-1][0]
            pts.append((min(hwr * 0.66, x6 * 0.8), ztop - crown * 0.45))
            pts.append((min(hwr * 0.33, x6 * 0.4), ztop - crown * 0.1))
            pts.append((0, ztop))
            n = len(pts)
            ring = []
            y = self.Y(yy)
            for i in range(n):
                ring.append(bm.verts.new((pts[i][0], y, pts[i][1])))
            for i in range(n - 2, 0, -1):
                ring.append(bm.verts.new((-pts[i][0], y, pts[i][1])))
            rings.append(ring)
            self.ring_data.append((yy, zs, ztop, hwb, hwr, c))
        m = len(rings[0])
        for i in range(len(rings) - 1):
            for j in range(m):
                bm.faces.new((rings[i][j], rings[i][(j + 1) % m], rings[i + 1][(j + 1) % m], rings[i + 1][j]))
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1][::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        mesh = bpy.data.meshes.new('body')
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(self.mats['Paint'])
        obj = bpy.data.objects.new('body', mesh)
        bpy.context.collection.objects.link(obj)
        return obj

    def arch_cut(self, obj):
        s = self.s
        r = s['r']
        ra = r + s.get('arch_gap', 0.055)
        cb = bmesh.new()
        seg = 32
        for yy in (s['fo'], s['fo'] + s['wb']):
            for sx in (1, -1):
                xc = sx * (s['hw'] - 0.14)
                half = 0.32
                ring0, ring1 = [], []
                for k in range(seg):
                    a = 2 * math.pi * k / seg
                    ring0.append(cb.verts.new((xc - half, self.Y(yy) + ra * math.cos(a), r + ra * math.sin(a))))
                    ring1.append(cb.verts.new((xc + half, self.Y(yy) + ra * math.cos(a), r + ra * math.sin(a))))
                for k in range(seg):
                    cb.faces.new((ring0[k], ring0[(k + 1) % seg], ring1[(k + 1) % seg], ring1[k]))
                cb.faces.new(ring0[::-1])
                cb.faces.new(ring1)
        bmesh.ops.recalc_face_normals(cb, faces=cb.faces[:])
        mesh = bpy.data.meshes.new('cutter')
        cb.to_mesh(mesh)
        cb.free()
        mesh.materials.append(self.mats['Trim'])
        cut = bpy.data.objects.new('cutter', mesh)
        bpy.context.collection.objects.link(cut)
        mod = obj.modifiers.new('arch', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = cut
        mod.solver = 'EXACT'
        try:
            mod.material_mode = 'TRANSFER'
        except Exception as e:
            print('material_mode?', e)
        bpy.context.view_layer.objects.active = obj
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.ops.object.modifier_apply(modifier='arch')
        bpy.data.objects.remove(cut)
        # move mesh into groups: Paint -> body, Trim -> trim
        me = obj.data
        names = [m.name if m else None for m in me.materials]
        print('body mats after boolean', names)
        bmb = bmesh.new()
        bmb.from_mesh(me)
        bmb.faces.ensure_lookup_table()
        self.group('body')
        self.group('trim')
        bpy.data.objects.remove(obj)
        bpy.data.meshes.remove(me)
        for gname in ('body', 'trim'):
            pass
        # split by material
        for gname, matname in (('body', 'Paint'), ('trim', 'Trim')):
            tgt, _ = self.group(gname)
            idx = self.mat_index(gname, matname)
            fs = [f for f in bmb.faces if names[f.material_index] == matname]
            mapv = {}
            for f in fs:
                nv = []
                for v in f.verts:
                    if v.index not in mapv:
                        mapv[v.index] = tgt.verts.new(v.co)
                    nv.append(mapv[v.index])
                nf = tgt.faces.new(nv)
                nf.material_index = idx
        bmb.free()

    # ------------------------------------------------------------ surface raycasting
    def refresh_surface(self, names=('body', 'glass')):
        bm = bmesh.new()
        for n in names:
            if n in self.groups:
                src, _ = self.groups[n]
                tmp = bmesh.new()
                mesh = bpy.data.meshes.new('tmp')
                src.to_mesh(mesh)
                bm.from_mesh(mesh)
                bpy.data.meshes.remove(mesh)
                tmp.free()
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        self.surf = BVHTree.FromBMesh(bm)
        bm.free()

    def cast(self, origin, direction):
        d = Vector(direction).normalized()
        loc, nor, idx, dist = self.surf.ray_cast(Vector(origin), d, 50.0)
        if loc is None:      # rays exactly on a triangle edge can slip through: retry with tiny jitter
            for j in ((3e-4, 1.7e-4, 2e-4), (-2.3e-4, 3e-4, -1.1e-4), (1.3e-4, -2.9e-4, 3.1e-4)):
                loc, nor, idx, dist = self.surf.ray_cast(Vector(origin) + Vector(j), d, 50.0)
                if loc is not None:
                    break
        if loc is not None and nor.dot(d) > 0:
            nor = -nor        # normals of sliver triangles can be flipped: always face the ray origin
        return loc, nor

    def ok_pts(self, mapper, direction, pts, nmin=0.7, axis=None, sign=1):
        """True if all sample points hit the surface facing roughly toward the ray."""
        d = Vector(direction).normalized()
        for a, b in pts:
            loc, nor = self.cast(mapper(a, b), d)
            if loc is None:
                return False
            if nor.dot(-d) < nmin:
                return False
        return True

    # ------------------------------------------------------------ conformed patches
    def patch(self, gname, mat, outline, mapper, direction, offset=0.004, maxlen=0.06, depth=0.0, reject_bad=False):
        d = Vector(direction).normalized()
        b2 = bmesh.new()
        is_rect = len(outline) == 4 and abs(outline[0][1] - outline[1][1]) < 1e-9 and abs(outline[1][0] - outline[2][0]) < 1e-9
        if is_rect:
            a0, a1 = outline[0][0], outline[1][0]
            bb0, bb1 = outline[0][1], outline[2][1]
            nx = max(1, math.ceil(abs(a1 - a0) / maxlen))
            ny = max(1, math.ceil(abs(bb1 - bb0) / maxlen))
            grid = [[b2.verts.new((lerp(a0, a1, i / nx), lerp(bb0, bb1, j / ny), 0)) for j in range(ny + 1)] for i in range(nx + 1)]
            for i in range(nx):
                for j in range(ny):
                    b2.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            bmesh.ops.triangulate(b2, faces=b2.faces[:])
        else:
            cx = sum(p[0] for p in outline) / len(outline)
            cy = sum(p[1] for p in outline) / len(outline)
            vc = b2.verts.new((cx, cy, 0))
            vs = [b2.verts.new((a, b, 0)) for a, b in outline]
            for i in range(len(vs)):
                try:
                    b2.faces.new((vc, vs[i], vs[(i + 1) % len(vs)]))
                except ValueError:
                    pass
            for _ in range(7):
                long = [e for e in b2.edges if e.calc_length() > maxlen]
                if not long:
                    break
                bmesh.ops.subdivide_edges(b2, edges=long, cuts=1, use_grid_fill=False)
                bmesh.ops.triangulate(b2, faces=b2.faces[:])
        hitn = {}
        miss = []
        for v in b2.verts:
            a, b = v.co.x, v.co.y
            loc, nor = self.cast(mapper(a, b), d)
            if loc is None or (reject_bad and nor.dot(-d) < 0.5):
                if reject_bad:
                    b2.free()
                    return
                miss.append(v)
                continue
            hitn[v.index] = nor
            v.co = loc + nor * offset
        if miss:
            self.warn += 1
            print('PATCH MISS', gname, mat, len(miss), [(round(v.co.x,3), round(v.co.y,3)) for v in miss[:3]])
            bmesh.ops.delete(b2, geom=miss, context='VERTS')
        b2.faces.ensure_lookup_table()
        b2.normal_update()
        tgt, _ = self.group(gname)
        mi = self.mat_index(gname, mat)
        mapv = {}
        tot = 0.0
        for f in b2.faces:
            ns = Vector()
            for v in f.verts:
                ns += hitn.get(v.index, Vector())
            tot += f.calc_area() * f.normal.dot(ns)
        flip = tot < 0
        for f in b2.faces:
            nv = []
            for v in f.verts:
                if v.index not in mapv:
                    mapv[v.index] = tgt.verts.new(v.co)
                nv.append(mapv[v.index])
            if flip:
                nv.reverse()
            try:
                nf = tgt.faces.new(nv)
                nf.material_index = mi
            except ValueError:
                self.dropped = getattr(self, 'dropped', 0) + 1
        b2.free()

    # side window etc. helpers
    def side_mapper(self, sx):
        return lambda yy, z: Vector((sx * 6.0, self.Y(yy), z))

    def top_mapper(self):
        return lambda x, yy: Vector((x, self.Y(yy), 6.0))

    def front_mapper(self):
        return lambda x, z: Vector((x, -12.0, z))

    def rear_mapper(self):
        return lambda x, z: Vector((x, 12.0, z))

    # ------------------------------------------------------------ text
    def text(self, gname, mat, string, width, mapper, direction, ab, mirror=False, depth=0.012, offset=0.0015, bold=0.025):
        cu = bpy.data.curves.new('txt', 'FONT')
        cu.body = string
        cu.size = 1.0
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.extrude = 0.03
        cu.offset = bold
        cu.resolution_u = 2
        ob = bpy.data.objects.new('txt', cu)
        bpy.context.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
        bm = bmesh.new()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        xs = [v.co.x for v in bm.verts]
        zs = [v.co.z for v in bm.verts]
        sc = width / (max(xs) - min(xs))
        zmin = min(zs)
        d = Vector(direction).normalized()
        tgt, _ = self.group(gname)
        mi = self.mat_index(gname, mat)
        mapv = {}
        for v in bm.verts:
            lx, ly, w = v.co.x * sc, v.co.y * sc, (v.co.z - zmin) * sc
            if mirror:
                lx = -lx
            a, b = ab(lx, ly)
            loc, nor = self.cast(mapper(a, b), d)
            if loc is None:
                self.warn += 1
                loc, nor = Vector(mapper(a, b)), -d
            mapv[v.index] = tgt.verts.new(loc + nor * (offset + min(w, depth)))
        fs = []
        for f in bm.faces:
            try:
                nf = tgt.faces.new([mapv[v.index] for v in f.verts])
                nf.material_index = mi
                fs.append(nf)
            except ValueError:
                pass
        bmesh.ops.recalc_face_normals(tgt, faces=fs)
        bm.free()

    # ------------------------------------------------------------ solid boxes (tapered)
    def tbox(self, gname, mat, cx, cy, z0, h, w0, d0, w1, d1, shift_y=0.0):
        """Tapered box: bottom w0 x d0 at z0, top w1 x d1 at z0+h, top shifted in y by shift_y. centre cx,cy."""
        bm, _ = self.group(gname)
        mi = self.mat_index(gname, mat)
        v = []
        for (w, d, z, sy) in ((w0, d0, z0, 0), (w1, d1, z0 + h, shift_y)):
            for sxn, syn in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v.append(bm.verts.new((cx + sxn * w / 2, cy + sy + syn * d / 2, z)))
        fs = [bm.faces.new(q) for q in ((v[0], v[1], v[2], v[3]), (v[4], v[7], v[6], v[5]), (v[0], v[4], v[5], v[1]),
                                        (v[1], v[5], v[6], v[2]), (v[2], v[6], v[7], v[3]), (v[3], v[7], v[4], v[0]))]
        for f in fs:
            f.material_index = mi
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        return fs

    def bevel_faces(self, gname, fs, off=0.01, seg=2):
        bm, _ = self.group(gname)
        edges = set()
        for f in fs:
            for e in f.edges:
                edges.add(e)
        bmesh.ops.bevel(bm, geom=list(edges), offset=off, segments=seg, affect='EDGES')

    # ------------------------------------------------------------ wheels
    def lathe_closed(self, bm, profile, segs, mi, xc=0.0, sgn=1):
        """profile = list of (radius, x) closed loop. revolve about X axis. returns faces"""
        rings = []
        for (r, x) in profile:
            ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                ring.append(bm.verts.new((xc + sgn * x, r * math.cos(a), r * math.sin(a))))
            rings.append(ring)
        n = len(profile)
        fs = []
        for i in range(n):
            j = (i + 1) % n
            for k in range(segs):
                k2 = (k + 1) % segs
                f = bm.faces.new((rings[i][k], rings[i][k2], rings[j][k2], rings[j][k]))
                f.material_index = mi
                fs.append(f)
        return fs

    def disc_solid(self, bm, r0, r1, x0, x1, segs, mi, sgn=1):
        prof = [(r0, x0), (r1, x0), (r1, x1), (r0, x1)]
        return self.lathe_closed(bm, prof, segs, mi, 0.0, sgn)

    def build_wheels(self):
        s = self.s
        R, wd, rr = s['r'], s['tyre_w'], s['rim_r']
        segs = s.get('wheel_segs', 28)
        w2 = wd / 2
        nspoke = s.get('spokes', 5)
        self.wheel_objs = []
        for nm, yy, sx in (('wheel_fl', s['fo'], 1), ('wheel_fr', s['fo'], -1),
                           ('wheel_rl', s['fo'] + s['wb'], 1), ('wheel_rr', s['fo'] + s['wb'], -1)):
            bm = bmesh.new()
            # tyre (profile coords x: outboard positive)
            R1 = R
            prof = [(rr, -w2 * 0.88), (rr + (R - rr) * 0.25, -w2 * 0.98), (rr + (R - rr) * 0.75, -w2 * 0.97),
                    (R * 0.985, -w2 * 0.80), (R, -w2 * 0.5), (R, w2 * 0.5), (R * 0.985, w2 * 0.80),
                    (rr + (R - rr) * 0.75, w2 * 0.97), (rr + (R - rr) * 0.25, w2 * 0.98), (rr, w2 * 0.88)]
            fs = self.lathe_closed(bm, prof, segs, 0, 0.0, sgn=sx)
            bmesh.ops.recalc_face_normals(bm, faces=fs)
            # rim lip/barrel
            prof2 = [(rr * 0.97, w2 * 0.9), (rr * 1.0, w2 * 0.84), (rr * 0.93, w2 * 0.74), (rr * 0.90, -w2 * 0.6),
                     (rr * 0.87, -w2 * 0.6), (rr * 0.91, w2 * 0.74), (rr * 0.95, w2 * 0.86)]
            fs = self.lathe_closed(bm, prof2, segs, 1, 0.0, sgn=sx)
            bmesh.ops.recalc_face_normals(bm, faces=fs)
            # dark backing plate
            fs = self.disc_solid(bm, 0.0, rr * 0.9, w2 * 0.26, w2 * 0.30, segs, 2, sx)
            bmesh.ops.recalc_face_normals(bm, faces=fs)
            # brake disc (annulus)
            fs = self.lathe_closed(bm, [(rr * 0.42, w2 * 0.34), (rr * 0.80, w2 * 0.34), (rr * 0.80, w2 * 0.42), (rr * 0.42, w2 * 0.42)],
                                   segs, 3, 0.0, sx)
            bmesh.ops.recalc_face_normals(bm, faces=fs)
            # hub cap
            fs = self.disc_solid(bm, 0.0, rr * 0.2, w2 * 0.30, w2 * 0.72, 12, 3, sx)
            bmesh.ops.recalc_face_normals(bm, faces=fs)
            # spokes
            r0, r1 = rr * 0.12, rr * 0.9
            xb, xf = w2 * 0.46, w2 * 0.66
            for k in range(nspoke):
                th = 2 * math.pi * k / nspoke + 0.3
                d0, d1 = 0.26, 0.15
                vv = []
                for x in (xb, xf):
                    for (r, d) in ((r0, -d0), (r0, d0), (r1, d1), (r1, -d1)):
                        a = th + d
                        vv.append(bm.verts.new((sx * x, r * math.cos(a), r * math.sin(a))))
                quads = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
                fs = []
                for q in quads:
                    f = bm.faces.new([vv[i] for i in q])
                    f.material_index = 1
                    fs.append(f)
                bmesh.ops.recalc_face_normals(bm, faces=fs)
            for f in bm.faces:
                f.smooth = True
            mesh = bpy.data.meshes.new(nm)
            bm.to_mesh(mesh)
            bm.free()
            for mn in ('Tyre', 'Rim', 'Trim', 'Chrome'):
                mesh.materials.append(self.mats[mn])
            ob = bpy.data.objects.new(nm, mesh)
            xc = sx * (s['hw'] - 0.012 - w2 * 0.98)
            ob.location = (xc, self.Y(yy), R)
            bpy.context.collection.objects.link(ob)
            self.wheel_objs.append(ob)

    # ------------------------------------------------------------ police equipment
    def add_glass(self, side_windows, windscreen, rear_window, off=0.006):
        """side_windows: polygons in (yy, z); windscreen/rear_window: polygons in (x, yy)."""
        for sx in (1, -1):
            for poly in side_windows:
                self.patch('glass', 'Glass', chaikin(poly, 2), self.side_mapper(sx), (-sx, 0, 0), offset=off, maxlen=0.07)
        self.patch('glass', 'Glass', chaikin(windscreen, 2), self.top_mapper(), (0, 0, -1), offset=off, maxlen=0.08)
        if rear_window is not None:
            self.patch('glass', 'Glass', chaikin(rear_window, 2), self.top_mapper(), (0, 0, -1), offset=off, maxlen=0.08)

    def surround(self, outline, mapper, direction, grow=1.15, offset=0.002):
        cx = sum(p[0] for p in outline) / len(outline)
        cy = sum(p[1] for p in outline) / len(outline)
        o2 = [(cx + (a - cx) * grow, cy + (b - cy) * grow) for a, b in outline]
        self.patch('trim', 'Trim', o2, mapper, direction, offset=offset, maxlen=0.03)

    def side_band(self, y0, y1, z0, rowh, rows=2, tilelen=0.24, skip=None):
        n = max(1, round((y1 - y0) / tilelen))
        tl = (y1 - y0) / n
        for sx in (1, -1):
            mp = self.side_mapper(sx)
            dr = (-sx, 0, 0)
            for row in range(rows):
                for i in range(n):
                    a0, a1 = y0 + i * tl, y0 + (i + 1) * tl
                    b0, b1 = z0 + row * rowh, z0 + (row + 1) * rowh
                    pts = [(a0, b0), (a1, b0), (a1, b1), (a0, b1), ((a0 + a1) / 2, (b0 + b1) / 2)]
                    if not self.ok_pts(mp, dr, pts, nmin=0.75):
                        continue
                    blue = (i + row) % 2 == 0
                    self.patch('livery_blue' if blue else 'livery_yellow', 'Livery_Blue' if blue else 'Livery_Yellow',
                               rect(a0, a1, b0, b1), mp, dr, offset=0.004, maxlen=0.09)
            # dark pin-stripes above and below
            for (b0, b1) in ((z0 - 0.025, z0), (z0 + rows * rowh, z0 + rows * rowh + 0.025)):
                self.patch('livery_dark', 'Livery_Dark', rect(y0, y1, b0, b1), mp, dr, offset=0.004, maxlen=0.12)

    def back_band(self, xh, z0, rowh, rows=2, tilelen=0.22, front=False):
        n = max(1, round(2 * xh / tilelen))
        tl = 2 * xh / n
        mp = self.front_mapper() if front else self.rear_mapper()
        dr = (0, 1, 0) if front else (0, -1, 0)
        for row in range(rows):
            for i in range(n):
                a0, a1 = -xh + i * tl, -xh + (i + 1) * tl
                b0, b1 = z0 + row * rowh, z0 + (row + 1) * rowh
                pts = [(a0, b0), (a1, b0), (a1, b1), (a0, b1), ((a0 + a1) / 2, (b0 + b1) / 2)]
                if not self.ok_pts(mp, dr, pts, nmin=0.6):
                    continue
                blue = (i + row) % 2 == 0
                self.patch('livery_blue' if blue else 'livery_yellow', 'Livery_Blue' if blue else 'Livery_Yellow',
                           rect(a0, a1, b0, b1), mp, dr, offset=0.004, maxlen=0.09)

    def side_sill(self, y0, y1, z0, z1):
        for sx in (1, -1):
            mp = self.side_mapper(sx)
            dr = (-sx, 0, 0)
            self.patch('trim', 'Trim', rect(y0, y1, z0, z1), mp, dr, offset=0.0035, maxlen=0.12, reject_bad=True)

    def door_line(self, yy, z0, z1, w=0.006):
        for sx in (1, -1):
            mp = self.side_mapper(sx)
            dr = (-sx, 0, 0)
            if self.ok_pts(mp, dr, [(yy, z0), (yy, z1), (yy, (z0 + z1) / 2)], nmin=0.7):
                self.patch('trim', 'Trim', rect(yy - w / 2, yy + w / 2, z0, z1), mp, dr, offset=0.0025, maxlen=0.1)

    def handle(self, yy, z, length=0.13, h=0.022):
        for sx in (1, -1):
            mp = self.side_mapper(sx)
            dr = (-sx, 0, 0)
            self.patch('trim', 'Trim', rrect(yy - length / 2, yy + length / 2, z - h / 2, z + h / 2, 1), mp, dr, offset=0.006, maxlen=0.05)

    def lightbar(self, yy, width, depth, height=0.05, mat_pairs=None):
        """roof light bar: outer modules blue, inner modules red, black base + feet."""
        y = self.Y(yy)
        zs = []
        for x in (-width / 2, -width / 4, 0, width / 4, width / 2):
            for dy in (-depth / 2, 0, depth / 2):
                loc, nor = self.cast((x, y + dy, 6), (0, 0, -1))
                zs.append(loc.z)
        zr = min(zs)
        zb = max(zs) + 0.012
        # feet
        for sx in (-1, 1):
            self.tbox('trim', 'Trim', sx * width * 0.34, y, zr - 0.02, zb - zr + 0.02, 0.05, depth * 0.85, 0.05, depth * 0.85)
        # base slab
        fs = self.tbox('trim', 'Trim', 0, y, zb, 0.022, width, depth, width - 0.02, depth - 0.02)
        zt = zb + 0.022
        # centre divider
        self.tbox('trim', 'Trim', 0, y, zt, height * 0.9, 0.05, depth * 0.8, 0.04, depth * 0.55)
        # modules: inner red, outer blue
        mw = width * 0.5 - 0.03
        inner = (width / 2 - 0.03) * 0.46
        for sx in (-1, 1):
            # red inner
            cx = sx * (0.025 + inner / 2 + 0.005)
            fs = self.tbox('lightbar_red', 'Light_Red', cx, y, zt, height, inner, depth * 0.94, inner - 0.035, depth * 0.62)
            self.bevel_faces('lightbar_red', fs, 0.012, 2)
            # blue outer
            ow = width / 2 - 0.03 - inner - 0.035
            cx2 = sx * (0.025 + inner + 0.01 + ow / 2)
            fs = self.tbox('lightbar_blue', 'Light_Blue', cx2, y, zt, height, ow, depth * 0.94, ow - 0.035, depth * 0.62)
            self.bevel_faces('lightbar_blue', fs, 0.012, 2)

    def mirror(self, yy, x, z, w=0.13, d=0.1, h=0.10):
        for sx in (-1, 1):
            fs = self.tbox('mirrors', 'Paint', sx * x, self.Y(yy), z, h, w, d, w * 0.8, d * 0.75, shift_y=d * 0.1)
            self.bevel_faces('mirrors', fs, 0.012, 2)
            # stem towards body
            self.tbox('mirrors', 'Paint', sx * (x - 0.07), self.Y(yy) + 0.02, z - 0.03, 0.05, 0.16, 0.07, 0.12, 0.05)


    # ------------------------------------------------------------ round 2: transparent windows + interior + officers
    def cut_windows(self, cell=0.05):
        """Remove body faces lying under the glass patches so the interior shows through the translucent glass."""
        bm, _ = self.groups['body']
        gb = bmesh.new()
        tmp = bpy.data.meshes.new('t')
        self.groups['glass'][0].to_mesh(tmp)
        gb.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        bmesh.ops.triangulate(gb, faces=gb.faces[:])
        gtree = BVHTree.FromBMesh(gb)
        gb.free()

        def near(p, r):
            loc, n, i, dist = gtree.find_nearest(p, r)
            return loc is not None
        for it in range(6):
            bmesh.ops.triangulate(bm, faces=bm.faces[:])
            todo = set()
            for f in bm.faces:
                if any(e.calc_length() > cell for e in f.edges):
                    pts = [v.co for v in f.verts] + [f.calc_center_median()]
                    if any(near(p, 0.03) for p in pts):
                        for e in f.edges:
                            if e.calc_length() > cell:
                                todo.add(e)
            if not todo:
                break
            bmesh.ops.subdivide_edges(bm, edges=list(todo), cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        kill = []
        for f in bm.faces:
            pts = [v.co for v in f.verts] + [f.calc_center_median()]
            if all(near(p, 0.012) for p in pts):
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        print('cut_windows: removed', len(kill), 'faces')

    def limb(self, g, mat, p0, p1, r0, r1, sides=6):
        bm, _ = self.group(g)
        mi = self.mat_index(g, mat)
        a, b = Vector(p0), Vector(p1)
        ax = (b - a).normalized()
        up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
        u = ax.cross(up).normalized()
        v = ax.cross(u).normalized()
        r0s, r1s = [], []
        for k in range(sides):
            t = 2 * math.pi * k / sides
            d = u * math.cos(t) + v * math.sin(t)
            r0s.append(bm.verts.new(a + d * r0))
            r1s.append(bm.verts.new(b + d * r1))
        fs = []
        for k in range(sides):
            k2 = (k + 1) % sides
            fs.append(bm.faces.new((r0s[k], r0s[k2], r1s[k2], r1s[k])))
        fs.append(bm.faces.new(r0s[::-1]))
        fs.append(bm.faces.new(r1s))
        for f in fs:
            f.material_index = mi
        bmesh.ops.recalc_face_normals(bm, faces=fs)

    def blob(self, g, mat, c, rx, ry, rz, sub=2):
        bm, _ = self.group(g)
        mi = self.mat_index(g, mat)
        r = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        for v in r['verts']:
            v.co = Vector((c[0] + v.co.x * rx, c[1] + v.co.y * ry, c[2] + v.co.z * rz))
        for f in bm.faces:
            if all(v in r['verts'] for v in f.verts):
                f.material_index = mi

    def torus(self, g, mat, c, R, rr, tilt, nu=16, nv=6):
        bm, _ = self.group(g)
        mi = self.mat_index(g, mat)
        rot = Matrix.Rotation(tilt, 3, 'X')
        vs = []
        for i in range(nu):
            a = 2 * math.pi * i / nu
            row = []
            for j in range(nv):
                b = 2 * math.pi * j / nv
                rad = R + rr * math.cos(b)
                p = Vector((rad * math.cos(a), rr * math.sin(b), rad * math.sin(a)))  # ring in XZ, axis = Y
                row.append(bm.verts.new(Vector(c) + rot @ p))
            vs.append(row)
        fs = []
        for i in range(nu):
            for j in range(nv):
                f = bm.faces.new((vs[i][j], vs[(i + 1) % nu][j], vs[(i + 1) % nu][(j + 1) % nv], vs[i][(j + 1) % nv]))
                f.material_index = mi
                fs.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=fs)

    def seat(self, cx, yy, ztop, w=0.46, depth=0.46, back_h=0.55, head=True, g='interior'):
        y = self.Y(yy)
        zc = ztop - 0.12
        self.tbox(g, 'Interior', cx, y, zc, 0.12, w, depth, w - 0.02, depth - 0.02)            # cushion
        self.tbox(g, 'Interior', cx, y + depth / 2 + 0.02, ztop - 0.02, back_h, w, 0.10, w - 0.06, 0.09, shift_y=0.12)  # back (leans back)
        if head:
            self.tbox(g, 'Interior', cx, y + depth / 2 + 0.02 + 0.125, ztop + back_h - 0.02, 0.15, 0.22, 0.08, 0.20, 0.07)  # headrest

    def interior(self, I):
        """I: dict of cabin layout (yy distances from front, heights z). Right-hand drive: driver at -X."""
        g = 'interior'
        Y = self.Y
        hw = I['hw_in']
        # floor, roof lining, parcel shelf
        self.tbox(g, 'Interior', 0, Y((I['dash_y0'] + I['bench_back_y']) / 2), I['floor_z'], 0.03, 2 * hw - 0.1, I['bench_back_y'] - I['dash_y0'], 2 * hw - 0.1, I['bench_back_y'] - I['dash_y0'])
        self.tbox(g, 'Interior', 0, Y((I['roof_y0'] + I['roof_y1']) / 2), I['roof_z'] - 0.02, 0.02, 2 * I['roof_hw'], I['roof_y1'] - I['roof_y0'], 2 * I['roof_hw'], I['roof_y1'] - I['roof_y0'])
        self.tbox(g, 'Interior', 0, Y((I['bench_back_y'] + I['shelf_y1']) / 2), I['shelf_z'], 0.025, 2 * I['shelf_hw'], I['shelf_y1'] - I['bench_back_y'], 2 * I['shelf_hw'], I['shelf_y1'] - I['bench_back_y'])
        # door cards
        for sx in (-1, 1):
            self.tbox(g, 'Interior', sx * (hw - 0.01), Y((I['dash_y1'] + I['bench_back_y']) / 2), I['card_z0'], I['card_z1'] - I['card_z0'], 0.03, I['bench_back_y'] - I['dash_y1'], 0.03, I['bench_back_y'] - I['dash_y1'])
        # dashboard
        dy0, dy1, dz = I['dash_y0'], I['dash_y1'], I['dash_z']
        fs = self.tbox(g, 'Interior', 0, Y((dy0 + dy1) / 2), dz - 0.20, 0.20, 2 * hw - 0.08, dy1 - dy0, 2 * hw - 0.08, (dy1 - dy0) * 0.75, shift_y=(dy1 - dy0) * 0.12)
        xd = -I['seat_x']
        # binnacle + dials
        by = Y(dy1) - 0.02
        self.tbox(g, 'Interior', xd, by, dz, 0.09, 0.40, 0.17, 0.38, 0.12, shift_y=0.02)
        for dx in (-0.09, 0.09):
            self.tbox(g, 'Emit_Dash', xd + dx, by + 0.09, dz + 0.02, 0.05, 0.075, 0.004, 0.075, 0.004)
        # steering column + wheel
        wy, wz = Y(I['wheel_y']), I['wheel_z']
        self.limb(g, 'Interior', (xd, wy - 0.12, wz - 0.12), (xd, wy, wz), 0.028, 0.03)
        self.torus(g, 'Interior', (xd, wy, wz), 0.17, 0.016, math.radians(28))
        self.limb(g, 'Interior', (xd, wy, wz), (xd + 0.17, wy + 0.0, wz + 0.0), 0.012, 0.012, 4)
        # centre stack, radio screen, console
        sy = Y(dy1) - 0.02
        self.tbox(g, 'Interior', 0, sy, dz - 0.30, 0.30, 0.20, 0.09, 0.20, 0.07, shift_y=0.02)
        self.tbox(g, 'Emit_Dash', 0, sy + 0.05, dz - 0.10, 0.045, 0.12, 0.004, 0.12, 0.004)
        self.tbox(g, 'Emit_Dash', 0, sy + 0.05, dz - 0.18, 0.025, 0.10, 0.004, 0.10, 0.004)
        cy0, cy1 = dy1 + 0.0, I['seat_y'] + 0.15
        self.tbox(g, 'Interior', 0, Y((cy0 + cy1) / 2), I['floor_z'], I['console_z'] - I['floor_z'], 0.22, cy1 - cy0, 0.18, cy1 - cy0 - 0.05)
        # front seats
        for sx in (-1, 1):
            self.seat(sx * I['seat_x'], I['seat_y'], I['seat_z'], back_h=I['back_h'])
        # cage / partition behind front seats
        cy = Y(I['cage_y'])
        z0, z1 = I['seat_z'] + 0.05, I['cage_top']
        n = int(2 * hw / 0.09)
        for i in range(n + 1):
            x = -hw + 0.04 + i * (2 * hw - 0.08) / n
            self.tbox(g, 'Interior', x, cy, z0, z1 - z0, 0.02, 0.02, 0.02, 0.02)
        for z in (z0, (z0 + z1) / 2, z1 - 0.02):
            self.tbox(g, 'Interior', 0, cy, z, 0.025, 2 * hw - 0.06, 0.03, 2 * hw - 0.06, 0.03)
        # rear bench
        self.seat(0, I['bench_y'], I['bench_z'], w=2 * hw - 0.2, depth=0.42, back_h=I['bench_back_h'], head=False)

    def officer(self, name, cx, yy, zseat, wheel=None, wheel_hands=True, hip_back=0.0):
        """Low-poly seated officer: hi-vis jacket, dark trousers, police cap. wheel=(y,z) hands on wheel."""
        g = name
        y = self.Y(yy) + hip_back
        zh = zseat + 0.0
        lean = 0.07
        # torso (hi-vis yellow jacket), leaning back slightly
        self.tbox(g, 'Livery_Yellow', cx, y + 0.05, zh + 0.02, 0.50, 0.40, 0.22, 0.46, 0.22, shift_y=lean)
        # dark reflective band on the jacket
        self.tbox(g, 'Livery_Dark', cx, y + 0.05 + lean * 0.35, zh + 0.20, 0.07, 0.405, 0.225, 0.405, 0.225, shift_y=lean * 0.14)
        hy = y + 0.05 + lean
        self.limb(g, 'Driver', (cx, hy - 0.01, zh + 0.50), (cx, hy - 0.02, zh + 0.58), 0.05, 0.045)     # neck
        hz = zh + 0.68
        self.blob(g, 'Driver', (cx, hy - 0.02, hz), 0.09, 0.10, 0.11)                                   # head
        # police cap: dark crown, blue/white band, peak
        self.limb(g, 'Livery_Dark', (cx, hy - 0.02, hz + 0.045), (cx, hy - 0.02, hz + 0.115), 0.112, 0.118, 10)
        self.limb(g, 'Livery_Blue', (cx, hy - 0.02, hz + 0.04), (cx, hy - 0.02, hz + 0.065), 0.116, 0.116, 10)
        self.tbox(g, 'Livery_Dark', cx, hy - 0.13, hz + 0.05, 0.012, 0.17, 0.08, 0.15, 0.06)
        # legs
        for sx in (-1, 1):
            hx = cx + sx * 0.10
            self.limb(g, 'Livery_Dark', (hx, y + 0.02, zh + 0.07), (hx, y - 0.40, zh + 0.13), 0.075, 0.062)
            self.limb(g, 'Livery_Dark', (hx, y - 0.40, zh + 0.13), (hx, y - 0.50, zseat - 0.28), 0.062, 0.05)
        # arms
        shy, shz = hy - 0.0, zh + 0.46
        for sx in (-1, 1):
            sh = (cx + sx * 0.22, shy, shz)
            if wheel is not None:
                wy, wz = self.Y(wheel[0]), wheel[1]
                hand = (cx + sx * 0.13, wy + 0.05, wz + sx * 0.0 - 0.0)
                el = (cx + sx * 0.26, (shy + wy) / 2 - 0.03, (shz + wz) / 2 - 0.12)
            else:
                hand = (cx + sx * 0.13, y - 0.28, zh + 0.20)
                el = (cx + sx * 0.25, y - 0.04, zh + 0.22)
            self.limb(g, 'Livery_Yellow', sh, el, 0.058, 0.05)
            self.limb(g, 'Livery_Yellow', el, hand, 0.05, 0.042)
            self.blob(g, 'Driver', hand, 0.04, 0.04, 0.04, 1)

    # ------------------------------------------------------------ finalize groups to objects
    def finalize(self):
        self.objs = {}
        for name, (bm, ml) in self.groups.items():
            if not bm.faces:
                continue
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(50):
                    e.smooth = False
            for f in bm.faces:
                f.smooth = name not in FLAT_GROUPS
            mesh = bpy.data.meshes.new(name)
            bm.to_mesh(mesh)
            for mn in ml:
                mesh.materials.append(self.mats[mn])
            ob = bpy.data.objects.new(name, mesh)
            bpy.context.collection.objects.link(ob)
            self.objs[name] = ob

    def tri_count(self):
        n = 0
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH':
                n += sum(max(1, len(p.vertices) - 2) for p in ob.data.polygons)
        return n

    # ------------------------------------------------------------ export + verify + preview
    def export(self):
        path = '%s/%s.glb' % (OUT_DIR, self.name)
        os.makedirs(OUT_DIR, exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                                  export_materials='EXPORT', export_cameras=False, export_lights=False)
        return path

    def verify_and_render(self, path, cams=None):
        tris = self.tri_count()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=path)
        mn = Vector((1e9, 1e9, 1e9))
        mx = Vector((-1e9, -1e9, -1e9))
        for ob in bpy.context.scene.objects:
            if ob.type == 'MESH':
                for c in ob.bound_box:
                    w = ob.matrix_world @ Vector(c)
                    for i in range(3):
                        mn[i] = min(mn[i], w[i])
                        mx[i] = max(mx[i], w[i])
        print('REIMPORT bbox min', tuple(round(v, 3) for v in mn), 'max', tuple(round(v, 3) for v in mx))
        print('size  W(x) %.3f  L(y) %.3f  H(z) %.3f   tris %d' % (mx.x - mn.x, mx.y - mn.y, mx.z - mn.z, tris))
        print('objects:', sorted(o.name for o in bpy.context.scene.objects))
        print('materials:', sorted(m.name for m in bpy.data.materials))
        self.render_rig(mn, mx)

    def render_rig(self, mn, mx):
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_EEVEE'
        sc.render.resolution_x, sc.render.resolution_y = 1000, 640
        sc.render.image_settings.file_format = 'PNG'
        try:
            sc.eevee.taa_render_samples = 24
        except Exception:
            pass
        sc.view_settings.view_transform = 'Standard'
        w = bpy.data.worlds.new('w')
        sc.world = w
        w.use_nodes = True
        bg = w.node_tree.nodes['Background']
        bg.inputs[0].default_value = (0.42, 0.50, 0.62, 1)
        bg.inputs[1].default_value = 1.1
        # ground
        gm = bpy.data.meshes.new('ground')
        bmg = bmesh.new()
        bmesh.ops.create_grid(bmg, x_segments=1, y_segments=1, size=30)
        bmg.to_mesh(gm)
        bmg.free()
        gmat = bpy.data.materials.new('gnd')
        gmat.diffuse_color = (0.16, 0.16, 0.17, 1)
        gmat.use_nodes = True
        gmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.16, 0.16, 0.17, 1)
        gmat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
        gm.materials.append(gmat)
        go = bpy.data.objects.new('ground', gm)
        bpy.context.collection.objects.link(go)
        for nm, kind, loc, energy, rot in (('sun', 'SUN', (5, -5, 8), 3.5, (math.radians(50), 0, math.radians(35))),
                                           ('fill', 'SUN', (-5, 5, 6), 1.2, (math.radians(60), 0, math.radians(-150)))):
            ld = bpy.data.lights.new(nm, kind)
            ld.energy = energy
            ld.use_shadow = nm != 'fill'
            ld.angle = math.radians(1.0)
            lo = bpy.data.objects.new(nm, ld)
            lo.location = loc
            lo.rotation_euler = rot
            bpy.context.collection.objects.link(lo)
        center = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mx.z) * 0.45))
        L = mx.y - mn.y
        cams = {
            'front34': (L * 0.95, -L * 1.25, 1.9),
            'rear34': (-L * 0.95, L * 1.25, 2.0),
            'side': (L * 2.4, 0.0, 0.9),
            'top': (L * 0.5, -L * 0.6, L * 1.9),
            'front': (0.0, -L * 2.0, 1.1),
            'rear': (0.0, L * 2.0, 1.2),
            'lightbar': (L * 0.5, L * 0.55, 2.7),
            'frontlow': (-L * 0.45, -L * 0.75, 0.6),
            'win34': (L * 0.62, -L * 0.5, 1.0),
            'closefront': (0.9, mn.y - 2.0, 1.0),
            'closerear': (-0.9, mx.y + 2.0, 1.1),
        }
        for nm, pos in cams.items():
            cd = bpy.data.cameras.new(nm)
            cd.lens = 55 if nm not in ('side',) else 90
            if nm in ('lightbar',):
                cd.lens = 70
            if nm.startswith('close'):
                cd.lens = 70
            co = bpy.data.objects.new(nm, cd)
            co.location = pos
            bpy.context.collection.objects.link(co)
            tgt = center if nm != 'lightbar' else Vector((0, 0.0, mx.z - 0.3))
            if nm == 'closefront':
                tgt = Vector((0, mn.y, 0.55))
            if nm == 'closerear':
                tgt = Vector((0, mx.y, 0.7))
            d = tgt - Vector(pos)
            co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            sc.camera = co
            if nm == 'win34':
                co.rotation_euler = (Vector((0, 0.1, 0.95)) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = '%s/%s_%s.png' % (PREV_DIR, self.name, nm)
            bpy.ops.render.render(write_still=True)
            print('rendered', sc.render.filepath)
        # roof-hidden views: strip the glass, light bar and everything above the belt
        cz = self.s.get('cut_z')
        if cz:
            for ob in list(bpy.context.scene.objects):
                if ob.name in ('glass', 'lightbar_red', 'lightbar_blue', 'mirrors', 'strobes'):
                    ob.hide_render = True
                if ob.name in ('body', 'livery_blue', 'livery_yellow', 'livery_dark', 'trim', 'chrome', 'lights', 'plates'):
                    b = bmesh.new()
                    b.from_mesh(ob.data)
                    dead = [f for f in b.faces if f.calc_center_median().z > cz]
                    bmesh.ops.delete(b, geom=dead, context='FACES')
                    b.to_mesh(ob.data)
                    b.free()
            for nm, pos, tg in (('topcut', (0.35, 0.2, L * 1.6), (0, 0.1, 0.8)),
                                ('sidecut', (L * 0.5, -L * 0.45, 2.7), (0, 0.2, 0.8)),
                                ('rearcut', (-L * 0.35, L * 0.5, 2.3), (0, -0.2, 0.9))):
                cd = bpy.data.cameras.new(nm)
                cd.lens = 40
                co = bpy.data.objects.new(nm, cd)
                co.location = pos
                bpy.context.collection.objects.link(co)
                co.rotation_euler = (Vector(tg) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
                sc.camera = co
                sc.render.filepath = '%s/%s_%s.png' % (PREV_DIR, self.name, nm)
                bpy.ops.render.render(write_still=True)


def sh(*a):
    sys.stdout.flush()
