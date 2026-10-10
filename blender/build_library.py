# Peckham Library (Will Alsop, 2000). Cues (from Commons photos + archiweb/c20/Wikipedia text):
# 1 inverted L: five-storey vertical stem + horizontal arm cantilevered ~12 m above a plaza
# 2 arm soffit carried on thin DARK steel raking columns at random angles, soffit dark bronze/timber with downlights
# 3 pre-patinated seamed copper, pale turquoise-green, horizontal panel seams, on end faces
# 4 long faces: vertical stripes of saturated coloured glass (lime-yellow, red, orange, green, teal, blue, black, clear)
# 5 vermilion 'beret' pod (dome with brim) + a 2nd pod piercing the roof, stainless 'LIBRARY' letters 2 m high on the front roof edge
# R2: undulating fine-louvre mesh screen on +X long face, staggered copper seams (horizontal+vertical), columns of varied thickness, bigger beret
# 6 stem ground floors glazed (lit info/media centre); stair/lift core and plant on roof
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lm_common import *
reset()
rng = random.Random(7)
b = B().frame(-1.3, 4.1, 6.7)       # footprint rect centre + yaw from OSM polygon
W, D = 25.0, 42.6; hx, hy = W/2, D/2
H = 22.0; Z_ARM = 12.0; YS = 0.0     # stem begins at local y=0
cuA = mat('Copper_A', (132, 204, 180), 0.45, 0.3)
cuB = mat('Copper_B', (108, 178, 156), 0.5, 0.3)
cuC = mat('Copper_C', (150, 214, 190), 0.45, 0.3)
soff = mat('Soffit', (74, 50, 34), 0.7)
steel = mat('Steel', (38, 40, 46), 0.4, 0.8)
roof = mat('Roof', (96, 108, 104), 0.8)
dark = mat('Glass_Dark', (22, 30, 42), 0.1, 0.5)
beret = mat('Beret', (235, 70, 25), 0.35, 0.1, emit=(255, 80, 20), strength=0.8)
pod2 = mat('Pod_Pale', (170, 200, 190), 0.4, 0.5)
steelc = mat('Stainless', (200, 205, 210), 0.3, 0.9)
cuS = mat('Copper_Seam', (70, 124, 108), 0.6, 0.3)
meshm = mat('Mesh_Screen', (205, 210, 214), 0.35, 0.9)
signm = mat('Emit_Sign', (255, 255, 255), 0.4, emit=(235, 245, 255), strength=3.5)
winw = mat('Emit_Window', (255, 214, 140), 0.3, emit=(255, 196, 110), strength=3.5)
pal = [('lime', (205, 235, 40)), ('red', (225, 35, 40)), ('orange', (245, 120, 30)), ('green', (30, 170, 70)),
       ('teal', (20, 160, 160)), ('blue', (40, 90, 220)), ('black', (18, 18, 22)), ('yellow', (250, 220, 40)),
       ('clear', (110, 150, 200)), ('magenta', (200, 30, 110))]
gm = {n: mat('Emit_Glass_' + n, c, 0.15, 0.2, emit=c, strength=(0.3 if n == 'black' else 1.1 if n != 'clear' else 0.7)) for n, c in pal}
seq = ['lime', 'lime', 'clear', 'red', 'orange', 'clear', 'green', 'teal', 'black', 'clear', 'lime', 'yellow', 'blue', 'clear', 'red', 'magenta', 'clear', 'lime', 'teal', 'blue', 'clear', 'orange', 'green', 'black']

# ---- structural core boxes (copper skin)
b.box(cuA, -hx, hx, YS, hy, 0, H)                       # stem full height
b.box(cuA, -hx, hx, -hy, YS, Z_ARM, H)                  # arm
b.box(soff, -hx, hx, -hy, YS, Z_ARM - 0.7, Z_ARM, top=False)   # soffit slab (drawn below arm)
b.box(roof, -hx - 0.1, hx + 0.1, -hy - 0.1, hy + 0.1, H, H + 0.35)  # roof slab / parapet cap

# ---- copper panel seams on end faces (horizontal strips) -- -Y end (arm), +Y end (stem back), and stem/arm sides partially
def seams(y, ny, z0, z1, x0, x1, ph=1.15):
    z = z0; k = 0
    while z + ph <= z1 + 1e-6:
        b.wrect(cuB if k % 3 == 1 else (cuC if k % 3 == 2 else cuA), (x0, y, z), (1, 0), (0, ny), x1 - x0, ph - 0.06, off=0.03)
        xj = x0 + (0.9 if k % 2 else 0.0)
        while xj < x1 - 0.1:
            b.wrect(cuS, (xj, y, z), (1, 0), (0, ny), 0.05, ph - 0.06, off=0.05)
            xj += 1.8
        b.wrect(cuS, (x0, y, z - 0.03), (1, 0), (0, ny), x1 - x0, 0.05, off=0.05)
        z += ph; k += 1
