"""Builder/preview helpers for the Streatham/Brixton landmark scripts (streatham_hub, st_leonards, english_martyrs,
theatre, ritzy). Separate from lm_common.py (another landmark author's file).

Pattern:  b = Builder(theta_deg); b.box(...); ...; b.finish(key, notes=...)
All build coordinates are in a LOCAL frame (front = -Y, ground z=0, origin = footprint centroid); the whole model
is rotated by theta (deg, CCW) about the origin on finish so that it lies on the real OSM footprint.
"""
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix, Euler

ROOT = os.path.expanduser('~/Projects/master-racer')
OUT_DIR = os.path.join(ROOT, 'public/models/landmarks')
PREV_DIR = os.path.join(ROOT, 'blender/previews')
FOOT = json.load(open(os.path.join(ROOT, 'blender/landmark_footprints.json')))

MATS = {}


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c)


def define(name, hexcol, rough=0.8, metal=0.0, emit=0.0, emit_hex=None):
    MATS[name] = dict(color=srgb(hexcol), rough=rough, metal=metal, emit=emit, emit_color=srgb(emit_hex or hexcol))


def make_material(name):
    spec = MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    c = spec['color']
    bsdf.inputs['Base Color'].default_value = (c[0], c[1], c[2], 1)
    bsdf.inputs['Roughness'].default_value = spec['rough']
    bsdf.inputs['Metallic'].default_value = spec['metal']
    if spec['emit'] > 0:
        ec = spec['emit_color']
        bsdf.inputs['Emission Color'].default_value = (ec[0], ec[1], ec[2], 1)
        bsdf.inputs['Emission Strength'].default_value = spec['emit']
    return m


def common_materials():
    define('Glass_Dark', '#1c2733', rough=0.06, metal=0.2)
    define('Emit_Window', '#ffd9a0', rough=0.4, emit=4.0)
    define('Emit_Window_Cool', '#bfe3ff', rough=0.4, emit=3.5)
    define('Emit_Sign', '#ffffff', rough=0.4, emit=5.0)
    define('Slate', '#3b4048', rough=0.7, metal=0.05)
    define('Concrete', '#8d8a84', rough=0.9)
    define('Trim_Dark', '#22252b', rough=0.6, metal=0.3)


def local_poly(key, theta):
    P = FOOT[key]['polygon_blender_xy']
    c, s = math.cos(-math.radians(theta)), math.sin(-math.radians(theta))
    return [(x * c - y * s, x * s + y * c) for x, y in P]


