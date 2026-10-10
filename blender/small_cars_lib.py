"""Shared helpers for fiat126.py / corsa.py / impreza.py (Blender 5.x, headless, bmesh only).

Conventions (see CONVENTIONS.md): Z-up, 1 unit = 1 m, car front faces -Y, origin on the
ground midway between the axles. Left of the car (driver's left, looking forward) is +X.
"""
import bpy, bmesh, math, os, bisect
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = os.path.expanduser('~/Projects/master-racer')
PREVIEWS = os.path.join(ROOT, 'blender', 'previews')
CARS_OUT = os.path.join(ROOT, 'public', 'models', 'cars')


# ----------------------------------------------------------------- scene / materials
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def make_mat(name, hexcol, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(emit), 1)
        b.inputs['Emission Strength'].default_value = strength
    return m


def standard_materials(paint, rim='#b9bcc0', rim_metal=0.9, rim_rough=0.3, plate='#e9e6d8'):
    return {
        'Paint': make_mat('Paint', paint, 0.25, 0.5),
        'Glass': make_mat('Glass', '#05080c', 0.05, 0.1),
        'Tyre': make_mat('Tyre', '#111111', 0.85, 0.0),
        'Rim': make_mat('Rim', rim, rim_rough, rim_metal),
        'Chrome': make_mat('Chrome', '#d8dade', 0.12, 1.0),
        'Trim': make_mat('Trim', '#141414', 0.6, 0.0),
        'Interior': make_mat('Interior', '#2b2a28', 0.8, 0.0),
        'HeadLight': make_mat('HeadLight', '#fff4dc', 0.1, 0.0, emit='#fff1d0', strength=4.0),
        'TailLight': make_mat('TailLight', '#d01010', 0.2, 0.0, emit='#ff1010', strength=4.0),
        'Plate': make_mat('Plate', plate, 0.4, 0.0),
    }


