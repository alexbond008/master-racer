"""Shared helpers for the master-racer Blender model scripts (bmesh based, procedural only).

Conventions: Z up, front faces -Y, +X is the vehicle's LEFT (kerb) side, origin on ground mid-wheelbase.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

# ----------------------------------------------------------------------------- scene / materials
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()


MATS = {}
PRESETS = {
    # name: (base rgba, roughness, metallic, emission rgb, emission strength)
    'Paint': ((0.02, 0.02, 0.02, 1), 0.25, 0.5, None, 0),
    'Glass': ((0.015, 0.02, 0.028, 1), 0.05, 0.3, None, 0),
    'Tyre': ((0.015, 0.015, 0.015, 1), 0.92, 0.0, None, 0),
    'Rim': ((0.72, 0.73, 0.75, 1), 0.3, 0.9, None, 0),
    'Chrome': ((0.85, 0.85, 0.88, 1), 0.08, 1.0, None, 0),
    'Trim': ((0.025, 0.025, 0.027, 1), 0.6, 0.0, None, 0),
    'Interior': ((0.14, 0.13, 0.12, 1), 0.8, 0.0, None, 0),
    'HeadLight': ((1, 0.95, 0.8, 1), 0.1, 0.0, (1, 0.93, 0.75), 4.0),
    'TailLight': ((0.9, 0.02, 0.02, 1), 0.2, 0.0, (1, 0.03, 0.02), 4.0),
    'Plate': ((0.95, 0.75, 0.08, 1), 0.4, 0.0, None, 0),
    'Emit_Window': ((1, 0.85, 0.55, 1), 0.3, 0.0, (1, 0.82, 0.5), 3.0),
    'Emit_Sign': ((1, 0.55, 0.05, 1), 0.3, 0.0, (1, 0.5, 0.04), 4.5),
    'Emit_Route': ((1, 0.95, 0.7, 1), 0.3, 0.0, (1, 0.93, 0.62), 4.0),
}


def mat(name, color=None):
    if name in MATS:
        return MATS[name]
    base, rough, metal, em, es = PRESETS[name]
    if color is not None:
        base = color
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = base
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if em:
        b.inputs['Emission Color'].default_value = (*em, 1)
        b.inputs['Emission Strength'].default_value = es
    MATS[name] = m
    return m


# ----------------------------------------------------------------------------- part accumulator
class Part:
    """Accumulates geometry (with per-face material) into one mesh/object."""

    def __init__(self, name, mats):
        self.name = name
        self.mats = mats  # list of material names
        self.bm = bmesh.new()

    def mi(self, m):
        return self.mats.index(m)

    def merge(self, src, m):
        """merge a temp bmesh into this part with material name m"""
        idx = self.mi(m)
        vm = {}
        for v in src.verts:
            vm[v] = self.bm.verts.new(v.co)
        for f in src.faces:
            nf = self.bm.faces.new([vm[v] for v in f.verts])
            nf.material_index = idx
            nf.smooth = f.smooth

    def poly(self, pts, m, smooth=False):
        idx = self.mi(m)
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = idx
        f.smooth = smooth
        return f

    def to_object(self, smooth_angle=None, origin=None):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(mat(m))
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        if smooth_angle is not None:
            smooth(ob, smooth_angle)
        return ob


def smooth(ob, angle_deg=35):
    bpy.context.view_layer.update()
    for v in list(bpy.context.view_layer.objects):
        if v is not None:
            v.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))


# ----------------------------------------------------------------------------- primitives
def _xform(bm, loc, rot=None, scale=None):
    m = Matrix.Translation(loc)
    if rot is not None:
        m = m @ rot.to_4x4()
    if scale is not None:
        m = m @ Matrix.Diagonal((*scale, 1))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)


def box(part, c, size, m, bevel=0.0, segs=1, rot=None):
    b = bmesh.new()
    bmesh.ops.create_cube(b, size=1.0)
    bmesh.ops.scale(b, vec=Vector(size), verts=b.verts)
    if bevel > 0:
        bmesh.ops.bevel(b, geom=list(b.edges), offset=bevel, segments=segs, affect='EDGES')
    _xform(b, c, rot)
    for f in b.faces:
        f.smooth = bevel > 0
    part.merge(b, m)
    b.free()


def cyl(part, c, axis, r, length, m, seg=20, r2=None, cap=True):
    """cylinder/cone with axis 'x','y' or 'z' (radius r at -length/2 end, r2 at +end)."""
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=cap, cap_tris=False, segments=seg, radius1=r, radius2=r if r2 is None else r2,
                          depth=length)
    rot = {'z': Matrix.Identity(3), 'x': Matrix.Rotation(math.pi / 2, 3, 'Y'),
           'y': Matrix.Rotation(-math.pi / 2, 3, 'X')}[axis]
    _xform(b, c, rot)
    part.merge(b, m)
    b.free()


def revolve(part, c, profile, m, seg=24, closed=False, smooth_faces=True, caps=True):
    """Revolve profile [(radius, axial_x)] about the X axis through c."""
    b = bmesh.new()
    rings = []
    for (r, ax) in profile:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(b.verts.new((ax, r * math.cos(a), r * math.sin(a))))
        rings.append(ring)
    n = len(rings)
    last = n if closed else n - 1
    for k in range(last):
        r0, r1 = rings[k], rings[(k + 1) % n]
        for i in range(seg):
            f = b.faces.new([r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]])
            f.smooth = smooth_faces
    if not closed and caps:
        for ring, pr in ((rings[0], profile[0]), (rings[-1], profile[-1])):
            if pr[0] > 1e-6:
                b.faces.new(ring)
    _xform(b, c)
    part.merge(b, m)
    b.free()


def text_mesh(part, text, c, size, m, depth=0.01, rot=None, align='CENTER'):
    cu = bpy.data.curves.new('txt', 'FONT')
    cu.body = text
    cu.size = size
    cu.extrude = depth / 2
    cu.align_x = align
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new('txt', cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    for v in list(bpy.context.view_layer.objects):
        if v is not None:
            v.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    me = ob.data
    b = bmesh.new()
    b.from_mesh(me)
    bmesh.ops.triangulate(b, faces=b.faces[:])
    _xform(b, c, rot)
    part.merge(b, m)
    b.free()
    bpy.data.objects.remove(ob)


# ----------------------------------------------------------------------------- lofted bodies
def ease_inset(d, R):
    """inset of a rounded end: d = distance from the extreme end (0..R); returns inward offset."""
    if d >= R:
        return 0.0
    return R - math.sqrt(max(R * R - (R - d) ** 2, 0.0))


class Loft:
    """Lofts a mirrored half-profile along Y.
    stations: list of dict(y=.., ...) passed to prof_fn(st)-> right-half pts [(x,z)] bottom-centre -> top-centre
    (first and last x must be 0). deform(x,y,z)->(x,y,z) optional.
    """

    def __init__(self, stations, prof_fn, deform=None):
        self.st = stations
        self.n = None
        self.rings = []
        self.deform = deform or (lambda x, y, z: (x, y, z))
        for st in stations:
            pts = prof_fn(st)
            if self.n is None:
                self.n = len(pts)
            assert len(pts) == self.n, (len(pts), self.n)
            right = pts
            left = [(-x, z) for (x, z) in reversed(pts[1:-1])]
            self.rings.append([(x, st['y'], z) for (x, z) in right + left])
        self.N = 2 * self.n - 2
        self.bm = bmesh.new()
        self.vg = []
        for ring in self.rings:
            self.vg.append([self.bm.verts.new(self.deform(*p)) for p in ring])
        self.fmap = {}
        for i in range(len(self.st) - 1):
            for k in range(self.N):
                f = self.bm.faces.new([self.vg[i][k], self.vg[i][(k + 1) % self.N],
                                       self.vg[i + 1][(k + 1) % self.N], self.vg[i + 1][k]])
                f.smooth = True
                self.fmap[(i, k)] = f
        for ring in (self.vg[0], self.vg[-1]):
            f = self.bm.faces.new(ring)
            f.smooth = True
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])

    def kr(self, j):
        """ring index of right-side point j"""
        return j

    def kl(self, j):
        """ring index of left-side mirror of point j (1..n-2)"""
        return self.N - j

    def patch(self, i0, i1, j0, j1, side):
        """faces between stations i0..i1 (station indices) and ring points j0..j1 on side +1 (right/+x) / -1.
        NOTE '+x' is the vehicle's left. side=+1 -> +x."""
        out = []
        for i in range(i0, i1):
            for j in range(j0, j1):
                if side > 0:
                    k = j
                else:
                    k = self.N - j - 1  # edge between left mirror of j+1 and j
                out.append(self.fmap[(i, k)])
        return out

    def extract(self, faces, off):
        """duplicate faces offset along smooth vertex normals; returns temp bmesh"""
        b = bmesh.new()
        vm = {}
        for f in faces:
            vs = []
            for v in f.verts:
                if v not in vm:
                    vm[v] = b.verts.new(v.co + v.normal * off)
                vs.append(vm[v])
            nf = b.faces.new(vs)
            nf.smooth = True
        return b

    def to_part_obj(self, name, mat_name, smooth_angle=40):
        p = Part(name, [mat_name])
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        me.materials.append(mat(mat_name))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def bmesh_from_obj(ob):
    b = bmesh.new()
    b.from_mesh(ob.data)
    return b


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def arc_pts(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


# ----------------------------------------------------------------------------- arches / wheels
def boolean_cut(ob, cutter_ob):
    bpy.context.view_layer.update()
    for v in list(bpy.context.view_layer.objects):
        if v is not None:
            v.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    md = ob.modifiers.new('cut', 'BOOLEAN')
    md.operation = 'DIFFERENCE'
    md.object = cutter_ob
    md.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier='cut')