seams(-hy, -1, Z_ARM, H, -hx, hx)
seams(hy, 1, 0.0, H, -hx, hx)
# small square dark windows on copper ends
for zz in (14.0, 17.5, 20.5):
    for xx in (-8.0, -2.5, 3.0, 8.5):
        b.wrect(dark, (xx, -hy, zz), (1, 0), (0, -1), 1.6, 1.6, off=0.07)
for zz in (4.0, 8.5, 13.0, 17.5):
    for xx in (-7.5, -1.5, 5.0):
        b.wrect(winw if rng.random() < 0.5 else dark, (xx, hy, zz), (1, 0), (0, 1), 1.6, 1.8, off=0.07)

# ---- coloured glass long faces
def stripes(x, nx, y0, y1, z0, z1, seed):
    r = random.Random(seed); y = y0; i = r.randint(0, 5)
    while y < y1 - 0.2:
        w = min(r.uniform(0.9, 1.9), y1 - y)
        if seq[i % len(seq)] in ('lime', 'yellow') and r.random() < 0.5: w = min(w + 0.7, y1 - y)
        n = seq[i % len(seq)]
        b.wrect(gm[n], (x, y if nx > 0 else y + w, z0), (0, 1) if nx > 0 else (0, -1), (nx, 0), w - 0.05, z1 - z0, off=0.05)
        y += w; i += 1
stripes(hx, 1, YS, hy, 0.0, H, 11)        # stem, +X side
stripes(hx, 1, -hy, YS, Z_ARM, H, 12)     # arm, +X side
stripes(-hx, -1, YS, hy, 0.0, H, 13)      # stem, -X side
stripes(-hx, -1, -hy, YS, Z_ARM, H, 14)   # arm, -X side
# floor-line mullion bands + hopper vents
for x, nx in ((hx, 1), (-hx, -1)):
    for k in range(1, 5):
        z = k * 4.4
        yy0 = -hy if z > Z_ARM else YS
        if z >= Z_ARM - 0.1 or True:
            ya = YS if z < Z_ARM else -hy
            b.box(steel, x + 0.0, x + nx * 0.14, ya, hy, z - 0.12, z + 0.12, top=True, bottom=True)
# stem ground-floor (z<12) base glazing zone on its front face (y=YS facing -Y, under the arm): lit info centre
for i in range(8):
    x0 = -hx + 0.8 + i * 3.0
    b.wrect(winw if i % 3 else dark, (x0, YS, 0.4), (1, 0), (0, -1), 2.6, 5.2, off=0.06)
    b.wrect(winw if i % 2 else dark, (x0, YS, 6.4), (1, 0), (0, -1), 2.6, 4.6, off=0.06)
    b.box(steel, x0 - 0.2, x0 - 0.05, YS - 0.1, YS - 0.03, 0.0, Z_ARM)
# ---- raking steel columns under the arm
r = random.Random(3)
cl = [(-10.5, -19.5, 0.36), (-4.0, -19.0, 0.2), (2.0, -19.5, 0.28), (8.0, -19.0, 0.2), (11.5, -18.5, 0.34),
      (-10.0, -11.0, 0.22), (-2.0, -10.5, 0.4), (5.0, -11.0, 0.18), (11.0, -10.0, 0.26),
      (-9.0, -3.0, 0.3), (-2.5, -2.5, 0.16), (4.5, -3.0, 0.38), (11.0, -2.5, 0.2)]
for (xt, yt, rad) in cl:
    top = (xt + r.uniform(-0.4, 0.4), yt, Z_ARM - 0.7)
    sgx = r.choice((-1, 1)); sgy = r.choice((-1, 1))
    bot = (xt + sgx * r.uniform(0.8, 3.2), yt + sgy * r.uniform(0.8, 3.0), 0.0)
    b.beam(steel, bot, top, w=rad, n=7)
    b.cyl(steel, bot[0], bot[1], 0.0, 0.25, rad * 1.5, n=7)
# downlights under soffit
for yy in (-18, -12, -6, -1.5):
    for xx in (-8, -2.7, 2.7, 8):
        b.wrect(winw, (xx - 0.25, yy, Z_ARM - 0.72), (1, 0), (0, 1), 0.5, 0.5, off=0.0) if False else \
            b.quad(winw, (xx-0.3, yy-0.3, Z_ARM-0.72), (xx-0.3, yy+0.3, Z_ARM-0.72), (xx+0.3, yy+0.3, Z_ARM-0.72), (xx+0.3, yy-0.3, Z_ARM-0.72))