# ----------------------------------------------------------------- interpolation
def pchip(pts):
    """Monotone cubic Hermite interpolation through (x, y) pairs."""
    pts = sorted(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(xs)
    if n == 1:
        return lambda x: ys[0]
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    if n == 2:
        m = [d[0], d[0]]
    else:
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0:
                m[i] = 0.0
            else:
                w1 = 2 * h[i] + h[i - 1]
                w2 = h[i] + 2 * h[i - 1]
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

        def end(h0, h1, d0, d1):
            v = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
            if v * d0 <= 0:
                return 0.0
            if d0 * d1 <= 0 and abs(v) > 3 * abs(d0):
                return 3 * d0
            return v
        m[0] = end(h[0], h[1], d[0], d[1])
        m[-1] = end(h[-1], h[-2], d[-1], d[-2])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = bisect.bisect_right(xs, x) - 1
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


# ----------------------------------------------------------------- loft body
def fillet_polyline(P, radii, k):
    """P: list of (x,z) with open ends; radii for interior points. Returns points with
    exactly (k+1) points per interior corner so the count is constant between rings."""
    out = [P[0]]
    for i in range(1, len(P) - 1):
        p, a, b = Vector(P[i]), Vector(P[i - 1]), Vector(P[i + 1])
        d1, d2 = a - p, b - p
        l1, l2 = d1.length, d2.length
        r = radii[i - 1]
        if l1 < 1e-6 or l2 < 1e-6:
            out += [tuple(p)] * (k + 1)
            continue
        d1n, d2n = d1 / l1, d2 / l2
        cosang = max(-1.0, min(1.0, d1n.dot(d2n)))
        ang = math.acos(cosang)
        if ang > math.pi - 1e-3 or r < 1e-5:
            out += [tuple(p)] * (k + 1)
            continue
        t = r / math.tan(ang / 2)
        tmax = 0.48 * min(l1, l2)
        if t > tmax:
            t = tmax
        rr = t * math.tan(ang / 2)
        bis = (d1n + d2n).normalized()
        c = p + bis * (rr / math.sin(ang / 2))
        t1 = p + d1n * t
        t2 = p + d2n * t
        v1 = (t1 - c)
        v2 = (t2 - c)
        a1 = math.atan2(v1.y, v1.x)
        a2 = math.atan2(v2.y, v2.x)
        da = a2 - a1
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for j in range(k + 1):
            a = a1 + da * j / k
            out.append((c.x + rr * math.cos(a), c.y + rr * math.sin(a)))
    out.append(P[-1])
    return out


def loft_body(keys, y0, y1, r_front, r_rear, step=0.05, k=5, extra_ys=(), end_seg=6, cap=True):
    """Cross-section loft. keys: dict param -> number or [(y, value)...].
    Params: zb (underside z), zs (shoulder/belt z), zt (top z), hw (half width at shoulder),
    tw (half width of top flat), bw (bottom inset ratio), rt/rs/rb (fillet radii)."""
    F = {}
    for kname, v in keys.items():
        F[kname] = (lambda c: (lambda y: c))(v) if isinstance(v, (int, float)) else pchip(v)
    ys = set()
    for v in keys.values():
        if not isinstance(v, (int, float)):
            for yy, _ in v:
                if y0 <= yy <= y1:
                    ys.add(round(yy, 5))
    n = int((y1 - y0) / step)
    for i in range(n + 1):
        ys.add(round(y0 + (y1 - y0) * i / n, 5))
    for yy in extra_ys:
        ys.add(round(yy, 5))
    for r, base, sgn in ((r_front, y0, 1), (r_rear, y1, -1)):
        if r > 0:
            for j in range(end_seg + 1):
                d = r * (1 - math.cos(j * math.pi / 2 / end_seg))
                ys.add(round(base + sgn * d, 5))
    ys = sorted(ys)

    def inset(y):
        i = 0.0
        for r, d in ((r_front, y - y0), (r_rear, y1 - y)):
            if r > 0 and d < r:
                i = max(i, r - math.sqrt(max(r * r - (r - d) ** 2, 0.0)))
        return i

    bm = bmesh.new()
    rings = []
    for y in ys:
        zb, zs, zt = F['zb'](y), F['zs'](y), F['zt'](y)
        hw, tw = F['hw'](y), F['tw'](y)
        bw = F['bw'](y) if 'bw' in F else 0.93
        rt = F['rt'](y) if 'rt' in F else 0.08
        rs = F['rs'](y) if 'rs' in F else 0.10
        rb = F['rb'](y) if 'rb' in F else 0.05
        ins = inset(y)
        if ins > 0:
            hw = max(hw - ins, 0.05)
            tw = max(min(tw - ins, hw), 0.03)
            zt -= ins
            zb += ins
        zs = min(max(zs, zb + 0.06), zt - 0.03)
        P = [(0, zt), (tw, zt), (hw, zs), (hw * bw, zb), (0, zb)]
        H = fillet_polyline(P, [rt, rs, rb], k)
        full = list(H)
        for p in reversed(H[1:-1]):
            full.append((-p[0], p[1]))
        rings.append([bm.verts.new((p[0], y, p[1])) for p in full])
    nv = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for j in range(nv):
            j2 = (j + 1) % nv
            try:
                bm.faces.new((a[j], a[j2], b[j2], b[j]))
            except ValueError:
                pass
    if cap:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def cyl_x(bm, x0, x1, cy, cz, r, seg=48):
    """closed cylinder along X from x0 to x1 centred (cy,cz)."""
    m = Matrix.Translation(((x0 + x1) / 2, cy, cz)) @ Matrix.Rotation(math.pi / 2, 4, 'Y')
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r,
                          depth=abs(x1 - x0), matrix=m)


