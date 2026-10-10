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
car.finalize()
print('tris', car.tri_count())
path = car.export()
car.verify_and_render(path)
