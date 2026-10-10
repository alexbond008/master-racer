"""streatham_hub - Streatham Ice & Leisure Centre + Tesco + flats ('Streatham Hub', 386 Streatham High Rd, 2013, Michael Aukett Architects).

Shape/colour cues (from Commons photos of the real building, Bing image results incl. the architect's CGI, Building.co.uk, Leisure Opportunities):
 1. Leisure block = 3-storey WHITE RENDERED box on a recessed, colourful GLAZED GROUND-FLOOR ARCADE (blue / purple / green / yellow panels, white columns).
 2. Small punched SLOT windows in blue / yellow / green in the white render (not a regular window grid).
 3. A TALL GLAZED CORNER TOWER (blue-violet glass, white fins) carrying a huge VERTICAL BLADE SIGN 'STREATHAM ICE & LEISURE CENTRE'.
 4. The ice-rink hall sits ABOVE/behind the pool podium: a big blue-grey clad volume under a long shallow-curved RUST-BRONZE standing-seam metal roof.
 5. Entrance plaza notch in the south-east corner of the footprint (open forecourt beside the tower).
 6. Tesco store on the west part: pale grey 2-level box, glazed lit shopfront, big blue 'TESCO' sign with red/blue stripes, car-park entrance ramp on Natal Road.
 7. Residential flats (205-250 homes) stacked on top of the Tesco: 5-6 storeys of buff/red brick + render, regular windows, glass-balustrade balconies, set-back top floor.
 8. Overall ~86 x 52 m on the OSM footprint (rotated -4 deg), leisure block ~21 m to the eaves with rink roof peaking ~22 m, flats ~31 m.
"""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sl_lib import *
from mathutils import Vector

THETA = -4.0
rng = random.Random(7)
b = Builder(THETA)

# ------------------------------------------------------------------ materials
define('Render_White', '#e8e6df', rough=0.85)
define('Render_Dark', '#4a4f57', rough=0.8)
define('Render_Grey', '#b8bcc1', rough=0.8)
define('Hall_Clad', '#6f7d8c', rough=0.55, metal=0.4)
define('Rust_Roof', '#7f4125', rough=0.45, metal=0.6)
define('Rust_Seam', '#5a2a16', rough=0.5, metal=0.6)
define('Glass_Blue_Lit', '#2c3fa8', rough=0.1, metal=0.2, emit=1.0, emit_hex='#4e63e0')
define('Panel_Blue', '#2155c8', rough=0.3, emit=1.8)
define('Panel_Purple', '#6a2fb0', rough=0.3, emit=1.8)
define('Panel_Green', '#3aa857', rough=0.3, emit=1.8)
define('Panel_Yellow', '#f0c020', rough=0.3, emit=2.2)
define('Glass_Lit_Warm', '#ffe2b0', rough=0.15, emit=2.6)
define('Sign_Blue', '#1a4fd0', rough=0.4, emit=4.0)
define('Tesco_Blue', '#00539f', rough=0.4, emit=4.5)
define('Tesco_Red', '#ee1c2e', rough=0.4, emit=4.5)
define('Brick_Buff', '#c9b58c', rough=0.9)
define('Brick_Red', '#9a4e39', rough=0.9)
define('Tesco_Wall', '#c9ccd0', rough=0.8)
define('Balcony_Glass', '#9fc3d0', rough=0.1, metal=0.1, emit=0.4)
define('Metal_Dark', '#2b2e33', rough=0.5, metal=0.6)

xW, xT, xE = -51.7, -22.0, 30.7
yS, yN = -22.7, 24.8
nx, ny = 20.9, -2.1      # notch corner (forecourt cut out of SE corner)
H_POD = 12.6             # podium height
H_HALL = 16.4            # rink hall eaves

# ================================================================== LEISURE CENTRE
# ground floor (recessed arcade on the front)
ground = [(-22, -20.7), (14.0, -20.7), (14.0, yS), (nx, yS), (nx, ny), (xE, ny), (xE, yN), (-22, yN)]
b.prism('Render_Dark', ground, 0, 4.8)
# upper podium (overhangs the arcade)
upper = [(-22, yS), (nx, yS), (nx, ny), (xE, ny), (xE, yN), (-22, yN)]
b.prism('Render_White', upper, 4.8, H_POD)
# string course
b.bbox('Render_Grey', -22.1, 14.0, yS - 0.12, yS + 0.1, 4.55, 4.85)
b.bbox('Render_Grey', -22.1, 20.95, yS - 0.12, yS + 0.1, H_POD - 0.1, H_POD + 0.5)  # parapet cap
b.bbox('Render_Grey', 20.8, 21.05, yS, ny, H_POD - 0.1, H_POD + 0.5)