def cutter_cyl(name, c, r, x0, x1, seg=32):
    me = bpy.data.meshes.new(name)
    b = bmesh.new()
    bmesh.ops.create_cone(b, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=abs(x1 - x0))
    _xform(b, ((x0 + x1) / 2, c[0], c[1]), Matrix.Rotation(math.pi / 2, 3, 'Y'))
    b.to_mesh(me)
    b.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def arch_liner(part, yc, zc, R, zmin, x_in, x_out, m='Trim', n=20):
    """open tube (arc over the top of the wheel above zmin) with a back cap at x_in; part is a Part."""
    s = (zmin - zc) / R
    s = max(-1.0, min(1.0, s))
    phi0 = math.degrees(math.asin(s))
    pts = arc_pts(yc, zc, R, phi0, 180 - phi0, n)
    b = bmesh.new()
    row_in = [b.verts.new((x_in, y, z)) for (y, z) in pts]
    row_out = [b.verts.new((x_out, y, z)) for (y, z) in pts]
    for i in range(len(pts) - 1):
        f = b.faces.new([row_in[i], row_in[i + 1], row_out[i + 1], row_out[i]])
        f.smooth = False
    b.faces.new(row_in)
    part.merge(b, m)
    b.free()


# ----------------------------------------------------------------------------- export / bbox
def export_glb(path, objs=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.view_layer.update()
    for v in list(bpy.context.view_layer.objects):
        if v is not None:
            v.select_set(False)
    for o in (objs or bpy.context.scene.objects):
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                              export_materials='EXPORT', export_cameras=False, export_lights=False,
                              use_selection=True)