def boolean_cut(bm, cutter_bm):
    me = bpy.data.meshes.new('_b')
    bm.to_mesh(me)
    ob = bpy.data.objects.new('_b', me)
    mc = bpy.data.meshes.new('_c')
    cutter_bm.to_mesh(mc)
    oc = bpy.data.objects.new('_c', mc)
    sc = bpy.context.scene.collection
    sc.objects.link(ob)
    sc.objects.link(oc)
    mod = ob.modifiers.new('cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = oc
    mod.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me2 = ev.to_mesh()
    out = bmesh.new()
    out.from_mesh(me2)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.objects.remove(oc)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(mc)
    return out


# ----------------------------------------------------------------- surface projection ("decals")
class Surf:
    def __init__(self, bm):
        bm2 = bm.copy()
        bmesh.ops.triangulate(bm2, faces=bm2.faces[:])
        self.bvh = BVHTree.FromBMesh(bm2)
        bm2.free()

    def ray(self, o, d):
        loc, nor, idx, dist = self.bvh.ray_cast(o, d)
        return loc, nor


def side(s):
    return lambda a, b: (Vector((s * 4, a, b)), Vector((-s, 0, 0)))      # outline (y, z)


def front():
    return lambda a, b: (Vector((a, -8, b)), Vector((0, 1, 0)))           # outline (x, z)


def rear():
    return lambda a, b: (Vector((a, 8, b)), Vector((0, -1, 0)))           # outline (x, z)


def top():
    return lambda a, b: (Vector((a, b, 4)), Vector((0, 0, -1)))           # outline (x, y)


def _hit(surf, frame, a, b, off):
    o, d = frame(a, b)
    loc, nor = surf.ray(o, d)
    if loc is None:
        return None, None
    return loc + nor * off, nor


def project_poly(surf, pts, frame, off=0.005, cuts=3):
    """Fill 2D polygon, subdivide, and drape onto the surface. returns (verts, faces)."""
    bm = bmesh.new()
    vs = [bm.verts.new((a, b, 0)) for a, b in pts]
    f = bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=[f])
    if cuts > 0:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    bm.verts.ensure_lookup_table()
    pos, nors, bad = [], [], 0
    for v in bm.verts:
        p, n = _hit(surf, frame, v.co.x, v.co.y, off)
        if p is None:
            bad += 1
            p, n = Vector((0, 0, 0)), None
        pos.append(p)
        nors.append(n)
    if bad:
        print('  [decal] %d/%d verts missed the surface' % (bad, len(bm.verts)))
        if len(nors) - bad < 3:
            bm.free()
            return [], []
        for i, v in enumerate(bm.verts):
            if nors[i] is None:
                j = min((j for j in range(len(pos)) if nors[j] is not None),
                        key=lambda j: (bm.verts[j].co - v.co).length)
                pos[i] = pos[j]
                nors[i] = nors[j]
    faces = []
    for fc in bm.faces:
        idx = [v.index for v in fc.verts]
        if len(idx) < 3:
            continue
        a, b, c = pos[idx[0]], pos[idx[1]], pos[idx[2]]
        nrm = (b - a).cross(c - a)
        avg = nors[idx[0]] + nors[idx[1]] + nors[idx[2]]
        if nrm.length < 1e-12:
            continue
        if nrm.dot(avg) < 0:
            idx = idx[::-1]
        faces.append(idx)
    bm.free()
    return pos, faces


def densify(pts, step):
    out = []
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        n = max(1, int((b - a).length / step))
        for j in range(n):
            out.append(a.lerp(b, j / n))
    out.append(Vector(pts[-1]))
    return out


