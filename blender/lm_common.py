"""Shared helpers for procedural landmark models (Blender 5.x, headless).

Usage in a model script:
    import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from lm_common import *
    B = Builder()
    B.box(...); ...
    finish(B, 'academy', footprint=[w, d], notes='...', cams=[...])
Everything is one object per material; names are Mat names.
"""
import bpy, bmesh, math, os, json, sys
from mathutils import Vector, Matrix

ROOT = os.path.expanduser('~/Projects/master-racer')
OUT_DIR = os.path.join(ROOT, 'public/models/landmarks')
PREV_DIR = os.path.join(ROOT, 'blender/previews')

_MATS = {}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()


def mat(name, color, rough=0.7, metal=0.0, emit=None, strength=4.0, alpha=None):
    """Principled BSDF with plain colour. emit=(r,g,b) -> emissive."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    c = tuple(color) + (1.0,) if len(color) == 3 else tuple(color)
    bsdf.inputs['Base Color'].default_value = c
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    if emit is not None:
        bsdf.inputs['Emission Color'].default_value = tuple(emit) + (1.0,)
        bsdf.inputs['Emission Strength'].default_value = strength
    if alpha is not None:
        bsdf.inputs['Alpha'].default_value = alpha
        m.surface_render_method = 'BLENDED'
    _MATS[name] = m
    return m


def hexc(h):
    h = h.lstrip('#')
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    # sRGB -> linear
    f = lambda c: (c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


class Builder:
    """Collects triangles/quads per material; supports a 2D rotate+translate transform stack."""

    def __init__(self):
        self.geo = {}  # matname -> (verts, faces, smooth flags)
        self.mats = {}
        self._xf = [(0.0, 0.0, 0.0, 1.0)]  # (rot_z, tx, ty, tz) -- applied as rotate then translate

    # ---- transform ----
    def push(self, rot=0.0, tx=0.0, ty=0.0, tz=0.0):
        self._xf.append((rot, tx, ty, tz))

    def pop(self):
        self._xf.pop()

    def _t(self, p):
        x, y, z = p
        for rot, tx, ty, tz in reversed(self._xf[1:]):
            c, s = math.cos(rot), math.sin(rot)
            x, y = x * c - y * s + tx, x * s + y * c + ty
            z = z + tz
        return (x, y, z)

    # ---- low level ----
    def _g(self, m):
        if isinstance(m, str):
            raise ValueError('pass a material object')
        n = m.name
        if n not in self.geo:
            self.geo[n] = ([], [], [])
            self.mats[n] = m
        return self.geo[n]

    def face(self, pts, m, smooth=False):
        v, f, s = self._g(m)
        base = len(v)
        for p in pts:
            v.append(self._t(p))
        f.append(tuple(range(base, base + len(pts))))
        s.append(smooth)

    def quad(self, a, b, c, d, m, smooth=False):
        self.face([a, b, c, d], m, smooth)

    # ---- primitives (all in local frame; z0 base) ----
    def box(self, cx, cy, z0, sx, sy, sz, m, rot=0.0, bottom=False):
        """Axis box centred at cx,cy; sizes sx (X), sy (Y), sz (Z up from z0). rot about its own centre."""
        c, s = math.cos(rot), math.sin(rot)
        hx, hy = sx / 2, sy / 2
        corners = []
        for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
            corners.append((cx + dx * c - dy * s, cy + dx * s + dy * c))
        self.prism(corners, z0, z0 + sz, m, bottom=bottom)

    def prism(self, poly, z0, z1, m, bottom=False, top=True, smooth=False):
        """Extrude CCW (or CW; auto-fixed) polygon between z0 and z1. Sides + optional top/bottom caps."""
        poly = list(poly)
        if _area(poly) < 0:
            poly.reverse()
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            self.face([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], m, smooth)
        if top:
            self._cap(poly, z1, m, up=True)
        if bottom:
            self._cap(poly, z0, m, up=False)

    def _cap(self, poly, z, m, up=True):
        pts = [(p[0], p[1], z) for p in poly]
        tris = _triangulate(poly)
        for a, b, c in tris:
            if up:
                self.face([pts[a], pts[b], pts[c]], m)
            else:
                self.face([pts[a], pts[c], pts[b]], m)

    def frustum(self, cx, cy, z0, z1, r0, r1, m, segs=24, cap_top=True, cap_bottom=False, smooth=True,
                rot=0.0, sx=1.0, sy=1.0):
        """Cylinder / cone / tapering tower. r0 at z0, r1 at z1. sx/sy squash for ellipses."""
        for i in range(segs):
            a0 = rot + 2 * math.pi * i / segs
            a1 = rot + 2 * math.pi * (i + 1) / segs
            p = lambda a, r, z: (cx + math.cos(a) * r * sx, cy + math.sin(a) * r * sy, z)
            if r1 > 1e-6:
                self.face([p(a0, r0, z0), p(a1, r0, z0), p(a1, r1, z1), p(a0, r1, z1)], m, smooth)
            else:
                self.face([p(a0, r0, z0), p(a1, r0, z0), (cx, cy, z1)], m, smooth)
        if cap_top and r1 > 1e-6:
            self.face([(cx + math.cos(rot + 2 * math.pi * i / segs) * r1 * sx,
                        cy + math.sin(rot + 2 * math.pi * i / segs) * r1 * sy, z1) for i in range(segs)], m)
        if cap_bottom:
            self.face([(cx + math.cos(rot - 2 * math.pi * i / segs) * r0 * sx,
                        cy + math.sin(rot - 2 * math.pi * i / segs) * r0 * sy, z0) for i in range(segs)], m)

    def dome(self, cx, cy, z0, r, m, segs=24, rings=8, hz=None, a_from=0.0, a_to=2 * math.pi, sx=1, sy=1):
        """Hemisphere (hz = height scale: z-radius). Optional angular wedge for half domes."""
        hz = r if hz is None else hz
        n = segs
        for j in range(rings):
            t0 = (math.pi / 2) * j / rings
            t1 = (math.pi / 2) * (j + 1) / rings
            for i in range(n):
                a0 = a_from + (a_to - a_from) * i / n
                a1 = a_from + (a_to - a_from) * (i + 1) / n
                P = lambda a, t: (cx + math.cos(a) * math.cos(t) * r * sx, cy + math.sin(a) * math.cos(t) * r * sy,
                                  z0 + math.sin(t) * hz)
                if j == rings - 1:
                    self.face([P(a0, t0), P(a1, t0), P(a1, t1)], m, True)
                else:
                    self.face([P(a0, t0), P(a1, t0), P(a1, t1), P(a0, t1)], m, True)

    def sphere(self, cx, cy, cz, r, m, segs=12, rings=8):
        for j in range(rings):
            t0 = -math.pi / 2 + math.pi * j / rings
            t1 = -math.pi / 2 + math.pi * (j + 1) / rings
            for i in range(segs):
                a0 = 2 * math.pi * i / segs
                a1 = 2 * math.pi * (i + 1) / segs
                P = lambda a, t: (cx + math.cos(a) * math.cos(t) * r, cy + math.sin(a) * math.cos(t) * r,
                                  cz + math.sin(t) * r)
                if j == 0:
                    self.face([P(a0, t0), P(a1, t1), P(a0, t1)], m, True) if False else self.face(
                        [P(a0, t0), P(a1, t1), P(a0, t1)], m, True)
                elif j == rings - 1:
                    self.face([P(a0, t0), P(a1, t0), P(a0, t1)], m, True)
                else:
                    self.face([P(a0, t0), P(a1, t0), P(a1, t1), P(a0, t1)], m, True)

    def arch_prism(self, x0, x1, y, z0, spring_z, depth, m, segs=10, flat_front=True):
        """Solid arch-shaped (round-headed) slab: width x0..x1, front face at y, thickness depth (+y). Used for
        glow panels / door shutters. Rect lower part to spring_z then semicircle."""
        w = x1 - x0
        r = w / 2
        cx = (x0 + x1) / 2
        pts = [(x0, z0), (x1, z0), (x1, spring_z)]
        for i in range(1, segs):
            a = math.pi * i / segs
            pts.append((cx + math.cos(a) * r, spring_z + math.sin(a) * r))
        pts.append((x0, spring_z))
        self.vprism(pts, y, depth, m)

    def vprism(self, pts_xz, y, depth, m, smooth=False):
        """Extrude a polygon given in (x,z) in the XZ plane, from y to y+depth (front face towards -Y)."""
        pts = list(pts_xz)
        if _area(pts) < 0:
            pts.reverse()
        n = len(pts)
        # front (-Y facing): triangulate
        tris = _triangulate(pts)
        for a, b, c in tris:
            # xz ccw viewed from -y? polygon ccw in (x,z) seen from front (-Y looking +Y) -> normal -Y when
            # winding (x,z) ccw viewed from -y side ... verified: x right, z up, viewer at -y => ccw is CCW
            self.face([(pts[a][0], y, pts[a][1]), (pts[b][0], y, pts[b][1]), (pts[c][0], y, pts[c][1])], m)
        if depth > 0:
            for a, b, c in tris:
                self.face([(pts[a][0], y + depth, pts[a][1]), (pts[c][0], y + depth, pts[c][1]),
                           (pts[b][0], y + depth, pts[b][1])], m)
            for i in range(n):
                a, b = pts[i], pts[(i + 1) % n]
                # side faces: outward normal for ccw (x,z) polygon seen from -y.
                self.face([(a[0], y + depth, a[1]), (b[0], y + depth, b[1]), (b[0], y, b[1]), (a[0], y, a[1])], m,
                          smooth)


    def obox(self, c, ex, ey, ez, sx, sy, sz, m, smooth=False):
        """Oriented box: centre c, unit axes ex,ey,ez (tuples), full sizes sx,sy,sz."""
        def P(a, b, d):
            return (c[0] + ex[0] * a * sx / 2 + ey[0] * b * sy / 2 + ez[0] * d * sz / 2,
                    c[1] + ex[1] * a * sx / 2 + ey[1] * b * sy / 2 + ez[1] * d * sz / 2,
                    c[2] + ex[2] * a * sx / 2 + ey[2] * b * sy / 2 + ez[2] * d * sz / 2)
        q = lambda *idx: self.face([P(*i) for i in idx], m, smooth)
        q((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1))
        q((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))
        q((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1))
        q((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1))
        q((1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1))
        q((-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1))

    def loft(self, rings, m, smooth=True, closed=False, cap_start=True, cap_end=True):
        """rings: list of rings, each a list of 3D points (same length). Connect consecutive rings.
        closed=True treats each ring as a closed loop. Winding: ring order must be CCW seen from outside
        looking along loft direction... caller checks visually; double-sided fix via flip flag not provided."""
        n = len(rings[0])
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            rng = range(n) if closed else range(n - 1)
            for i in rng:
                j = (i + 1) % n
                self.face([a[i], a[j], b[j], b[i]], m, smooth)
        if closed and cap_start:
            self.face(list(reversed(rings[0])), m)
        if closed and cap_end:
            self.face(list(rings[-1]), m)

    def line_ring(self, pts, m, w, z0, z1):
        """Thin vertical wall along a polyline (list of (x,y)), thickness w. For railings/parapets."""
        for a, b in zip(pts[:-1], pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 1e-6:
                continue
            ang = math.atan2(dy, dx)
            self.box((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z0, L, w, z1 - z0, m, rot=ang)

    def text(self, s, x, y, z, size, m, rot_z=0.0, extrude=0.05, align='CENTER', facing='-Y', font=None, bold=False):
        """Text as mesh. facing '-Y': readable from the front (-Y looking +Y). Position = centre/baseline-centre."""
        crv = bpy.data.curves.new('t', 'FONT')
        crv.body = s
        crv.size = size
        crv.extrude = extrude / 2
        crv.align_x = align
        crv.align_y = 'CENTER'
        crv.resolution_u = 2
        if font:
            crv.font = font
        obj = bpy.data.objects.new('t', crv)
        bpy.context.scene.collection.objects.link(obj)
        dg = bpy.context.evaluated_depsgraph_get()
        eo = obj.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(eo)
        # text lies in XY plane facing +Z. Stand it up facing -Y: rotate +90 about X => text normal +Z -> -Y.
        R = Matrix.Rotation(math.radians(90), 4, 'X')
        if facing == '+Y':
            R = Matrix.Rotation(math.radians(180), 4, 'Z') @ R
        v, f, sm = self._g(m)
        base = len(v)
        for vert in me.vertices:
            p = R @ vert.co
            p = Vector((p.x, p.y, p.z))
            c, s_ = math.cos(rot_z), math.sin(rot_z)
            px, py = p.x * c - p.y * s_, p.x * s_ + p.y * c
            v.append(self._t((px + x, py + y, p.z + z)))
        for poly in me.polygons:
            f.append(tuple(base + i for i in poly.vertices))
            sm.append(False)
        bpy.data.objects.remove(obj)
        bpy.data.curves.remove(crv)
        bpy.data.meshes.remove(me)

    # ---- output ----
    def build(self, bevel=None, skip_bevel=()):
        objs = []
        for name, (v, f, s) in self.geo.items():
            me = bpy.data.meshes.new(name)
            me.from_pydata(v, [], f)
            me.update()
            for p, sm in zip(me.polygons, s):
                p.use_smooth = sm
            o = bpy.data.objects.new(name, me)
            bpy.context.scene.collection.objects.link(o)
            me.materials.append(self.mats[name])
            if bevel and name not in skip_bevel:
                mod = o.modifiers.new('bev', 'BEVEL')
                mod.width = bevel
                mod.segments = 1
                mod.limit_method = 'ANGLE'
                mod.angle_limit = math.radians(40)
            objs.append(o)
        return objs


def _area(poly):
    a = 0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i][:2]
        x1, y1 = poly[(i + 1) % n][:2]
        a += x0 * y1 - x1 * y0
    return a / 2


def _triangulate(poly):
    """Ear clipping for simple polygons (CCW). Returns index triples."""
    n = len(poly)
    idx = list(range(n))
    if _area(poly) < 0:
        idx.reverse()
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        ear = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = poly[j]
                if _in_tri(p, a, b, c):
                    ok = False
                    break
            if ok:
                tris.append((i0, i1, i2))
                idx.pop(k)
                ear = True
                break
        if not ear:
            # degenerate; fan the rest
            break
    if len(idx) >= 3:
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return tris


def _in_tri(p, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg = (d1 < -1e-9) or (d2 < -1e-9) or (d3 < -1e-9)
    pos = (d1 > 1e-9) or (d2 > 1e-9) or (d3 > 1e-9)
    return not (neg and pos)


# ---------------------------------------------------------------- previews / export
def tri_count():
    n = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            eo = o.evaluated_get(dg)
            me = eo.to_mesh()
            n += sum(max(1, len(p.vertices) - 2) for p in me.polygons)
            eo.to_mesh_clear()
    return n


def bbox_world():
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            eo = o.evaluated_get(dg)
            for c in eo.bound_box:
                w = o.matrix_world @ Vector(c)
                mn = Vector((min(mn.x, w.x), min(mn.y, w.y), min(mn.z, w.z)))
                mx = Vector((max(mx.x, w.x), max(mx.y, w.y), max(mx.z, w.z)))
    return mn, mx


def setup_render(res=(1000, 700)):
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    try:
        sc.eevee.taa_render_samples = 24
    except Exception:
        pass
    try:
        sc.view_settings.view_transform = 'Standard'
    except Exception:
        pass
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.05, 0.07, 0.14, 1)
    bg.inputs['Strength'].default_value = 1.0
    sc.world = w


def add_ground(size=400):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, -0.02))
    g = bpy.context.active_object
    g.name = 'PreviewGround'
    m = bpy.data.materials.new('PG')
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.03, 0.03, 0.035, 1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    g.data.materials.append(m)
    return g


def add_lights():
    ld = bpy.data.lights.new('sun', 'SUN')
    ld.energy = 3.0
    ld.color = (1.0, 0.82, 0.65)
    so = bpy.data.objects.new('sun', ld)
    so.rotation_euler = (math.radians(55), math.radians(0), math.radians(-35))
    bpy.context.scene.collection.objects.link(so)
    ld2 = bpy.data.lights.new('fill', 'SUN')
    ld2.energy = 1.0
    ld2.color = (0.55, 0.65, 1.0)
    fo = bpy.data.objects.new('fill', ld2)
    fo.rotation_euler = (math.radians(60), 0, math.radians(150))
    bpy.context.scene.collection.objects.link(fo)


def render_cams(name, cams, res=(1000, 700)):
    """cams: list of (label, location, target, lens)"""
    os.makedirs(PREV_DIR, exist_ok=True)
    setup_render(res)
    g = add_ground(600)
    add_lights()
    sc = bpy.context.scene
    for label, loc, tgt, lens in cams:
        cd = bpy.data.cameras.new('c')
        cd.lens = lens
        cd.clip_end = 2000
        co = bpy.data.objects.new('cam', cd)
        sc.collection.objects.link(co)
        co.location = loc
        d = Vector(tgt) - Vector(loc)
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        sc.camera = co
        sc.render.filepath = os.path.join(PREV_DIR, f'{name}_{label}.png')
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(co)
    bpy.data.objects.remove(g)


def export(name, footprint, notes, extra=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    # hide preview-only objects
    for o in list(bpy.context.scene.objects):
        if o.name.startswith('PreviewGround'):
            bpy.data.objects.remove(o)
    path = os.path.join(OUT_DIR, f'{name}.glb')
    sel = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in sel:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_lights=False,
                              use_selection=True)
    mn, mx = bbox_world()
    info = {'footprint': [round(footprint[0], 2), round(footprint[1], 2)], 'height': round(mx.z, 2), 'notes': notes,
            'bbox_x': [round(mn.x, 2), round(mx.x, 2)], 'bbox_y': [round(mn.y, 2), round(mx.y, 2)],
            'triangles': tri_count()}
    if extra:
        info.update(extra)
    json.dump(info, open(os.path.join(OUT_DIR, f'{name}.json'), 'w'), indent=1)
    print('EXPORT', name, info)
    return path


def finish(B, name, footprint, notes, cams, bevel=0.03, skip_bevel=(), res=(1000, 700), do_preview=True):
    B.build(bevel=bevel, skip_bevel=skip_bevel)
    export(name, footprint, notes)
    if do_preview and '--nopreview' not in sys.argv:
        render_cams(name, cams, res)


def reimport_check(name):
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT_DIR, f'{name}.glb'))
    mn, mx = bbox_world()
    print('REIMPORT', name, 'bbox', tuple(round(v, 2) for v in mn), tuple(round(v, 2) for v in mx))
