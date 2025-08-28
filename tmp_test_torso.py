import re, sys, numpy as np
from typing import Tuple, Optional, List

p = 'src/infer_demo_Mac/live_demo_mac.py'
s = open(p, 'r', encoding='utf-8').read()
# extract function by regex from def line to next def at column 0 or EOF
m = re.search(r"^def compute_torso_angle_from_keypoints\([\s\S]*?\n(?=^def |\Z)", s, flags=re.M)
if not m:
    print('function not found')
    sys.exit(1)
func_src = m.group(0)
# provide numpy and typing symbols expected by the extracted function
ns = {'np': np, 'Tuple': Tuple, 'Optional': Optional, 'List': List}
exec(func_src, ns)
fn = ns.get('compute_torso_angle_from_keypoints')
print('fn loaded:', callable(fn))
# run tests
print('None ->', fn(None, (480, 640)))
print('empty ->', fn([], (480, 640)))
print('1D ->', fn([1, 2, 3], (480, 640)))
kps = [[0.5, 0.2, 1.0]] * 17
print('valid ->', fn(kps, (480, 640)))
# test pixel coords
pts = [[100, 120, 0.9]] * 17
print('pixel ->', fn(pts, (480, 640)))
# non-17 but valid array
pts2 = [[0.4, 0.3, 0.8]] * 10
print('10kp ->', fn(pts2, (480, 640)))