# columns + coloured glazing along the arcade
cols = ['Panel_Blue', 'Glass_Lit_Warm', 'Panel_Purple', 'Glass_Lit_Warm', 'Panel_Green', 'Glass_Lit_Warm', 'Panel_Blue', 'Panel_Yellow']
xs = [-22 + i * 4.5 for i in range(9)]
for i in range(8):
    x0, x1 = xs[i], xs[i + 1]
    b.bbox(cols[i], x0 + 0.35, x1 - 0.35, -20.75, -20.6, 0.2, 4.4)
for x in xs:
    b.box('Render_White', x, yS + 1.2, 0, 0.55, 0.55, 4.8)
b.bbox('Glass_Dark', -22, 14.0, -20.65, -20.55, 0.0, 0.2)

# coloured slot windows on front podium face
def slot(i, j):
    r = rng.random()
    if r < 0.30: return 'Panel_Blue'
    if r < 0.45: return 'Panel_Yellow'
    if r < 0.55: return 'Panel_Green'
    return 'Glass_Dark' if r < 0.8 else None
b.windows('x', yS, -21.0, 12.5, 4.8, H_POD, 0.9, 2.3, 2.6, 3.8, slot, out=-1, depth=0.14, sill=1.1)
# big pool-hall window band
b.bbox('Emit_Window_Cool', -19.5, -3.5, yS - 0.14, yS, 5.9, 8.4)
for x in [-19.5 + i * 2.0 for i in range(9)]:
    b.bbox('Render_White', x - 0.07, x + 0.07, yS - 0.16, yS - 0.1, 5.9, 8.4)

# tower (glazed corner)
b.bbox('Glass_Blue_Lit', 13.6, nx, yS, -12.5, 0, 21.0)
for i in range(9):
    x = 13.6 + i * (nx - 13.6) / 8
    b.bbox('Render_White', x - 0.12, x + 0.12, yS - 0.25, yS, 0.0, 21.0)
for z in (4.8, 12.6, 21.0):
    b.bbox('Render_White', 13.5, nx + 0.1, yS - 0.3, -12.4, z - 0.1, z + 0.25)
# vertical blade sign on tower front
b.bbox('Render_White', 15.2, 19.3, yS - 0.5, yS - 0.3, 5.5, 20.4)
b.text('Sign_Blue', 'STREATHAM', 18.0, yS - 0.52, 12.95, 2.9, roll=90, extrude=0.12)
b.text('Sign_Blue', 'ICE & LEISURE CENTRE', 19.2, yS - 0.52, 12.95, 1.15, roll=90, extrude=0.12)
# tower east face sign band too
b.bbox('Glass_Blue_Lit', nx, nx + 0.1, yS + 1, -12.5, 0, 4.8)

# east wall of notch (face x=nx, normal +x) and notch back wall (face y=ny, normal -y)
b.windows('y', nx, yS + 0.5, -12.6, 4.8, H_POD, 0.9, 2.3, 2.8, 3.8, slot, out=1, sill=1.0)
b.windows('x', ny, nx + 1.2, xE - 1.0, 4.8, H_POD, 0.9, 2.3, 2.6, 3.8, slot, out=-1, sill=1.0)
b.bbox('Glass_Lit_Warm', nx + 1.2, xE - 1.2, ny - 0.1, ny, 0.2, 4.4)  # entrance glazing
b.text('Sign_Blue', 'ICE & LEISURE', (nx + xE) / 2, ny - 0.2, 6.0, 1.15, extrude=0.1)

# ---- rink hall above/behind
b.bbox('Hall_Clad', -22, xE, -6.0, yN, H_POD, H_HALL)
b.bbox('Emit_Window_Cool', -20.0, 29.5, -6.06, -6.0, 13.6, 15.4)   # clerestory band on south face
for i in range(14):
    x = -20.0 + i * (49.5 / 13)
    b.bbox('Render_Grey', x - 0.1, x + 0.1, -6.2, -6.0, 13.6, 15.4)
b.bbox('Emit_Window_Cool', xE, xE + 0.06, -2.0, 22.0, 13.8, 15.2)    # east face clerestory
# curved standing-seam roof (arc across Y, ridge along X)
RISE = 5.2
yA, yB = -6.4, yN + 0.4
def arc(off=0.0, n=14):
    pts = []
    for k in range(n + 1):
        y = yA + (yB - yA) * k / n
        t = (y - (yA + yB) / 2) / ((yB - yA) / 2)
        pts.append((y, H_HALL + RISE * (1 - t * t) + off))
    return pts