def project_strip(surf, pts, width, frame, off=0.004, step=0.03):
    """Thin ribbon along a 2D polyline draped on the surface (door lines, slats, trim)."""
    sp = densify(pts, step)
    verts, nors = [], []
    for i, p in enumerate(sp):
        if i == 0:
            t = sp[1] - sp[0]
        elif i == len(sp) - 1:
            t = sp[-1] - sp[-2]
        else:
            t = sp[i + 1] - sp[i - 1]
        t = Vector((t.x, t.y)).normalized()
        nrm = Vector((-t.y, t.x)) * width / 2
        for sgn in (1, -1):
            a, b = p.x + sgn * nrm.x, p.y + sgn * nrm.y
            pp, nn = _hit(surf, frame, a, b, off)
            if pp is None:
                pp = verts[-2] if len(verts) >= 2 else Vector((0, 0, 0))
                nn = nors[-2] if len(nors) >= 2 else Vector((0, 0, 1))
            verts.append(pp)
            nors.append(nn)
    faces = []
    for i in range(len(sp) - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        q = [a, b, c, d]
        nrm = (verts[b] - verts[a]).cross(verts[d] - verts[a])
        if nrm.dot(nors[a]) < 0:
            q = q[::-1]
        faces.append(q)
    return verts, faces


def circle_pts(cx, cy, rx, ry=None, n=20, rot=0.0):
    ry = rx if ry is None else ry
    return [(cx + rx * math.cos(2 * math.pi * i / n + rot), cy + ry * math.sin(2 * math.pi * i / n + rot))
            for i in range(n)]


def rrect_pts(cx, cy, w, h, r, k=3):
    """rounded rectangle outline, counter-clockwise."""
    r = min(r, w / 2, h / 2)
    out = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = cx + sx * (w / 2 - r), cy + sy * (h / 2 - r)
        for j in range(k + 1):
            a = math.radians(a0 + 90 * j / k)
            out.append((ccx + r * math.cos(a), ccy + r * math.sin(a)))
    return out


# ----------------------------------------------------------------- composing objects
class Car:
    def __init__(self):
        self.objs = {}      # name -> (bmesh, [mat names])
        self.mats = None

    def bm(self, obj):
        if obj not in self.objs:
            self.objs[obj] = (bmesh.new(), [])
        return self.objs[obj]

    def set_bm(self, obj, bm, matname):
        self.objs[obj] = (bm, [matname])
        for f in bm.faces:
            f.material_index = 0

    def add(self, obj, matname, verts, faces):
        if not len(verts):
            return
        bm, mats = self.bm(obj)
        if matname not in mats:
            mats.append(matname)
        mi = mats.index(matname)
        vs = [bm.verts.new(v) for v in verts]
        for f in faces:
            try:
                fc = bm.faces.new([vs[i] for i in f])
                fc.material_index = mi
            except ValueError:
                pass

    def add_bm(self, obj, matname, src, flip=False):
        bm, mats = self.bm(obj)
        if matname not in mats:
            mats.append(matname)
        mi = mats.index(matname)
        mp = {}
        for v in src.verts:
            mp[v] = bm.verts.new(v.co)
        for f in src.faces:
            vs = [mp[v] for v in f.verts]
            if flip:
                vs = vs[::-1]
            try:
                fc = bm.faces.new(vs)
                fc.material_index = mi
            except ValueError:
                pass

    def decal(self, obj, matname, surf, pts, frame, off=0.005, cuts=3):
        v, f = project_poly(surf, pts, frame, off, cuts)
        self.add(obj, matname, v, f)

    def strip(self, obj, matname, surf, pts, width, frame, off=0.004, step=0.03):
        v, f = project_strip(surf, pts, width, frame, off, step)
        self.add(obj, matname, v, f)

    # ---- primitives (world space)
    def box(self, obj, matname, c, size, bevel=0.0, rot=None):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if bevel > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect='EDGES')
        if rot is not None:
            bmesh.ops.transform(bm, matrix=rot, verts=bm.verts[:])
        bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add_bm(obj, matname, bm)
        bm.free()

    def ellipsoid(self, obj, matname, c, radii, seg=12, rings=8, rot=None):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
        if rot is not None:
            bmesh.ops.transform(bm, matrix=rot, verts=bm.verts[:])
        bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add_bm(obj, matname, bm)
        bm.free()

    def sweep(self, obj, matname, path, section, out_dir, caps=True):
        """Sweep a closed 2D section (u = outward horizontal, v = up) along a path of points
        (x, y, z). Outward is whichever horizontal normal faces `out_dir`."""
        out_dir = Vector(out_dir).normalized()
        bm = bmesh.new()
        rings = []
        sign = None
        for i, p in enumerate(path):
            p = Vector(p)
            if i == 0:
                t = Vector(path[1]) - p
            elif i == len(path) - 1:
                t = p - Vector(path[-2])
            else:
                t = Vector(path[i + 1]) - Vector(path[i - 1])
            t.z = 0
            t.normalize()
            n = Vector((-t.y, t.x, 0))
            if sign is None:
                sign = 1 if n.dot(out_dir) >= 0 else -1
            n *= sign
            rings.append([bm.verts.new(p + n * u + Vector((0, 0, 1)) * v) for u, v in section])
        ns = len(section)
        for a, b in zip(rings[:-1], rings[1:]):
            for j in range(ns):
                try:
                    bm.faces.new((a[j], a[(j + 1) % ns], b[(j + 1) % ns], b[j]))
                except ValueError:
                    pass
        if caps:
            bm.faces.new(rings[0])
            bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        self.add_bm(obj, matname, bm)
        bm.free()

    # ---- finalize
    def build_objects(self, angle=35.0):
        out = {}
        for name, (bm, mats) in self.objs.items():
            bm.normal_update()
            lim = math.radians(angle)
            bm.edges.ensure_lookup_table()
            for e in bm.edges:
                if len(e.link_faces) == 2:
                    a, b = e.link_faces
                    e.smooth = a.normal.angle(b.normal, 0.0) < lim
                else:
                    e.smooth = True
            for f in bm.faces:
                f.smooth = True
            me = bpy.data.meshes.new(name)
            bm.to_mesh(me)
            for mn in mats:
                me.materials.append(self.mats[mn])
            ob = bpy.data.objects.new(name, me)
            bpy.context.scene.collection.objects.link(ob)
            out[name] = ob
        return out