# ---- roof: pods, core, plant
b.cyl(beret, 0.5, -9.5, H + 0.2, H + 1.2, 3.4, n=20)                                  # drum
b.ellipsoid(beret, 0.5, -9.5, H + 1.2, 6.4, 5.0, 3.4, nu=20, nv=8, zmin=0.0)       # big dome
b.cyl(beret, 0.5, -9.5, H + 1.0, H + 1.5, 8.2, n=24)                              # brim disc
b.ellipsoid(pod2, 6.0, -2.0, H + 0.2, 3.2, 3.0, 2.6, nu=12, nv=5, zmin=0.0)
b.ellipsoid(pod2, -6.5, 5.0, H + 0.2, 2.6, 2.4, 2.0, nu=12, nv=5, zmin=0.0)
b.box(cuC, 4.5, 10.5, 12.0, 18.0, H + 0.35, H + 4.0)                              # lift/stair core
b.box(steel, 4.5, 10.5, 12.0, 18.0, H + 4.0, H + 4.25)
for k in range(4): b.wrect(winw, (5.2 + k * 1.4, 12.0, H + 1.2), (1, 0), (0, -1), 0.8, 1.8, off=0.05)
b.box(roof, -9, -3, 8, 13, H + 0.35, H + 1.8)
# parapet
for (x0, x1, y0, y1) in ((-hx, hx, hy - 0.2, hy), (-hx, hx, -hy, -hy + 0.2), (-hx, -hx + 0.2, -hy, hy), (hx - 0.2, hx, -hy, hy)):
    b.box(cuB, x0, x1, y0, y1, H + 0.35, H + 0.9)
# undulating louvre mesh screen in front of the +X coloured glass (stem + arm), plus under the soffit
def screen_y(y): return hx + 1.0 + 0.9 * math.sin(y * 0.33) + 0.5 * math.sin(y * 0.9 + 1.0)
yy = -hy + 0.2
while yy < hy - 0.1:
    x = screen_y(yy)
    z0s = Z_ARM - 0.3 if yy < YS else 0.0
    b.box(meshm, x, x + 0.34, yy, yy + 0.05, z0s, H - 0.2)
    yy += 0.3
for k in range(18):        # slim horizontal rails holding the louvres
    pass
yy = -hy + 0.2
while yy < hy - 0.1:
    x = screen_y(yy); x2 = screen_y(yy + 0.9)
    for z in (Z_ARM + 3.0, H - 0.4) if yy < YS else (0.4, 8.0, 15.0, H - 0.4):
        b.beam(meshm, (x, yy, z), (x2, yy + 0.9, z), w=0.05, h=0.08)
    yy += 0.9
# soffit louvres (undersides of the arm), fine lateral slats
yy = -hy + 0.3
while yy < YS - 0.2:
    b.box(meshm, -hx + 0.3, hx - 0.3, yy, yy + 0.06, Z_ARM - 1.05, Z_ARM - 0.7)
    yy += 0.45
objs = b.build('library')
# LIBRARY letters, stainless, glowing slightly, standing on the front roof edge facing -Y
px, py, pz = Frame(-1.3, 4.1, 6.7).p(-3.0, -hy - 0.15, H + 0.9)
t = text_mesh('LIBRARY', 2.1, signm, (px, py, pz), rot=(math.radians(90), 0, math.radians(6.7)), extrude=0.25, name='library_letters')
objs = [o for o in bpy.data.objects if o.type == 'MESH']
# crisp bevel? skip (cost). smooth-shade the pods only
for o in objs:
    if 'Beret' in o.name or 'Pod' in o.name:
        for p in o.data.polygons: p.use_smooth = True
print('TRIS', tri_count(objs))
export('library', 'Peckham Library (Alsop 2000): inverted-L, stem + arm cantilevered 12 m on raking steel columns, patinated copper ends, '
       'coloured-glass long faces, vermilion beret pod, LIBRARY letters. Front (arm end) faces -Y; rotated 6.7 deg to OSM footprint.')
if '--preview' in sys.argv or True:
    shoot = setup_preview('library', (0, 0), 60, H)
    for nm, az, dm, el in (('front34', -35, 1.0, 0.35), ('rear34', 145, 1.0, 0.35), ('side', 90, 0.9, 0.12), ('top', -25, 1.0, 1.0)):
        shoot(nm, az, dm, el)