roof_pts = arc() + [(yB, H_HALL - 0.35), (yA, H_HALL - 0.35)]
b.profile_y('Rust_Roof', roof_pts, -22.4, xE + 0.4)
n_ribs = 44
for r in range(n_ribs):
    x = -22.0 + (xE - (-22.0)) * r / (n_ribs - 1)
    up = arc(0.14)
    lo = arc(0.0)
    b.profile_y('Rust_Seam', up + lo[::-1], x - 0.05, x + 0.05)
# roof edge fascia
b.bbox('Metal_Dark', -22.4, xE + 0.4, yA - 0.05, yA + 0.05, H_HALL - 0.45, H_HALL + 0.05)

# upper windows etc on hall north/east (dark panel louvres)
b.windows('x', yN, -20.0, 29.0, 4.8, H_HALL, 1.2, 1.6, 3.5, 4.0, lambda i, j: 'Glass_Dark' if rng.random() < 0.6 else None, out=1, sill=1.5)
b.windows('y', xE, -1.0, 22.5, 4.8, H_POD, 0.9, 2.2, 3.2, 3.8, lambda i, j: 'Glass_Dark' if rng.random() < 0.6 else None, out=1, sill=1.0)

# ================================================================== TESCO STORE
b.bbox('Tesco_Wall', xW, xT, yS, yN, 0, 10.2)
b.bbox('Render_Grey', xW - 0.1, xT + 0.1, yS - 0.12, yS + 0.05, 9.7, 10.4)
# glazed lit shopfront
b.bbox('Glass_Lit_Warm', -46.0, -24.0, yS - 0.12, yS, 0.3, 4.6)
for x in [-46.0 + i * 2.2 for i in range(11)]:
    b.bbox('Metal_Dark', x - 0.06, x + 0.06, yS - 0.18, yS - 0.1, 0.0, 4.7)
b.bbox('Metal_Dark', -46.2, -23.8, yS - 0.5, yS - 0.1, 4.6, 5.0)  # entrance canopy
# sign
b.bbox('Emit_Sign', -46.0, -24.0, yS - 0.25, yS - 0.1, 6.0, 9.4)
b.text('Tesco_Blue', 'TESCO', -35.0, yS - 0.27, 6.9, 2.2, extrude=0.1)
b.bbox('Tesco_Red', -46.0, -24.0, yS - 0.27, yS - 0.1, 6.35, 6.55)
b.bbox('Tesco_Blue', -46.0, -24.0, yS - 0.27, yS - 0.1, 6.0, 6.2)
# upper store level: louvred car-park deck panels
b.bbox('Render_Grey', -46.0, -24.0, yS - 0.1, yS, 4.9, 5.9)
# car-park entrance ramp opening
b.bbox('Metal_Dark', -50.4, -47.0, yS - 0.12, yS, 0.0, 4.2)
b.bbox('Sign_Blue', -49.4, -48.0, yS - 0.14, yS - 0.12, 4.4, 5.4)
b.text('Emit_Sign', 'P', -48.7, yS - 0.17, 4.55, 0.85, extrude=0.04)
# west face and north face of store: plain with a loading-bay door
b.bbox('Metal_Dark', -40.0, -33.0, yN, yN + 0.1, 0.0, 4.5)

# ================================================================== FLATS on Tesco
# main block over the rear (north) of the store
fl_top = 27.6
b.bbox('Brick_Buff', xW, xT, -4.0, yN, 10.2, fl_top)
# front-left wing (red brick) over the front-west
b.bbox('Brick_Red', xW, -43.5, yS, -4.0, 10.2, 24.4)
# render attic floor, set back
b.bbox('Render_Grey', -49.0, -26.0, 2.0, 22.0, fl_top, fl_top + 2.9)
b.bbox('Metal_Dark', -49.3, -25.7, 1.7, 22.3, fl_top + 2.9, fl_top + 3.2)
# stair core / corner tower NW
b.bbox('Brick_Red', xW, -45.0, 17.0, yN, fl_top, fl_top + 5.0)
b.bbox('Metal_Dark', xW - 0.2, -44.8, 16.8, yN + 0.2, fl_top + 5.0, fl_top + 5.3)
# parapets
b.bbox('Render_Grey', xW - 0.1, xT + 0.1, -4.1, -3.8, fl_top - 0.2, fl_top + 0.5)
b.bbox('Render_Grey', xW - 0.1, -43.4, yS - 0.1, yS + 0.2, 24.2, 24.9)

