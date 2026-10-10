"""theatre - Streatham Hill Theatre (110 Streatham Hill), W G R Sprague & W H Barton 1928-29, Grade II ('unusually lavish').

Cues (Historic England listing, Theatres Trust, Commons photos - CORRECTING the brief: the front is cream FAIENCE, not dark stone/brick):
 1. Steel-framed, brick-clad; the street front is faced in cream-white DOULTON CARRARA TERRACOTTA/faience.
 2. Front in THREE sections: central five-bay block flanked by two four-bay PAVILIONS, each topped by a triangular PEDIMENT with swags/wreath.
 3. Centre: an open PROMENADE BALCONY with balustrade behind a COLONNADE OF FOUR TUSCAN/DORIC COLUMNS 'in antis', two storeys tall; name carried at attic level.
 4. Ground floor: five pairs of entrance doors under a deep flat CANOPY (blue fascia in its bingo years, lit sign); big arched foyer windows glow at night.
 5. Pavilion windows: regular rows of four tall sash windows per level, plain surrounds.
 6. Red PANTILE mansard/hipped roofs show above the cornice behind the pavilions.
 7. Brick (buff-brown) auditorium block (~3,000 seats, ~21 m) and a much taller brick FLY TOWER / stage house (~30 m) at the rear.
 8. Tall vertical lit BLADE SIGNS ('THEATRE' stacked, blue box + glowing letters) at the two ends of the front. Footprint ~31 x 59 m, rotated +3.2 deg.
"""
import sys, os, random, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sl_lib import *
from mathutils import Vector

THETA = 3.2
rng = random.Random(3)
b = Builder(THETA)

define('Faience', '#e7e3d4', rough=0.45)
define('Faience_Shade', '#cfc9b6', rough=0.5)
define('Brick_Buff', '#9c8363', rough=0.95)
define('Brick_Dark', '#7d6248', rough=0.95)
define('Pantile', '#a8452d', rough=0.7)
define('Canopy_Blue', '#1c3d96', rough=0.35, emit=0.8, emit_hex='#2a56d0')
define('Sign_Blue', '#1a3aa8', rough=0.4, emit=1.2, emit_hex='#2a56d0')
define('Sign_Letters', '#ffe9f0', rough=0.4, emit=5.5)
define('Bulb', '#ffe8b0', rough=0.4, emit=6.0)
define('Door_Lit', '#ffd18a', rough=0.3, emit=3.0)
define('Balustrade', '#dcd7c6', rough=0.5)

xL, xR = -18.0, 12.6
yF, yB = -24.0, 35.3
xc = (-8.7 + 3.3) / 2   # centre of central section
XP1, XP2 = -8.7, 3.3    # pavilion/centre boundaries
H_FRONT = 16.0
H_AUD = 21.0
H_FLY = 30.0
YA0, YA1 = -8.0, 17.0   # auditorium extents

# ---------------------------------------------------------------- rear volumes
b.bbox('Brick_Buff', xL + 0.4, xR - 0.2, -9.0, YA1, 0, H_AUD)
b.bbox('Brick_Dark', xL + 0.1, xR + 0.0, YA1, yB, 0, H_FLY)
# auditorium roof: low pantile hip, flat fly tower with parapet
b.hip('Pantile', xL + 0.6, xR - 0.4, -8.6, YA1 - 0.2, H_AUD, 3.0, top_frac=0.15)
b.bbox('Brick_Dark', xL - 0.1, xR + 0.15, yB - 0.4, yB + 0.1, H_FLY, H_FLY + 0.9)
b.bbox('Brick_Dark', xL - 0.1, xR + 0.15, YA1, YA1 + 0.4, H_FLY, H_FLY + 0.9)
b.bbox('Brick_Dark', xL - 0.1, xL + 0.4, YA1, yB, H_FLY, H_FLY + 0.9)
b.bbox('Brick_Dark', xR - 0.3, xR + 0.15, YA1, yB, H_FLY, H_FLY + 0.9)
b.bbox('Concrete', -12.0, -5.0, 22.0, 30.0, H_FLY, H_FLY + 2.2)   # fly-tower roof plant
b.bbox('Concrete', 0.0, 6.0, 20.0, 26.0, H_FLY, H_FLY + 1.6)
# pilaster rhythm + windows on the flanks
for x, out in ((xL, -1), (xR, 1)):
    for y in [-8 + i * 6.2 for i in range(0, 7)]:
        b.bbox('Brick_Dark', x - 0.3 if out < 0 else x, x if out < 0 else x + 0.3, y - 0.35, y + 0.35, 0, H_AUD if y < YA1 else H_FLY)
    b.windows('y', x, -6.0, 15.5, 4.0, H_AUD - 2, 1.4, 3.4, 6.2, 8.0, lambda i, j: 'Glass_Dark' if rng.random() < 0.8 else 'Door_Lit', out=out, sill=0.5)
    b.windows('y', x, 19.0, 34.0, 8.0, H_FLY - 3, 1.4, 2.4, 6.0, 6.0, lambda i, j: 'Glass_Dark' if rng.random() < 0.7 else None, out=out, sill=0.5)