def stats():
    tris = 0
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in bpy.context.scene.objects:
        if o.type != 'MESH':
            continue
        dg = bpy.context.evaluated_depsgraph_get()
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        for v in me.vertices:
            w = o.matrix_world @ v.co
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    return tris, mn, mx


# ----------------------------------------------------------------------------- wheels
def wheel_object(name, hub, r, width, rim_r, side, offsets=(0.0,), style='alloy', seg=28):
    """One object: tyre(s)+rim+brake disc, ORIGIN at hub centre, axis = local X.
    side=+1 -> vehicle left (+x) so the dish faces +x; offsets = axial positions of tyres (dual wheels)."""
    p = Part(name, ['Tyre', 'Rim', 'Trim', 'Chrome'])
    for ox in offsets:
        w = width
        prof = [(rim_r * 0.98, ox - w / 2), (r * 0.90, ox - w / 2), (r * 0.972, ox - w * 0.44), (r, ox - w * 0.32),
                (r, ox + w * 0.32), (r * 0.972, ox + w * 0.44), (r * 0.90, ox + w / 2), (rim_r * 0.98, ox + w / 2)]
        revolve(p, (0, 0, 0), prof, 'Tyre', seg=seg, closed=True)
        s = side if len(offsets) == 1 else (1 if ox >= 0 else -1) * side
        # rim barrel + lip
        revolve(p, (0, 0, 0), [(rim_r, ox - w * 0.42), (rim_r * 0.96, ox - w * 0.1), (rim_r, ox + w * 0.42)], 'Rim',
                seg=seg, caps=False)
        xf = ox + s * w * 0.18
        if style == 'alloy':
            cyl(p, (xf, 0, 0), 'x', rim_r * 0.30, w * 0.16, 'Chrome', seg=14)
            for k in range(5):
                a = k * 2 * math.pi / 5
                bx = bmesh.new()
                bmesh.ops.create_cube(bx, size=1.0)
                bmesh.ops.scale(bx, vec=Vector((w * 0.12, rim_r * 0.80, rim_r * 0.34)), verts=bx.verts)
                _xform(bx, (xf, 0, 0), Matrix.Rotation(a, 3, 'X') @ Matrix.Translation((0, 0, 0)).to_3x3())
                bmesh.ops.translate(bx, vec=(0, 0, 0), verts=bx.verts)
                # push spoke outward from the hub along its own axis
                dirv = Vector((0, math.cos(a), math.sin(a)))
                bmesh.ops.translate(bx, vec=dirv * rim_r * 0.42, verts=bx.verts)
                p.merge(bx, 'Rim')
                bx.free()
            cyl(p, (ox - s * w * 0.05, 0, 0), 'x', rim_r * 0.80, w * 0.05, 'Trim', seg=seg)  # brake disc
        else:  # steel / bus
            cyl(p, (ox + s * w * 0.12, 0, 0), 'x', rim_r * 0.96, w * 0.14, 'Rim', seg=seg)
            cyl(p, (ox + s * w * 0.22, 0, 0), 'x', rim_r * 0.42, w * 0.06, 'Chrome', seg=seg)
            for k in range(8):
                a = k * 2 * math.pi / 8
                cyl(p, (ox + s * w * 0.21, rim_r * 0.68 * math.cos(a), rim_r * 0.68 * math.sin(a)), 'x', rim_r * 0.07,
                    w * 0.06, 'Chrome', seg=8)
    ob = p.to_object(smooth_angle=40)
    ob.location = hub
    return ob
