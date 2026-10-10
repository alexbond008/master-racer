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
    mk('Glass', (0.012, 0.016, 0.022), 0.05, 0.3)
    mk('Tyre', (0.025, 0.025, 0.027), 0.85, 0.0)
    mk('Rim', (0.72, 0.73, 0.76), 0.3, 0.9)
    mk('Chrome', (0.9, 0.9, 0.92), 0.12, 1.0)
    mk('Trim', (0.025, 0.025, 0.028), 0.6, 0.0)
    mk('Interior', (0.05, 0.05, 0.055), 0.8, 0.0)
    mk('HeadLight', (1.0, 0.95, 0.8), 0.1, 0.0, (1.0, 0.92, 0.72), 3.0)
    mk('TailLight', (0.8, 0.02, 0.02), 0.2, 0.0, (1.0, 0.04, 0.03), 2.5)
    mk('Plate', (0.93, 0.9, 0.82), 0.5, 0.0)
    mk('Livery_Blue', (0.0, 0.07, 0.42), 0.35, 0.0)
    mk('Livery_Yellow', (1.0, 0.72, 0.0), 0.35, 0.0, (1.0, 0.7, 0.0), 0.25)
    mk('Livery_Dark', (0.012, 0.02, 0.09), 0.4, 0.0)
    mk('Light_Red', (1.0, 0.05, 0.03), 0.2, 0.0, (1.0, 0.04, 0.02), 5.0)
    mk('Light_Blue', (0.05, 0.2, 1.0), 0.2, 0.0, (0.1, 0.25, 1.0), 6.0)
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
        loc, nor, idx, dist = self.surf.ray_cast(Vector(origin), Vector(direction).normalized(), 50.0)
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
    def patch(self, gname, mat, outline, mapper, direction, offset=0.004, maxlen=0.07, depth=0.0):
        d = Vector(direction).normalized()
        b2 = bmesh.new()
        vs = [b2.verts.new((a, b, 0)) for a, b in outline]
        try:
            f = b2.faces.new(vs)
        except ValueError:
            b2.free()
            return
        bmesh.ops.triangulate(b2, faces=[f])
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
            if loc is None:
                miss.append(v)
                continue
            hitn[v.index] = nor
            v.co = loc + nor * offset
        if miss:
            self.warn += 1
            bmesh.ops.delete(b2, geom=miss, context='VERTS')
        b2.faces.ensure_lookup_table()
        b2.normal_update()
        tgt, _ = self.group(gname)
        mi = self.mat_index(gname, mat)
        mapv = {}
        for f in b2.faces:
            ns = Vector()
            for v in f.verts:
                ns += hitn.get(v.index, Vector())
            flip = f.normal.dot(ns) < 0
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
                pass
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
                f.smooth = True
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
        }
        for nm, pos in cams.items():
            cd = bpy.data.cameras.new(nm)
            cd.lens = 55 if nm not in ('side',) else 90
            if nm in ('lightbar',):
                cd.lens = 70
            co = bpy.data.objects.new(nm, cd)
            co.location = pos
            bpy.context.collection.objects.link(co)
            tgt = center if nm != 'lightbar' else Vector((0, 0.0, mx.z - 0.3))
            d = tgt - Vector(pos)
            co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
            sc.camera = co
            sc.render.filepath = '%s/%s_%s.png' % (PREV_DIR, self.name, nm)
            bpy.ops.render.render(write_still=True)
            print('rendered', sc.render.filepath)


def sh(*a):
    sys.stdout.flush()
