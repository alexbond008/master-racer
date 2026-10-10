"""Shared helpers for the procedural car scripts (gtr.py, f40.py, lambo.py).

Axes: Blender Z-up, car front faces -Y, +X = right side of the picture in front view.
Everything is plain bmesh; no external assets.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = os.path.expanduser('~/Projects/master-racer')
PREV = os.path.join(ROOT, 'blender', 'previews')
OUT = os.path.join(ROOT, 'public', 'models', 'cars')

# ---------------------------------------------------------------- materials
def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


def _mk(name, hexcol, rough, metal, emit=None, es=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    col = srgb(hexcol)
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*srgb(emit), 1)
        b.inputs['Emission Strength'].default_value = es
    m.diffuse_color = (*col, 1)
    return m


def make_materials(paint, rim='#bfc3cb', rim_rough=0.3, rim_metal=0.9):
    M = {}
    M['Paint'] = _mk('Paint', paint, 0.25, 0.5)
    M['Glass'] = _mk('Glass', '#06090e', 0.05, 0.3)
    M['Tyre'] = _mk('Tyre', '#141414', 0.85, 0.0)
    M['Rim'] = _mk('Rim', rim, rim_rough, rim_metal)
    M['Chrome'] = _mk('Chrome', '#d9dde3', 0.12, 1.0)
    M['Trim'] = _mk('Trim', '#0d0d0f', 0.55, 0.0)
    M['Interior'] = _mk('Interior', '#1b1b1d', 0.8, 0.0)
    M['HeadLight'] = _mk('HeadLight', '#fff1d0', 0.1, 0.0, '#fff1d0', 4.0)
    M['TailLight'] = _mk('TailLight', '#ff1a10', 0.2, 0.0, '#ff1208', 3.0)
    M['Plate'] = _mk('Plate', '#ece6c4', 0.5, 0.0)
    gc = _mk('GlassClear', '#0a1218', 0.05, 0.0)
    gc.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.3
    for attr, val in (('blend_method', 'BLEND'), ('surface_render_method', 'BLENDED')):
        try:
            setattr(gc, attr, val)
        except Exception as e:
            pass
    M['GlassClear'] = gc
    return M


MATGROUP = {'Glass': 'glass', 'GlassClear': 'glass', 'Trim': 'trim', 'Chrome': 'trim', 'Plate': 'trim',
            'HeadLight': 'lights', 'TailLight': 'lights', 'Interior': 'interior',
            'Tyre': 'trim', 'Rim': 'trim'}

# ---------------------------------------------------------------- mesh wrapper
class Mesh:
    def __init__(s, name, group=None):
        s.name = name
        s.group = group or name
        s.bm = bmesh.new()
        s.slots = []

    def mi(s, mat):
        if mat not in s.slots:
            s.slots.append(mat)
        return s.slots.index(mat)

    def vert(s, p):
        return s.bm.verts.new(Vector(p))

    def face(s, vs, mat='Paint', smooth=True):
        vs = list(vs)
        if len(set(vs)) < 3:
            return None
        try:
            f = s.bm.faces.new(vs)
        except ValueError:
            return None
        f.material_index = s.mi(mat)
        f.smooth = smooth
        return f

    def quad(s, a, b, c, d, mat='Paint'):
        return s.face([a, b, c, d], mat)

    def fix(s):
        bmesh.ops.recalc_face_normals(s.bm, faces=s.bm.faces[:])

    def tris(s):
        return sum(len(f.verts) - 2 for f in s.bm.faces)

    def to_obj(s, M, name=None):
        me = bpy.data.meshes.new(name or s.name)
        s.bm.to_mesh(me)
        for m in s.slots:
            me.materials.append(M[m])
        o = bpy.data.objects.new(name or s.name, me)
        bpy.context.scene.collection.objects.link(o)
        return o

    @staticmethod
    def from_obj(o, name, group):
        dg = bpy.context.evaluated_depsgraph_get()
        oe = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(oe)
        me.transform(o.matrix_world)
        m = Mesh(name, group)
        m.bm.from_mesh(me)
        m.slots = [x.name for x in me.materials]
        return m


# ---------------------------------------------------------------- interpolation
def pchip(xs, ys):
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for k in range(1, n - 1):
        if d[k - 1] * d[k] > 0:
            w1 = 2 * h[k] + h[k - 1]
            w2 = h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k])
    def end(h0, h1, d0, d1):
        v = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if v * d0 <= 0:
            return 0.0
        if d0 * d1 <= 0 and abs(v) > 3 * abs(d0):
            return 3 * d0
        return v
    if n > 2:
        m[0] = end(h[0], h[1], d[0], d[1])
        m[-1] = end(h[-1], h[-2], d[-1], d[-2])
    else:
        m[0] = m[1] = d[0]
    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        t = (x - xs[lo]) / h[lo]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[lo] + (t3 - 2 * t2 + t) * h[lo] * m[lo]
                + (-2 * t3 + 3 * t2) * ys[lo + 1] + (t3 - t2) * h[lo] * m[lo + 1])
    return f


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- body loft
LOFT_COLS = ('hw', 'zb', 'zc', 'zt', 'nu', 'nl', 'k', 'kb')


def make_profile_fn(stations):
    ys = [s[0] for s in stations]
    fns = [pchip(ys, [s[1 + i] for s in stations]) for i in range(len(LOFT_COLS))]
    def at(y):
        return dict(zip(LOFT_COLS, [f(y) for f in fns]))
    return at, ys[0], ys[-1]


def ring_pts(p, y, nseg, xoff=0.0):
    pts = []
    hw, zb, zc, zt, nu, nl, k, kb = (p[c] for c in LOFT_COLS)
    for j in range(nseg):
        t = 2 * math.pi * j / nseg
        c, s = math.cos(t), math.sin(t)
        n = nu if s >= 0 else nl
        e = 2.0 / n
        sx = math.copysign(abs(c) ** e, c)
        sz = math.copysign(abs(s) ** e, s)
        if s >= 0:
            z = zc + (zt - zc) * sz
            f = (z - zc) / max(zt - zc, 1e-6)
            x = hw * sx * (1 - (1 - k) * f)
        else:
            z = zc + (zc - zb) * sz
            g = ((zc - z) / max(zc - zb, 1e-6)) ** 2
            x = hw * sx * (1 - (1 - kb) * g)
        pts.append((x + xoff, y, z))
    return pts


def loft_body(name, stations, nseg, step, face_mat, group='body', extra_ys=()):
    """Loft rings along y. face_mat(cx,cy,cz,nx,ny,nz)->material name."""
    at, y0, y1 = make_profile_fn(stations)
    ys = set(s[0] for s in stations) | set(extra_ys)
    n = int(round((y1 - y0) / step))
    for i in range(n + 1):
        ys.add(y0 + (y1 - y0) * i / n)
    ys = sorted(ys)
    # drop near-duplicates
    out = [ys[0]]
    for y in ys[1:]:
        if y - out[-1] > 0.012:
            out.append(y)
    if out[-1] != y1:
        out[-1] = y1
    ys = out
    m = Mesh(name, group)
    rings = []
    for y in ys:
        p = at(y)
        rings.append([m.vert(q) for q in ring_pts(p, y, nseg)])
    faces = []
    for i in range(len(rings) - 1):
        for j in range(nseg):
            a, b = rings[i][j], rings[i][(j + 1) % nseg]
            c, d = rings[i + 1][(j + 1) % nseg], rings[i + 1][j]
            faces.append(m.face([a, b, c, d], 'Paint'))
    m.face(rings[0][::-1], 'Paint')
    m.face(rings[-1], 'Paint')
    m.fix()
    for f in m.bm.faces:
        if len(f.verts) == nseg:
            continue
        c = f.calc_center_median()
        nrm = f.normal
        f.material_index = m.mi(face_mat(c.x, c.y, c.z, nrm.x, nrm.y, nrm.z))
    return m, at


def mirror_x(p):
    return (-p[0], p[1], p[2])


# ---------------------------------------------------------------- primitives
def add_hex(m, pts, mat='Trim'):
    """pts: 8 points, bottom quad 0-3 then top quad 4-7 (same order)."""
    v = [m.vert(p) for p in pts]
    for idx in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        m.face([v[i] for i in idx], mat)


def add_box(m, c, size, mat='Trim', rot=None):
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    P = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    R = rot if rot is not None else Matrix.Identity(3)
    add_hex(m, [Vector(c) + R @ Vector(p) for p in P], mat)


def rotx(a):
    return Matrix.Rotation(a, 3, 'X')


def roty(a):
    return Matrix.Rotation(a, 3, 'Y')


def rotz(a):
    return Matrix.Rotation(a, 3, 'Z')


def add_cyl(m, p0, p1, r0, r1=None, seg=16, mat='Trim', cap=True):
    r1 = r0 if r1 is None else r1
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0).normalized()
    ref = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(ref).normalized()
    w = ax.cross(u)
    ra, rb = [], []
    for j in range(seg):
        a = 2 * math.pi * j / seg
        d = u * math.cos(a) + w * math.sin(a)
        ra.append(m.vert(p0 + d * r0))
        rb.append(m.vert(p1 + d * r1))
    for j in range(seg):
        k = (j + 1) % seg
        m.face([ra[j], ra[k], rb[k], rb[j]], mat)
    if cap:
        m.face(ra[::-1], mat)
        m.face(rb, mat)


def add_prism(m, poly, plane, a0, a1, mat='Paint'):
    """Extrude 2D polygon. plane 'YZ' -> extrude along x from a0 to a1; 'XZ' along y; 'XY' along z."""
    def P(q, a):
        if plane == 'YZ':
            return (a, q[0], q[1])
        if plane == 'XZ':
            return (q[0], a, q[1])
        return (q[0], q[1], a)
    A = [m.vert(P(q, a0)) for q in poly]
    B = [m.vert(P(q, a1)) for q in poly]
    n = len(poly)
    for i in range(n):
        k = (i + 1) % n
        m.face([A[i], A[k], B[k], B[i]], mat)
    m.face(A[::-1], mat)
    m.face(B, mat)


def add_loft_sections(m, sections, mat='Paint', cap=True):
    """sections: list of lists of 3D points (same count, same order). Closed rings."""
    rings = [[m.vert(p) for p in s] for s in sections]
    n = len(rings[0])
    for i in range(len(rings) - 1):
        for j in range(n):
            k = (j + 1) % n
            m.face([rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]], mat)
    if cap:
        m.face(rings[0][::-1], mat)
        m.face(rings[-1], mat)


def rect_section(c, hx, hz, plane_y=None):
    cx, cy, cz = c
    return [(cx - hx, cy, cz - hz), (cx + hx, cy, cz - hz), (cx + hx, cy, cz + hz), (cx - hx, cy, cz + hz)]


def shift(poly, dx=0.0, dy=0.0):
    return [(a + dx, b + dy) for a, b in poly]


# ---------------------------------------------------------------- conformal patches
class Surf:
    def __init__(s, mesh):
        s.tree = BVHTree.FromBMesh(mesh.bm)

    def hit(s, o, d):
        loc, nor, idx, dist = s.tree.ray_cast(Vector(o), Vector(d))
        if loc is None:
            return None
        return loc, nor


MODES = {
    'F': lambda a, b: ((a, -9.0, b), (0, 1, 0)),
    'R': lambda a, b: ((a, 9.0, b), (0, -1, 0)),
    'S': lambda a, b: ((9.0, a, b), (-1, 0, 0)),
    'L': lambda a, b: ((-9.0, a, b), (1, 0, 0)),
    'T': lambda a, b: ((a, b, 9.0), (0, 0, -1)),
}


def patch(m, surf, mode, grid, mat='Trim', lift=0.004, skirt=True, wrap=False, crown=0.0, sdepth=None):
    """grid: rows x cols of 2D points in projection plane; rays are cast onto surf."""
    wrap = wrap or getattr(grid, 'wrap', False)
    nr, nc = len(grid), len(grid[0])
    V = [[None] * nc for _ in range(nr)]
    NOR = {}
    d = None
    for i in range(nr):
        for j in range(nc):
            a, b = grid[i][j]
            o, d = MODES[mode](a, b)
            h = surf.hit(o, d)
            if h is None:
                continue
            loc, nor = h
            ed = min(i, nr - 1 - i, j if not wrap else 99, nc - 1 - j if not wrap else 99)
            lf = lift * (1 - crown * (1 - min(1.0, ed))) if crown else lift
            nn = nor.normalized()
            if nn.dot(Vector(d)) > 0:
                nn = -nn
            v = m.vert(loc + nn * lf)
            V[i][j] = v
            NOR[v] = nn
    dv = Vector(d)
    newv = [v for r in V for v in r if v]
    ncol = nc if wrap else nc - 1
    fl = []
    for i in range(nr - 1):
        for j in range(ncol):
            k = (j + 1) % nc
            q = [V[i][j], V[i][k], V[i + 1][k], V[i + 1][j]]
            if any(x is None for x in q):
                continue
            nrm = (q[1].co - q[0].co).cross(q[3].co - q[0].co)
            if nrm.dot(dv) > 0:
                q = q[::-1]
            f = m.face(q, mat)
            if f:
                fl.append(f)
    if not fl:
        return
    if skirt:
        sd = (lift + 0.012) if sdepth is None else sdepth
        cen = sum((v.co for v in newv), Vector()) / len(newv)
        edges = set()
        for f in fl:
            for e in f.edges:
                if len([x for x in e.link_faces if x in fl]) == 1:
                    edges.add(e)
        for e in edges:
            v1, v2 = e.verts
            if v1 not in NOR or v2 not in NOR:
                continue
            w1 = m.vert(v1.co - NOR[v1] * sd)
            w2 = m.vert(v2.co - NOR[v2] * sd)
            qn = (v2.co - v1.co).cross(w1.co - v1.co)
            mid = (v1.co + v2.co) / 2
            if qn.dot(mid - cen) > 0:
                m.face([v1, v2, w2, w1], mat)
            else:
                m.face([v2, v1, w1, w2], mat)
    if any(r[0] is not None and r[0] is not None for r in V):
        bmesh.ops.remove_doubles(m.bm, verts=[v for v in newv if v.is_valid], dist=1e-6)


class Grid(list):
    wrap = False


def sym(m, surf, mode, grid, mat='Trim', **kw):
    """Place a patch on both sides of the car (grid given for the +x side)."""
    if mode in ('S', 'L'):
        patch(m, surf, 'S', grid, mat, **kw)
        patch(m, surf, 'L', grid, mat, **kw)
    else:
        patch(m, surf, mode, grid, mat, **kw)
        g2 = Grid([[(-a, b) for a, b in r] for r in grid])
        g2.wrap = getattr(grid, 'wrap', False)
        patch(m, surf, mode, g2, mat, **kw)


def quad_grid(c, nu=6, nv=4, rnd=0.0):
    """c: 4 corners (-u-v, +u-v, +u+v, -u+v) as 2D points. rnd 0..1 squircle rounding."""
    g = Grid()
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            u = 2 * i / nu - 1
            v = 2 * j / nv - 1
            if rnd > 0:
                ln = math.hypot(u, v)
                if ln > 1e-9:
                    sc = lerp(1.0, max(abs(u), abs(v)) / ln, rnd)
                    u, v = u * sc, v * sc
            a = (1 - u) * (1 - v) / 4
            b = (1 + u) * (1 - v) / 4
            cc = (1 + u) * (1 + v) / 4
            dd = (1 - u) * (1 + v) / 4
            row.append((a * c[0][0] + b * c[1][0] + cc * c[2][0] + dd * c[3][0],
                        a * c[0][1] + b * c[1][1] + cc * c[2][1] + dd * c[3][1]))
        g.append(row)
    return g


def rect_c(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def ellipse_grid(cx, cz, a, b, nr=3, ns=20, r0=0.0, rot=0.0):
    g = Grid()
    g.wrap = True
    for i in range(nr + 1):
        rho = lerp(r0, 1.0, i / nr)
        row = []
        for j in range(ns):
            t = 2 * math.pi * j / ns
            x, z = a * rho * math.cos(t), b * rho * math.sin(t)
            if rot:
                x, z = x * math.cos(rot) - z * math.sin(rot), x * math.sin(rot) + z * math.cos(rot)
            row.append((cx + x, cz + z))
        g.append(row)
    return g


def resample(pts, step=0.02):
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(L / step)))
        for i in range(1, n + 1):
            t = i / n
            out.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t)))
    return out


def ribbon_grid(pts, width, step=0.02):
    pts = resample(pts, step)
    g = Grid()
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        g.append([(p[0] - nx * width / 2, p[1] - ny * width / 2), (p[0] + nx * width / 2, p[1] + ny * width / 2)])
    return g


def arc_pts(cx, cz, r, a0, a1, n=24):
    """angles in degrees from vertical (0 = straight up), increasing toward +first coord."""
    return [(cx + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.cos(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def arc_band(cy, cz, r0, r1, a0, a1, n=30):
    """Annular arc band grid (rows along arc, 2 cols radial) for flares."""
    g = Grid()
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        g.append([(cy + r0 * math.sin(a), cz + r0 * math.cos(a)), (cy + r1 * math.sin(a), cz + r1 * math.cos(a))])
    return g


# ---------------------------------------------------------------- wheels
def lathe(m, prof, nseg, mat, side=1, loop=False):
    """prof: (x, r) points; revolve about local X. loop closes the profile."""
    rings = []
    for x, r in prof:
        rings.append([m.vert((side * x, r * math.cos(2 * math.pi * j / nseg), r * math.sin(2 * math.pi * j / nseg)))
                      for j in range(nseg)])
    cnt = len(rings) if loop else len(rings) - 1
    for i in range(cnt):
        a, b = rings[i], rings[(i + 1) % len(rings)]
        for j in range(nseg):
            k = (j + 1) % nseg
            m.face([a[j], a[k], b[k], b[j]], mat)


def spoke(m, side, r0, r1, a0, a1, x0, x1, w0, w1, t0, t1, mat='Rim'):
    secs = []
    for r, a, x, w, t in ((r0, a0, x0, w0, t0), (r1, a1, x1, w1, t1)):
        c = Vector((side * x, r * math.cos(a), r * math.sin(a)))
        tv = Vector((0, -math.sin(a), math.cos(a)))
        xd = Vector((side, 0, 0))
        secs.append([c - tv * w / 2 - xd * t / 2, c + tv * w / 2 - xd * t / 2,
                     c + tv * w / 2 + xd * t / 2, c - tv * w / 2 + xd * t / 2])
    add_loft_sections(m, secs, mat)


def build_wheel(name, side, R, W, rim_r, style, nseg=28):
    """Local axes: X = axle (outward = side). Origin = hub centre."""
    m = Mesh(name, name)
    hw = W / 2
    sw = R - rim_r
    half = [(hw * 0.84, rim_r), (hw * 0.99, rim_r + sw * 0.18), (hw, rim_r + sw * 0.55),
            (hw * 0.93, R - sw * 0.12), (hw * 0.62, R - 0.002), (0, R)]
    prof = half + [(-x, r) for x, r in reversed(half[:-1])]
    prof = prof[::-1] if False else prof
    lathe(m, prof, nseg, 'Tyre', side, loop=True)
    # rim barrel
    b = rim_r
    th = 0.012
    lathe(m, [(hw * 0.95, b - th), (hw * 0.95, b + 0.004), (hw * 0.82, b), (-hw * 0.82, b), (-hw * 0.9, b - 0.002), (-hw * 0.9, b - th)],
          nseg, style.get('barrel_mat', 'Rim'), side, loop=True)
    if style.get('lip_mat'):
        lathe(m, [(hw * 0.97, b - 0.02), (hw * 0.97, b + 0.006), (hw * 0.80, b + 0.002), (hw * 0.80, b - 0.02)],
              nseg, style['lip_mat'], side, loop=True)
    # dark backing disc + brake disc
    lathe(m, [(-0.02, 0.0), (-0.02, b - th), (0.0, b - th), (0.0, 0.0)], nseg, 'Trim', side, loop=True)
    bd = style.get('disc', (0.12, 0.19))
    lathe(m, [(0.012, bd[0]), (0.012, bd[1]), (0.034, bd[1]), (0.034, bd[0])], nseg, 'Chrome', side, loop=True)
    # spokes
    xf = style['x_face']
    for (r0, r1, a0, a1, w0, w1, t0, t1, xa, xb) in style['spokes'](b - th * 0.5, xf):
        spoke(m, side, r0, r1, a0, a1, xa, xb, w0, w1, t0, t1, style.get('spoke_mat', 'Rim'))
    # hub
    hr = style.get('hub_r', 0.05)
    lathe(m, [(0.0, 0.0), (0.0, hr), (xf + 0.015, hr), (xf + 0.015, hr * 0.6), (xf + 0.026, hr * 0.5), (xf + 0.026, 0.0)],
          nseg, style.get('hub_mat', 'Chrome'), side)
    if 'extra' in style:
        style['extra'](m, side, xf)
    bmesh.ops.remove_doubles(m.bm, verts=m.bm.verts[:], dist=1e-6)
    m.fix()
    return m


# ---------------------------------------------------------------- finalize / export / verify
def finalize(parts, smooth_deg=38):
    dests = {}
    maps = {}
    for p in parts:
        for f in p.bm.faces:
            mat = p.slots[f.material_index]
            dn = p.group if mat == 'Paint' else MATGROUP.get(mat, p.group)
            d = dests.setdefault(dn, Mesh(dn))
            mp = maps.setdefault((dn, id(p)), {})
            vs = []
            for v in f.verts:
                if v not in mp:
                    mp[v] = d.vert(v.co)
                vs.append(mp[v])
            d.face(vs, mat, f.smooth)
    for d in dests.values():
        smooth_edges(d, smooth_deg)
    return dests


def smooth_edges(m, deg=38):
    lim = math.radians(deg)
    for e in m.bm.edges:
        if len(e.link_faces) == 2:
            try:
                ang = e.calc_face_angle()
            except ValueError:
                ang = 0
            e.smooth = ang < lim
        else:
            e.smooth = True
    for f in m.bm.faces:
        f.smooth = True


def export_car(car_id, objs):
    os.makedirs(OUT, exist_ok=True)
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    path = os.path.join(OUT, car_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_lights=False,
                              use_selection=True)
    return path


def verify_and_render(car_id, glb, focus=None, cam_dist=1.0):
    """Re-import the GLB into an empty scene, print bbox/tri stats, render previews."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    tris = 0
    names = []
    body_mx = None
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        names.append(o.name)
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
    size = mx - mn
    print('OBJECTS', sorted(names))
    print('BBOX min', tuple(round(x, 3) for x in mn), 'max', tuple(round(x, 3) for x in mx))
    print('SIZE L(y)=%.3f W(x)=%.3f H(z)=%.3f  tris=%d' % (size.y, size.x, size.z, tris))
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and o.name.startswith('wheel'):
            print(o.name, 'origin', tuple(round(x, 3) for x in o.matrix_world.translation))
    for mt in bpy.data.materials:
        print('MAT', mt.name, getattr(mt, 'blend_method', None), getattr(mt, 'surface_render_method', None))
    sc = bpy.context.scene
    # lights & ground
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.42, 0.5, 0.62, 1)
    bg.inputs[1].default_value = 0.7
    for nm, loc, e, col in (('sun', (4, -6, 8), 5.5, (1, 0.95, 0.88)), ('fill', (-6, 5, 3), 1.2, (0.7, 0.8, 1))):
        ld = bpy.data.lights.new(nm, 'SUN')
        ld.energy = e
        ld.color = col
        lo = bpy.data.objects.new(nm, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.001))
    gp = bpy.context.object
    gm = bpy.data.materials.new('g')
    gm.diffuse_color = (0.35, 0.36, 0.38, 1)
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.2, 0.21, 0.23, 1)
    gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    gp.data.materials.append(gm)
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = 1000
    sc.render.resolution_y = 600
    sc.render.film_transparent = False
    try:
        sc.eevee.taa_render_samples = 24
    except Exception:
        pass
    c = (mn + mx) / 2
    c.z = size.z * 0.42
    if focus:
        c = Vector(focus)
    D = max(size.x, size.y) * cam_dist
    views = {
        'front34': (-0.95 * D, -1.25 * D, 0.38 * D, 0.0),
        'rear34': (1.0 * D, 1.25 * D, 0.42 * D, 0.0),
        'side': (2.2 * D, 0.0001 * D, 0.1 * D, 0.0),
        'top': (0.15 * D, -0.3 * D, 2.1 * D, 0.0),
        'front': (0.0001, -2.3 * D, 0.2 * D, 0.0),
        'rear': (0.0001, 2.3 * D, 0.25 * D, 0.0),
        'low34': (1.3 * D, -0.9 * D, -0.05 * D, 0.0),
    }
    cust = os.environ.get('CAMS')
    if cust:
        for spec in cust.split(';'):
            nm, vals = spec.split(':')
            v = [float(t) for t in vals.split(',')]
            views[nm] = ('custom', v)
    only = os.environ.get('VIEWS')
    for nm, vv in views.items():
        if only and nm not in only.split(','):
            continue
        cd = bpy.data.cameras.new('c')
        cd.lens = 55 if nm not in ('top',) else 45
        co = bpy.data.objects.new('cam', cd)
        sc.collection.objects.link(co)
        if vv[0] == 'custom':
            v = vv[1]
            co.location = (v[0], v[1], v[2])
            tgt = Vector((v[3], v[4], v[5]))
            if len(v) > 6:
                cd.lens = v[6]
        else:
            x, y, z, _ = vv
            co.location = (c.x + x, c.y + y, c.z + z)
            tgt = c
        co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = co
        sc.render.filepath = os.path.join(PREV, '%s_%s.png' % (car_id, nm))
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(co)
    return size