# stage-door and loading bay at the back
b.bbox('Trim_Dark', -4.0, 4.0, yB, yB + 0.1, 0, 5.5)
b.bbox('Door_Lit', xR - 3.0, xR - 1.2, yB, yB + 0.1, 0, 2.6)

# ---------------------------------------------------------------- front block
# ground floor (whole width) + roof mass behind
b.bbox('Faience', xL, xR, yF, -8.0, 0, 5.5)
b.bbox('Brick_Buff', xL + 0.2, xR - 0.2, -12.0, -8.0, 5.5, H_FRONT)
# pavilions (3 storeys with windows)
for (x0, x1) in ((xL, XP1), (XP2, xR)):
    b.bbox('Faience', x0, x1, yF, -9.0, 5.5, H_FRONT)
    # cornice, band courses
    b.bbox('Faience_Shade', x0 - 0.1, x1 + 0.1, yF - 0.35, yF + 0.1, H_FRONT - 0.7, H_FRONT + 0.15)
    b.bbox('Faience_Shade', x0 - 0.05, x1 + 0.05, yF - 0.2, yF + 0.05, 5.5, 5.9)
    b.bbox('Faience_Shade', x0 - 0.05, x1 + 0.05, yF - 0.15, yF + 0.05, 10.3, 10.6)
    # pediment with wreath
    xm = (x0 + x1) / 2
    b.profile_x('Faience', [(x0 - 0.1, H_FRONT + 0.1), (x1 + 0.1, H_FRONT + 0.1), (xm, H_FRONT + 3.3)], yF - 0.1, -22.8)
    b.profile_x('Faience_Shade', [(x0 + 1.0, H_FRONT + 0.2), (x1 - 1.0, H_FRONT + 0.2), (xm, H_FRONT + 2.4)], yF - 0.18, yF - 0.08)
    pts = [(xm + 0.9 * math.cos(2 * math.pi * i / 16), H_FRONT + 1.15 + 0.9 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    b.profile_x('Faience', pts, yF - 0.28, yF - 0.18)
    pts = [(xm + 0.55 * math.cos(2 * math.pi * i / 16), H_FRONT + 1.15 + 0.55 * math.sin(2 * math.pi * i / 16)) for i in range(16)]
    b.profile_x('Faience_Shade', pts, yF - 0.34, yF - 0.28)
    # quoin strips on pavilion outer edges
    qx = x0 if x0 == xL else x1
    # windows: two rows of four
    def pw(i, j):
        return 'Emit_Window' if rng.random() < 0.55 else 'Glass_Dark'
    b.windows('x', yF, x0 + 0.9, x1 - 0.9, 5.9, 15.2, 1.15, 2.3, 2.2, 4.3, pw, out=-1, depth=0.16, sill=0.8)
    # surrounds above windows (tiny pediments/cornices)
    for k in range(4):
        wx = x0 + 0.9 + 0.5 * 0 + k * ((x1 - x0 - 1.8) / 3)
        for z in (6.7, 11.0):
            b.bbox('Faience_Shade', wx - 0.75, wx + 0.75, yF - 0.22, yF, z + 2.3, z + 2.55)
# vertical corner quoins
for x in (xL, xR):
    for z in [6.0 + i * 1.5 for i in range(7)]:
        b.bbox('Faience_Shade', x - 0.05 if x == xL else x - 0.9, x + 0.9 if x == xL else x + 0.05, yF - 0.12, yF, z, z + 0.7)

# central recessed loggia (back wall at y=-22.0)
YR = -22.0
b.bbox('Faience', XP1, XP2, YR, -9.0, 5.5, 16.5)
b.bbox('Faience', XP1, XP2, yF, YR, 5.5, 5.9)            # promenade slab
b.bbox('Balustrade', XP1, XP2, yF, yF + 0.2, 5.9, 7.0)   # balustrade
for x in [XP1 + 0.3 + i * 0.6 for i in range(int((XP2 - XP1) / 0.6))]:
    b.bbox('Faience_Shade', x - 0.07, x + 0.07, yF - 0.05, yF + 0.25, 5.9, 7.1)
# three big arched foyer windows (lit)
for dx in (-3.6, 0, 3.6):
    b.arch('Faience_Shade', xc + dx, YR, 6.2, 3.0, 8.0, depth=0.15, pointed=False, face='-Y')
    b.arch('Emit_Window', xc + dx, YR - 0.1, 6.5, 2.5, 7.4, depth=0.1, pointed=False, face='-Y')
    b.bbox('Faience_Shade', xc + dx - 0.05, xc + dx + 0.05, YR - 0.2, YR - 0.1, 6.5, 13.5)
# four columns
for dx in (-4.2, -1.45, 1.45, 4.2):
    b.cyl('Faience', xc + dx, yF + 1.0, 5.9, 0.5, 9.0, n=14)
    b.bbox('Faience_Shade', xc + dx - 0.7, xc + dx + 0.7, yF + 0.3, yF + 1.7, 14.9, 15.15)  # capital
    b.bbox('Faience_Shade', xc + dx - 0.65, xc + dx + 0.65, yF + 0.35, yF + 1.65, 5.9, 6.2)  # base
# entablature + attic with name
b.bbox('Faience', XP1, XP2, yF, YR + 0.5, 15.1, 16.6)
b.bbox('Faience_Shade', XP1, XP2, yF - 0.2, yF, 16.3, 16.7)
b.bbox('Faience', XP1, XP2, yF + 0.4, YR + 0.8, 16.7, 18.3)
b.bbox('Faience_Shade', XP1, XP2, yF + 0.3, yF + 0.5, 18.1, 18.5)
b.text('Sign_Letters', 'STREATHAM HILL THEATRE', xc, yF + 0.38, 17.15, 0.62, extrude=0.08)

# canopy + marquee bulbs + doors
b.bbox('Canopy_Blue', xL + 1.0, xR - 1.0, yF - 1.2, yF, 4.1, 5.5)
b.bbox('Bulb', xL + 1.0, xR - 1.0, yF - 1.25, yF - 1.2, 4.2, 4.35)
b.bbox('Bulb', xL + 1.0, xR - 1.0, yF - 1.25, yF - 1.2, 5.3, 5.45)
b.text('Sign_Letters', 'STREATHAM HILL THEATRE', xc, yF - 1.3, 4.5, 0.58, extrude=0.06)
for k in range(5):
    dx = -4.8 + k * 2.4
    b.bbox('Door_Lit', xc + dx - 0.95, xc + dx + 0.95, yF - 0.08, yF, 0.0, 3.2)
    b.bbox('Faience_Shade', xc + dx - 1.05, xc + dx - 0.95, yF - 0.14, yF, 0.0, 3.4)
b.bbox('Door_Lit', xc + 4.8 + 1.15, xc + 4.8 + 1.25, yF - 0.14, yF, 0.0, 3.4)
# ground-floor shop windows on the pavilions
for (x0, x1) in ((xL, XP1), (XP2, xR)):
    for k in range(3):
        wx = x0 + 1.6 + k * ((x1 - x0 - 3.2) / 2)
        b.bbox('Emit_Window_Cool' if rng.random() < 0.5 else 'Door_Lit', wx - 1.0, wx + 1.0, yF - 0.08, yF, 0.4, 3.4)

# blade signs (vertical, lit) on the front corners
for bx in (xL + 0.2, xR - 1.5):
    b.bbox('Sign_Blue', bx, bx + 1.3, yF - 0.9, yF - 0.2, 6.0, 16.4)
    b.bbox('Faience_Shade', bx - 0.06, bx + 1.36, yF - 0.95, yF - 0.88, 6.0, 16.4)
    b.text('Sign_Letters', 'T\nH\nE\nA\nT\nR\nE', bx + 0.65, yF - 0.95, 6.6, 1.0, extrude=0.08, spacing=1.3)

# pantile mansard / hip roofs peeking over the cornice
b.hip('Pantile', xL + 0.8, XP1 - 0.2, yF + 2.5, -8.8, H_FRONT, 2.8, top_frac=0.2)
b.hip('Pantile', XP2 + 0.2, xR - 0.8, yF + 2.5, -8.8, H_FRONT, 2.8, top_frac=0.2)
b.bbox('Pantile', XP1, XP2, -21.0, -9.0, 16.5, 17.2)
b.hip('Pantile', XP1 + 0.4, XP2 - 0.4, -20.5, -9.2, 17.2, 2.6, top_frac=0.2)

# front block upper flanks (y -9..-8) hide nothing; add parapet balustrade on pavilions' roofs? (skipped)

b.finish('theatre', footprint=FOOT['theatre']['footprint_bbox_m'],
         notes='Streatham Hill Theatre (Sprague 1929, Grade II). Cream faience front in 3 sections (two pedimented pavilions + central colonnaded promenade loggia of four Tuscan columns), '
               'blue canopy with lit sign, vertical lit THEATRE blade signs, red pantile roofs, buff brick auditorium (~21 m) and ~30 m fly tower behind.',
         cams={
             'front34': (Vector((-0.75, -1.0, 0.35)), 1.0),
             'front34b': (Vector((0.8, -1.0, 0.3)), 1.0),
             'rear34': (Vector((0.8, 1.0, 0.45)), 1.0),
             'side': (Vector((1.0, -0.1, 0.22)), 1.0),
             'front': (Vector((0.0, -1.0, 0.15)), 1.0, wpt(THETA, -2.7, -24, 8), 24),
             'top': (Vector((0.12, -0.5, 1.4)), 1.0),
         })