class Builder:
    def __init__(self, theta=0.0):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.theta = theta
        self.bm = {}
        MATS.clear()
        common_materials()

    def _bm(self, mat):
        if mat not in self.bm:
            assert mat in MATS, 'undefined material ' + mat
            self.bm[mat] = bmesh.new()
        return self.bm[mat]

    def _solid(self, bm, faces, tri=None):
        if tri:
            bmesh.ops.triangulate(bm, faces=tri, quad_method='BEAUTY', ngon_method='EAR_CLIP')
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in faces if f.is_valid])

    # ---- primitives -------------------------------------------------
    def prism(self, mat, poly, z0, z1):
        """Extrude 2D polygon (any winding, may be concave) between z0 and z1."""
        bm = self._bm(mat)
        n = len(poly)
        bot = [bm.verts.new((x, y, z0)) for x, y in poly]
        top = [bm.verts.new((x, y, z1)) for x, y in poly]
        fs = [bm.faces.new([bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]]) for i in range(n)]
        ft = bm.faces.new(top)
        fb = bm.faces.new(bot[::-1])
        self._solid(bm, fs + [ft, fb], tri=[ft, fb])

    def box(self, mat, cx, cy, z0, sx, sy, sz, rot=0.0):
        hx, hy = sx / 2, sy / 2
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = [(cx + x * c - y * s, cy + x * s + y * c) for x, y in [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]]
        self.prism(mat, pts, z0, z0 + sz)

    def bbox(self, mat, x0, x1, y0, y1, z0, z1):
        self.box(mat, (x0 + x1) / 2, (y0 + y1) / 2, min(z0, z1), abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))

    def profile_x(self, mat, pts, y0, y1):
        """(x,z) polygon in XZ plane extruded along +y from y0 to y1."""
        bm = self._bm(mat)
        n = len(pts)
        f = [bm.verts.new((x, y0, z)) for x, z in pts]
        k = [bm.verts.new((x, y1, z)) for x, z in pts]
        fs = [bm.faces.new([f[i], f[(i + 1) % n], k[(i + 1) % n], k[i]]) for i in range(n)]
        fa = bm.faces.new(f)
        fb = bm.faces.new(k[::-1])
        self._solid(bm, fs + [fa, fb], tri=[fa, fb])

    def profile_y(self, mat, pts, x0, x1):
        """(y,z) polygon in YZ plane extruded along +x from x0 to x1."""
        bm = self._bm(mat)
        n = len(pts)
        f = [bm.verts.new((x0, y, z)) for y, z in pts]
        k = [bm.verts.new((x1, y, z)) for y, z in pts]
        fs = [bm.faces.new([f[i], f[(i + 1) % n], k[(i + 1) % n], k[i]]) for i in range(n)]
        fa = bm.faces.new(f)
        fb = bm.faces.new(k[::-1])
        self._solid(bm, fs + [fa, fb], tri=[fa, fb])

    def gable(self, mat, x0, x1, y0, y1, z, rise, ridge='y', oh=0.0):
        """Gabled roof over rectangle; ridge along 'y' (gable ends face +-y) or 'x'."""
        x0 -= oh; x1 += oh; y0 -= oh; y1 += oh
        if ridge == 'y':
            self.profile_x(mat, [(x0, z), (x1, z), ((x0 + x1) / 2, z + rise)], y0, y1)
        else:
            self.profile_y(mat, [(y0, z), (y1, z), ((y0 + y1) / 2, z + rise)], x0, x1)

    def lean(self, mat, x0, x1, y0, y1, z_low, z_high, slope='y+', thick=0.0):
        """Mono-pitch (lean-to) roof: surface rises from z_low to z_high toward the named side ('y+','y-','x+','x-').
        If thick>0 makes a slab of that thickness under the surface; else a solid wedge down to z_low."""
        zb = min(z_low, z_high)
        if slope in ('y+', 'y-'):
            a, b = (z_low, z_high) if slope == 'y+' else (z_high, z_low)
            top = [(y0, a), (y1, b)]
            if thick > 0:
                pts = [(y0, a - thick), (y1, b - thick), (y1, b), (y0, a)]
            else:
                pts = [(y0, zb), (y1, zb), (y1, b), (y0, a)]
            self.profile_y(mat, pts, x0, x1)
        else:
            a, b = (z_low, z_high) if slope == 'x+' else (z_high, z_low)
            if thick > 0:
                pts = [(x0, a - thick), (x1, b - thick), (x1, b), (x0, a)]
            else:
                pts = [(x0, zb), (x1, zb), (x1, b), (x0, a)]
            self.profile_x(mat, pts, y0, y1)

    def hip(self, mat, x0, x1, y0, y1, z, rise, top_frac=0.0):
        bm = self._bm(mat)
        w, d = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if w >= d:
            L = (w - d) + d * top_frac
            tx0, tx1, ty0, ty1 = cx - L / 2, cx + L / 2, cy - d * top_frac / 2, cy + d * top_frac / 2
        else:
            L = (d - w) + w * top_frac
            tx0, tx1, ty0, ty1 = cx - w * top_frac / 2, cx + w * top_frac / 2, cy - L / 2, cy + L / 2
        b = [bm.verts.new(p) for p in [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]]
        t = [bm.verts.new(p) for p in [(tx0, ty0, z + rise), (tx1, ty0, z + rise), (tx1, ty1, z + rise), (tx0, ty1, z + rise)]]
        fs = []
        for i in range(4):
            j = (i + 1) % 4
            if (t[i].co - t[j].co).length > 1e-6:
                fs.append(bm.faces.new([b[i], b[j], t[j], t[i]]))
            else:
                fs.append(bm.faces.new([b[i], b[j], t[i]]))
        if (tx1 - tx0) > 1e-6 and (ty1 - ty0) > 1e-6:
            try:
                fs.append(bm.faces.new(t))
            except ValueError:
                pass
        fs.append(bm.faces.new(b[::-1]))
        self._solid(bm, fs)

    def frustum(self, mat, cx, cy, z, r_base, height, n=8, r_top=0.0, rot=0.0, sx=1.0, sy=1.0):
        """n-gon spire (r_top=0) / frustum / cylinder; circumradius r_base, optional x/y stretch."""
        bm = self._bm(mat)
        a0 = math.radians(rot)
        bs = [bm.verts.new((cx + sx * r_base * math.cos(a0 + 2 * math.pi * i / n), cy + sy * r_base * math.sin(a0 + 2 * math.pi * i / n), z)) for i in range(n)]
        fs = []
        if r_top > 0:
            ts = [bm.verts.new((cx + sx * r_top * math.cos(a0 + 2 * math.pi * i / n), cy + sy * r_top * math.sin(a0 + 2 * math.pi * i / n), z + height)) for i in range(n)]
            for i in range(n):
                fs.append(bm.faces.new([bs[i], bs[(i + 1) % n], ts[(i + 1) % n], ts[i]]))
            ft = bm.faces.new(ts)
            fs.append(ft)
            tri = [ft]
        else:
            apex = bm.verts.new((cx, cy, z + height))
            for i in range(n):
                fs.append(bm.faces.new([bs[i], bs[(i + 1) % n], apex]))
            tri = []
        fb = bm.faces.new(bs[::-1])
        fs.append(fb)
        self._solid(bm, fs, tri=tri + [fb])

    def cyl(self, mat, cx, cy, z0, r, h, n=12, sx=1.0, sy=1.0):
        self.frustum(mat, cx, cy, z0, r, h, n=n, r_top=r, sx=sx, sy=sy)

    def cyl_x(self, mat, x0, x1, cy, cz, r, n=12):
        """cylinder along X (for rink-roof ribs, columns lying down, etc)."""
        bm = self._bm(mat)
        a = [bm.verts.new((x0, cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))) for i in range(n)]
        b = [bm.verts.new((x1, cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))) for i in range(n)]
        fs = [bm.faces.new([a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]]) for i in range(n)]
        fa = bm.faces.new(a[::-1])
        fb = bm.faces.new(b)
        self._solid(bm, fs + [fa, fb], tri=[fa, fb])

    def arch_pts(self, cx, z0, w, h, pointed=False, steps=6):
        """(x,z) outline of a window/door with round or pointed (two-centred) arch top; total height h."""
        hw = w / 2
        if pointed:
            R = w * 0.95
            rise = R * math.sin(math.acos((R - hw) / R))
            zs = z0 + h - rise
            pts = [(cx - hw, z0), (cx + hw, z0), (cx + hw, zs)]
            ang_max = math.acos((R - hw) / R)
            # right arc: centre at (cx + hw - R, zs); goes from angle 0 (at x=cx+hw) to ang_max (apex at cx)
            for i in range(1, steps):
                a = ang_max * i / steps
                pts.append((cx + hw - R + R * math.cos(a), zs + R * math.sin(a)))
            pts.append((cx, z0 + h))
            for i in range(steps - 1, 0, -1):
                a = ang_max * i / steps
                pts.append((cx - hw + R - R * math.cos(a), zs + R * math.sin(a)))
            pts.append((cx - hw, zs))
        else:
            zs = z0 + h - hw
            pts = [(cx - hw, z0), (cx + hw, z0), (cx + hw, zs)]
            for i in range(1, steps):
                a = math.pi * i / steps
                pts.append((cx + hw * math.cos(a), zs + hw * math.sin(a)))
            pts.append((cx - hw, zs))
        return pts

    def arch(self, mat, cx, y, z0, w, h, depth=0.12, pointed=False, steps=6, face='-Y'):
        """Arched slab (window pane / door recess) whose front face lies at plane y; extruded `depth` into -Y direction
        (outward) when face='-Y' i.e. it protrudes toward the street, or into +Y when face='+Y'."""
        pts = self.arch_pts(cx, z0, w, h, pointed, steps)
        if face == '-Y':
            self.profile_x(mat, pts, y - depth, y)
        else:
            self.profile_x(mat, pts, y, y + depth)

    def arch_y(self, mat, x, cy, z0, w, h, out=1, depth=0.1, pointed=True, steps=6):
        """Arched slab on a wall that runs along Y at plane x (outward normal sign `out`)."""
        pts = self.arch_pts(cy, z0, w, h, pointed, steps)
        if out > 0:
            self.profile_y(mat, pts, x, x + depth)
        else:
            self.profile_y(mat, pts, x - depth, x)

    def mesh(self, mat, verts, faces):
        """Arbitrary closed solid from verts [(x,y,z)] and faces [[i..]] (normals auto-fixed)."""
        bm = self._bm(mat)
        vs = [bm.verts.new(v) for v in verts]
        fs = [bm.faces.new([vs[i] for i in f]) for f in faces]
        self._solid(bm, fs)

    def text(self, mat, body, x, y, z, size, rot_z=0.0, align='CENTER', extrude=0.06, face='-Y', spacing=1.0, roll=0.0):
        """Real text as geometry. Plane faces -Y (street) by default. (x,y,z)=baseline centre. rot_z yaws about Z."""
        curve = bpy.data.curves.new('t', 'FONT')
        curve.body = body
        curve.size = size
        curve.align_x = align
        curve.align_y = 'BOTTOM'
        curve.extrude = extrude
        curve.space_line = spacing
        o = bpy.data.objects.new('t', curve)
        bpy.context.scene.collection.objects.link(o)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        bpy.data.objects.remove(o)
        bpy.data.curves.remove(curve)
        me.transform(Matrix.Rotation(math.radians(roll), 4, 'Z'))
        M = Matrix.Rotation(math.radians(90), 4, 'X')
        if face == '+Y':
            M = Matrix.Rotation(math.radians(180), 4, 'Z') @ M
        M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rot_z), 4, 'Z') @ M
        me.transform(M)
        bm = self._bm(mat)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def windows(self, axis, fixed, a0, a1, z0, z1, w, h, pitch_a, pitch_z, mat_fn, out=1, depth=0.12, sill=0.9):
        """Grid of window boxes on an axis-aligned wall.
        axis 'x': wall runs along x at y=fixed;  axis 'y': wall runs along y at x=fixed.  out=+1/-1 outward normal sign.
        Floors start at z0+sill every pitch_z while top <= z1.  mat_fn(i, j) -> material name or None (skip)."""
        n_a = max(1, int((a1 - a0) // pitch_a))
        margin = ((a1 - a0) - (n_a - 1) * pitch_a) / 2
        j = 0
        z = z0 + sill
        while z + h <= z1 + 1e-6:
            for i in range(n_a):
                m = mat_fn(i, j)
                if m:
                    a = a0 + margin + i * pitch_a
                    if axis == 'x':
                        self.box(m, a, fixed + out * depth / 2, z, w, depth, h)
                    else:
                        self.box(m, fixed + out * depth / 2, a, z, depth, w, h)
            j += 1
            z += pitch_z

    # ---- output -----------------------------------------------------
    def finish(self, key, footprint=None, notes='', preview=True, cams=None, extra=None):
        R = Matrix.Rotation(math.radians(self.theta), 4, 'Z')
        objs = []
        for mat, bm in self.bm.items():
            bmesh.ops.transform(bm, matrix=R, verts=list(bm.verts))
            me = bpy.data.meshes.new(mat)
            bm.to_mesh(me)
            bm.free()
            for p in me.polygons:
                p.use_smooth = False
            me.materials.append(make_material(mat))
            o = bpy.data.objects.new(mat, me)
            bpy.context.scene.collection.objects.link(o)
            objs.append(o)
        tris = sum(len(o.data.polygons) for o in objs)
        allv = [v.co for o in objs for v in o.data.vertices]
        mn = Vector((min(v.x for v in allv), min(v.y for v in allv), min(v.z for v in allv)))
        mx = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
        print(f'[{key}] tris={tris} min={tuple(round(c,2) for c in mn)} max={tuple(round(c,2) for c in mx)} '
              f'size={tuple(round(c,2) for c in (mx-mn))}')
        assert tris <= 60000, 'over triangle budget'
        os.makedirs(OUT_DIR, exist_ok=True)
        glb = os.path.join(OUT_DIR, key + '.glb')
        for o in bpy.data.objects:
            o.select_set(False)
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', export_apply=True, export_yup=True,
                                  export_materials='EXPORT', export_cameras=False, export_lights=False,
                                  use_selection=True)
        fp = footprint or [round(mx.x - mn.x, 1), round(mx.y - mn.y, 1)]
        meta = {'footprint': fp, 'height': round(mx.z, 1), 'notes': notes, 'triangles': tris,
                'bbox_min': [round(c, 2) for c in mn], 'bbox_max': [round(c, 2) for c in mx]}
        if extra:
            meta.update(extra)
        json.dump(meta, open(os.path.join(OUT_DIR, key + '.json'), 'w'), indent=1)
        print(f'[{key}] wrote {glb} ({os.path.getsize(glb)/1024:.0f} KB)')
        if preview:
            render_previews(key, glb, cams)
        return mn, mx, tris


def render_previews(key, glb, cams=None, size=(1100, 760)):
    """Re-import exported GLB (validates export + prints its bbox), then render preview views."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    allv = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
    mn = Vector((min(v.x for v in allv), min(v.y for v in allv), min(v.z for v in allv)))
    mx = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
    print(f'[{key}] GLB re-import bbox (Blender axes) min={tuple(round(c,2) for c in mn)} max={tuple(round(c,2) for c in mx)} '
          f'size={tuple(round(c,2) for c in (mx-mn))}')
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', 'CYCLES'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    if sc.render.engine == 'CYCLES':
        sc.cycles.samples = 24
    sc.render.resolution_x, sc.render.resolution_y = size
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.20, 0.26, 0.40, 1)
    bg.inputs[1].default_value = 0.9
    ext = max(mx.x - mn.x, mx.y - mn.y)
    bpy.ops.mesh.primitive_plane_add(size=ext * 4, location=((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, -0.02))
    g = bpy.context.active_object
    gm = bpy.data.materials.new('ground')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.09, 0.10, 1)
    gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
    g.data.materials.append(gm)
    for nm, en, col, rot in (('sun', 3.2, (1.0, 0.82, 0.62), (52, 0, -35)), ('fill', 1.1, (0.6, 0.7, 1.0), (60, 0, 150))):
        l = bpy.data.lights.new(nm, 'SUN')
        l.energy = en
        l.color = col
        o = bpy.data.objects.new(nm, l)
        sc.collection.objects.link(o)
        o.rotation_euler = Euler([math.radians(a) for a in rot], 'XYZ')
    c = (mn + mx) / 2
    H = mx.z
    views = cams or {
        'front34': (Vector((-0.8, -1.0, 0.42)), 1.0),
        'rear34': (Vector((0.8, 1.0, 0.45)), 1.0),
        'side': (Vector((1.0, -0.1, 0.22)), 1.0),
        'front': (Vector((0.0, -1.0, 0.2)), 1.0),
        'top': (Vector((0.12, -0.5, 1.4)), 1.0),
    }
    os.makedirs(PREV_DIR, exist_ok=True)
    cd = bpy.data.cameras.new('cam')
    cd.lens = 35
    cd.clip_end = 3000
    co = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(co)
    sc.camera = co
    for name, spec in views.items():
        dirv, zoom = spec[0], spec[1]
        target = Vector(spec[2]) if len(spec) > 2 else Vector((c.x, c.y, H * 0.4))
        d = dirv.normalized()
        # fit: bounding-sphere radius
        rad = max(((mx - mn).length) / 2, 8) if len(spec) <= 2 else spec[3]
        fov = 2 * math.atan(18 / cd.lens)
        dist = rad / math.sin(fov / 2) * 1.0 / zoom
        co.location = target + d * dist
        co.rotation_euler = (target - co.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(PREV_DIR, f'{key}_{name}.png')
        bpy.ops.render.render(write_still=True)
    print(f'[{key}] previews -> {PREV_DIR}/{key}_*.png')


def wpt(theta, x, y, z=0.0):
    """local-frame point -> world (Blender) point after the build rotation."""
    c, s = math.cos(math.radians(theta)), math.sin(math.radians(theta))
    return (x * c - y * s, x * s + y * c, z)