def flat_win(i, j):
    r = rng.random()
    return 'Emit_Window' if r < 0.38 else ('Glass_Dark' if r < 0.95 else 'Emit_Window_Cool')

# windows: front-wing front (y=yS) and side
b.windows('x', yS, xW + 0.8, -43.5 - 0.8, 10.2, 24.4, 1.5, 1.6, 2.8, 2.8, flat_win, out=-1, sill=0.8)
b.windows('y', xW, yS + 1.0, -5.0, 10.2, 24.4, 1.5, 1.6, 3.0, 2.8, flat_win, out=-1, sill=0.8)
b.windows('y', -43.5, yS + 1.0, -5.0, 10.2, 24.4, 1.5, 1.6, 3.0, 2.8, flat_win, out=1, sill=0.8)
# main block faces
b.windows('x', -4.0, -43.5, xT - 0.8, 10.2, fl_top, 1.5, 1.6, 3.0, 2.8, flat_win, out=-1, sill=0.8)
b.windows('y', xW, -3.0, yN - 1.0, 10.2, fl_top, 1.5, 1.6, 3.0, 2.8, flat_win, out=-1, sill=0.8)
b.windows('x', yN, xW + 1.0, xT - 1.0, 10.2, fl_top, 1.5, 1.6, 3.0, 2.8, flat_win, out=1, sill=0.8)
b.windows('y', xT, -3.0, yN - 1.0, H_POD, fl_top, 1.5, 1.6, 3.0, 2.8, flat_win, out=1, sill=0.8)
b.windows('x', 2.0 - 0.0, -48.0, -27.0, fl_top, fl_top + 2.9, 1.8, 1.5, 3.0, 3.0, flat_win, out=-1, sill=0.7)
# balconies on south face of main block (facing Natal Road side)
for fl in range(5):
    z = 10.2 + 0.2 + fl * 2.8 + 2.8
    for k in range(5):
        x = -41.0 + k * 3.8
        b.bbox('Concrete', x - 1.3, x + 1.3, -4.0 - 1.3, -4.0, z, z + 0.15)
        b.bbox('Balcony_Glass', x - 1.3, x + 1.3, -4.0 - 1.3, -4.0 - 1.2, z + 0.15, z + 1.2)
        b.bbox('Balcony_Glass', x - 1.3, x - 1.2, -4.0 - 1.3, -4.0, z + 0.15, z + 1.2)
        b.bbox('Balcony_Glass', x + 1.2, x + 1.3, -4.0 - 1.3, -4.0, z + 0.15, z + 1.2)
# balconies on the east face
for fl in range(5):
    z = H_POD + 0.2 + fl * 2.8 + 0.4
    if z + 1.2 > fl_top: break
    for k in range(5):
        y = -1.0 + k * 4.8
        b.bbox('Concrete', xT, xT + 1.3, y - 1.2, y + 1.2, z, z + 0.15)
        b.bbox('Balcony_Glass', xT + 1.2, xT + 1.3, y - 1.2, y + 1.2, z + 0.15, z + 1.2)
# roof plant on Tesco/front deck roof (visible between flats and tower)
for (x, y, sx, sy, h) in [(-38, -12, 3, 2.5, 1.4), (-31, -16, 2.2, 3, 1.2), (-27, -9, 2.4, 2.4, 1.7)]:
    b.box('Metal_Dark', x, y, 10.2, sx, sy, h)

V = Vector
CAMS = {
    'front34': (V((-0.8, -1.0, 0.42)), 1.0),
    'rear34': (V((0.8, 1.0, 0.45)), 1.0),
    'side': (V((1.0, -0.1, 0.22)), 1.0),
    'front': (V((0.0, -1.0, 0.2)), 1.0),
    'top': (V((0.12, -0.5, 1.4)), 1.0),
    'tower_close': (V((0.3, -1.0, 0.12)), 1.0, wpt(THETA, 15, -22, 10), 18),
    'east34': (V((1.0, -0.8, 0.35)), 1.0),
}
b.finish('streatham_hub', footprint=FOOT['streatham_hub']['footprint_bbox_m'],
         notes='Streatham Ice & Leisure Centre + Tesco + flats (Streatham Hub 2013). Built on OSM footprint rotated -4deg; front faces -Y (Natal Road side). '
               'White-render leisure block on coloured glazed arcade, glazed corner tower with vertical blade sign, rust standing-seam curved roof over rink hall, '
               'Tesco store with lit TESCO sign, flats stacked above. Materials: Emit_* are lit windows/signs.', cams=CAMS)
