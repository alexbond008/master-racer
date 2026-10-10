"""Met Police Vauxhall Astra (mk4/mk5) 5-door hatch response car -> public/models/cars/cruiser.glb
Run: blender -b --python police_cruiser.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, police_common as pc
importlib.reload(pc)
from police_common import *

spec = dict(
    name='cruiser', L=4.25, W=1.70, wb=2.61, fo=0.88, r=0.30, rim_r=0.19, tyre_w=0.20, spokes=5,
    hw=0.78, tumble=0.03, inset=0.09, lean=0.19, crown=0.02,
    plan_rf=0.42, plan_rr=0.38, plan_minf=0.66, plan_minr=0.70,
    stations=[0.0, 0.03, 0.08, 0.16, 0.28, 0.45, 0.7, 1.0, 1.3, 1.55, 1.75, 1.95, 2.15, 2.35, 2.6, 2.9, 3.2, 3.4, 3.6, 3.8, 3.95, 4.05, 4.13, 4.19, 4.23, 4.25],
    ztop=[(0, 0.60), (0.05, 0.69), (0.2, 0.76), (0.5, 0.82), (0.9, 0.875), (1.3, 0.925), (1.55, 0.965), (1.95, 1.19),
          (2.35, 1.335), (2.8, 1.35), (3.3, 1.345), (3.7, 1.19), (4.02, 1.03), (4.15, 0.99), (4.22, 0.93), (4.25, 0.80)],
    zs=[(0, 0.50), (0.05, 0.60), (0.2, 0.67), (0.5, 0.73), (0.9, 0.785), (1.3, 0.835), (1.55, 0.875), (1.8, 0.93), (2.2, 0.96),
        (3.3, 0.985), (3.8, 0.995), (4.05, 0.975), (4.2, 0.93), (4.25, 0.80)],
    zb=[(0, 0.36), (0.03, 0.31), (0.08, 0.27), (0.2, 0.235), (0.6, 0.205), (1.2, 0.19), (3.3, 0.19), (3.8, 0.23), (4.1, 0.28),
        (4.25, 0.36)],
)

car = Car(spec)
body = car.build_loft()
car.arch_cut(body)
car.build_wheels()

# ---- details ----------------------------------------------------------------
car.refresh_surface(('body',))
car.add_glass(
    side_windows=[
        [(1.88, 1.0), (2.28, 1.28), (2.70, 1.29), (2.72, 1.0)],               # front door
        [(2.84, 1.0), (2.84, 1.29), (3.26, 1.285), (3.56, 1.10), (3.56, 1.0)],  # rear door + quarter
    ],
    windscreen=[(-0.63, 1.66), (0.63, 1.66), (0.565, 2.27), (-0.565, 2.27)],
    rear_window=[(-0.50, 3.38), (0.50, 3.38), (0.56, 4.0), (-0.56, 4.0)],
)
car.refresh_surface(('body', 'glass'))
F = car.front_mapper(); Rr = car.rear_mapper(); T = car.top_mapper()
FD, RD, TD = (0, 1, 0), (0, -1, 0), (0, 0, -1)

# battenburg flank band between the wheel arches + front/rear
car.side_band(0.88 + 0.40, 0.88 + 2.61 - 0.40, 0.44, 0.14, rows=2, tilelen=0.235)
car.back_band(0.66, 0.40, 0.12, rows=2, tilelen=0.22)             # rear
# doors
for yy in (1.72, 2.78):
    car.door_line(yy, 0.27, 0.97)
car.door_line(3.50, 0.72, 0.97)
car.side_sill(0.88 + 0.40, 0.88 + 2.61 - 0.40, 0.215, 0.285)
car.handle(2.58, 0.90); car.handle(3.38, 0.90)
car.mirror(1.93, 0.785, 0.95)

# front: lights, grille, intake, plate
hl = [(0.27, 0.575), (0.45, 0.56), (0.62, 0.585), (0.735, 0.625), (0.74, 0.69), (0.66, 0.735), (0.52, 0.745), (0.38, 0.715)]
for pts in (hl, mirror_x(hl)):
    car.surround(chaikin(pts, 1), F, FD, 1.14)
    car.patch('lights', 'HeadLight', chaikin(pts, 1), F, FD, offset=0.005, maxlen=0.03)
car.patch('trim', 'Trim', rrect(-0.24, 0.24, 0.56, 0.685), F, FD, offset=0.004)
car.patch('chrome', 'Chrome', rect(-0.24, 0.24, 0.62, 0.628), F, FD, offset=0.006)
car.patch('chrome', 'Chrome', rrect(-0.035, 0.035, 0.585, 0.65, 1), F, FD, offset=0.007)   # badge
for x0, x1 in ((0.30, 0.64), (-0.64, -0.30)):
    car.patch('trim', 'Trim', rrect(x0, x1, 0.375, 0.485), F, FD, offset=0.004)
car.patch('trim', 'Trim', rect(-0.30, 0.30, 0.40, 0.50), F, FD, offset=0.004)
car.patch('plates', 'Plate', rrect(-0.255, 0.255, 0.395, 0.505, 1), F, FD, offset=0.009)
for x in (0.13, -0.13):
    car.patch('strobes', 'Light_Blue', rect(x - 0.07, x + 0.07, 0.585, 0.612), F, FD, offset=0.009)
for x in (0.62, -0.62):
    car.patch('lights', 'HeadLight', rrect(x - 0.045, x + 0.045, 0.415, 0.465, 1), F, FD, offset=0.005)

# rear: tail lights, plate, bumper strip
tl = [(0.42, 0.64), (0.70, 0.64), (0.765, 0.70), (0.765, 0.90), (0.70, 0.93), (0.44, 0.88)]
for pts in (tl, mirror_x(tl)):
    car.surround(chaikin(pts, 1), Rr, RD, 1.12)
    car.patch('lights', 'TailLight', chaikin(pts, 1), Rr, RD, offset=0.005, maxlen=0.03)
car.patch('plates', 'Plate', rrect(-0.255, 0.255, 0.44, 0.55, 1), Rr, RD, offset=0.009)
car.patch('trim', 'Trim', rect(-0.72, 0.72, 0.335, 0.375), Rr, RD, offset=0.004)
car.patch('trim', 'Trim', rrect(-0.1, 0.1, 0.80, 0.82, 1), Rr, RD, offset=0.004)
for x in (0.42, -0.42):
    car.patch('strobes', 'Light_Blue', rect(x - 0.09, x + 0.09, 3.39, 3.44), T, TD, offset=0.009)

# POLICE text: bonnet (mirror reading), rear, flanks
car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.62, T, TD, lambda lx, ly: (lx, 0.80 + ly), mirror=True)
car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.62, Rr, RD, lambda lx, ly: (-lx, 0.745 + ly))
for sx in (1, -1):
    car.text('livery_blue', 'Livery_Blue', 'POLICE', 0.70, car.side_mapper(sx), (-sx, 0, 0),
             (lambda lx, ly, sx=sx: (2.55 + sx * lx, 0.85 + ly)))

# roof light bar
car.lightbar(2.80, 1.12, 0.28)

car.finalize()
print('tris', car.tri_count())
path = car.export()
car.verify_and_render(path)