# ----------------------------------------------------------------- wheels
def revolve_x(loop, seg, xmul=1.0):
    """Closed (x, r) loop revolved around the X axis -> (verts, faces) in local coords."""
    verts, faces = [], []
    rings = []
    for (x, r) in loop:
        if r < 1e-6:
            verts.append((x * xmul, 0.0, 0.0))
            rings.append([len(verts) - 1] * seg)
        else:
            idx = []
            for s in range(seg):
                a = 2 * math.pi * s / seg
                verts.append((x * xmul, r * math.cos(a), r * math.sin(a)))
                idx.append(len(verts) - 1)
            rings.append(idx)
    n = len(loop)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        for s in range(seg):
            s2 = (s + 1) % seg
            q = [a[s], a[s2], b[s2], b[s]]
            uniq = []
            for qi in q:
                if not uniq or uniq[-1] != qi:
                    uniq.append(qi)
            if len(uniq) > 1 and uniq[0] == uniq[-1]:
                uniq.pop()
            if len(set(uniq)) >= 3:
                faces.append(uniq)
    return verts, faces


def prism(poly, x0, x1):
    """Extrude 2D polygon (y,z) between x0 and x1 -> (verts, faces)."""
    n = len(poly)
    verts = [(x0, p[0], p[1]) for p in poly] + [(x1, p[0], p[1]) for p in poly]
    faces = [list(range(n)), list(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    return verts, faces


def tyre_loop(R, W, Rr):
    H = R - Rr
    half = [(0.44 * W, Rr + 0.02 * H), (0.50 * W, Rr + 0.18 * H), (0.505 * W, Rr + 0.55 * H),
            (0.47 * W, R - 0.14 * H), (0.38 * W, R - 0.03 * H), (0.22 * W, R)]
    return half + [(-x, r) for x, r in reversed(half)]


def build_wheel(car, name, side_sign, R, W, Rr, style, seg=32, spokes=5):
    """Wheel geometry in LOCAL coordinates (hub at origin), axis = X.
    side_sign=+1 -> outward is +X, -1 -> outward is -X."""
    xo = 0.5 * W - 0.012     # outer rim face position
    xi = -0.5 * W + 0.02
    mul = side_sign

    def put(matname, vf):
        v, f = vf
        if side_sign < 0:
            f = [fc[::-1] for fc in f]
        car.add(name, matname, v, f)

    put('Tyre', revolve_x(tyre_loop(R, W, Rr), seg, mul))
    if style == 'steel':
        loop = [(xo, Rr), (xo, Rr - 0.012), (xo - 0.022, Rr - 0.04), (xo - 0.022, 0.0), (xi, 0.0), (xi, Rr)]
        put('Rim', revolve_x(loop, seg, mul))
        cap = [(xo + 0.014, 0.0), (xo + 0.011, 0.035), (xo + 0.002, 0.066), (xo - 0.012, 0.078),
               (xo - 0.024, 0.078), (xo - 0.024, 0.0)]
        put('Chrome', revolve_x(cap, seg, mul))
        for i in range(8):
            a = 2 * math.pi * i / 8
            rr = 0.62 * Rr
            hole = [(xo - 0.021, 0.0), (xo - 0.021, 0.014), (xo - 0.016, 0.014), (xo - 0.016, 0.0)]
            vv, ff = revolve_x(hole, 10, mul)
            vv = [(p[0], p[1] + rr * math.cos(a), p[2] + rr * math.sin(a)) for p in vv]
            put('Trim', (vv, ff))
    elif style == 'steel_plastic':       # steel wheel with slotted plastic trim (Corsa)
        loop = [(xo + 0.002, Rr + 0.004), (xo + 0.002, Rr - 0.015), (xo - 0.02, Rr - 0.045),
                (xo - 0.02, 0.0), (xi, 0.0), (xi, Rr)]
        put('Rim', revolve_x(loop, seg, mul))
        cap = [(xo + 0.01, 0.0), (xo + 0.007, 0.03), (xo - 0.002, 0.052), (xo - 0.018, 0.058),
               (xo - 0.02, 0.0)]
        put('Chrome', revolve_x(cap, seg, mul))
        for i in range(10):
            a = 2 * math.pi * i / 10
            rr = 0.62 * Rr
            hole = [(xo - 0.018, 0.0), (xo - 0.018, 0.013), (xo, 0.013), (xo, 0.0)]
            vv, ff = revolve_x(hole, 8, mul)
            vv = [(p[0], p[1] + rr * math.cos(a), p[2] + rr * math.sin(a)) for p in vv]
            put('Trim', (vv, ff))
    elif style == 'alloy':
        barrel = [(xo, Rr + 0.003), (xo, Rr - 0.022), (xi, Rr - 0.022), (xi, Rr + 0.003)]
        put('Rim', revolve_x(barrel, seg, mul))
        xs0, xs1 = xo - 0.05, xo - 0.014
        rin = 0.045
        rout = Rr - 0.018
        for s in range(spokes):
            a = 2 * math.pi * s / spokes + math.pi / 2
            ux, uy = math.cos(a), math.sin(a)
            px, py = -uy, ux
            prof = [(rin, -0.020), (rout * 0.55, -0.022), (rout, -0.034), (rout, 0.034), (rout * 0.55, 0.022), (rin, 0.020)]
            poly = [(u * ux + w * px, u * uy + w * py) for u, w in prof]
            put('Rim', prism(poly, xs0 * mul, xs1 * mul))
        cap = [(xo - 0.008, 0.0), (xo - 0.008, 0.05), (xs0, 0.056), (xs0, 0.0)]
        put('Chrome', revolve_x(cap, 20, mul))
        back = [(xs0 - 0.04, 0.0), (xs0 - 0.04, Rr - 0.025), (xs0 - 0.022, Rr - 0.025), (xs0 - 0.022, 0.0)]
        put('Trim', revolve_x(back, seg, mul))
        disc = [(xs0 - 0.01, 0.075), (xs0 - 0.01, R * 0.52), (xs0 + 0.004, R * 0.52), (xs0 + 0.004, 0.075)]
        put('Chrome', revolve_x(disc, seg, mul))


# ----------------------------------------------------------------- export + verify
def export_glb(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_lights=False)


def tri_count(objs):
    n = 0
    for ob in objs.values():
        me = ob.data
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
    return n
