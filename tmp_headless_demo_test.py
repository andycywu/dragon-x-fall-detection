import sys, os, json
sys.path.insert(0, os.path.abspath('.'))
from src.infer_demo_Mac.adapters.pose_adapter import PoseAdapter
import numpy as np

# local copy of compute_torso_angle_from_keypoints extracted from live_demo_mac
def compute_torso_angle_from_keypoints(keypoints: list, frame_shape: tuple, key_mode='average'):
    if keypoints is None:
        return None
    arr = np.array(keypoints, dtype='float32')
    if arr.size == 0:
        return None
    if arr.ndim == 1 or arr.shape[-1] < 2:
        return None
    h, w = frame_shape[0], frame_shape[1]
    if np.max(arr[:, 0]) <= 1.0 and np.max(arr[:, 1]) <= 1.0:
        pts = np.copy(arr)
        pts[:, 0] = pts[:, 0] * w
        pts[:, 1] = pts[:, 1] * h
    else:
        pts = arr
    if pts.shape[0] >= 17:
        try:
            ls = pts[5][:2]
            rs = pts[6][:2]
            lh = pts[11][:2]
            rh = pts[12][:2]
        except Exception:
            ls = pts[0][:2]
            rs = pts[1][:2]
            lh = pts[2][:2]
            rh = pts[3][:2]
    else:
        ys = pts[:, 1]
        top_idx = np.argsort(ys)[:2]
        bot_idx = np.argsort(ys)[-2:]
        ls = pts[top_idx[0]][:2]
        rs = pts[top_idx[1]][:2]
        lh = pts[bot_idx[0]][:2]
        rh = pts[bot_idx[1]][:2]
    if key_mode == 'left':
        shoulder, hip = ls, lh
    elif key_mode == 'right':
        shoulder, hip = rs, rh
    else:
        shoulder = (ls + rs) / 2.0
        hip = (lh + rh) / 2.0
    torso = shoulder - hip
    vert = np.array([0, -1.0])
    cos = np.dot(torso, vert) / (np.linalg.norm(torso) * np.linalg.norm(vert) + 1e-8)
    cos = np.clip(cos, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))
import numpy as np
from PIL import Image

# pick a sample viz image from reports
with open('reports/batch_diagnostic_summary.json','r',encoding='utf-8') as f:
    data = json.load(f)
# find first wrote entry with at least one image
img = None
for ent in data:
    if ent.get('wrote'):
        img = ent['wrote'][0]
        break
if img is None:
    print('No report viz images found')
    sys.exit(1)

print('Using image:', img)
if not os.path.isfile(img):
    print('Image file not found:', img)
    sys.exit(1)

# load image
im = Image.open(img).convert('RGB')
arr = np.array(im)  # RGB image
h, w = arr.shape[0], arr.shape[1]

adapter = PoseAdapter()
# try detect_and_adapt with raw image (should return None usually)
res = None
try:
    res = adapter.detect_and_adapt(None, w, h)
    print('adapter.detect_and_adapt(None) ->', type(res), res is not None)
except Exception as e:
    print('adapter.detect_and_adapt(None) raised:', e)

# load a plausible kps by using one of the viz output files that contain detect_and_adapt name
# try to find a detect_and_adapt variant image for same model entry
cand = None
for ent in data:
    if ent.get('wrote'):
        for p in ent['wrote']:
            if 'detect_and_adapt' in p:
                cand = p
                break
    if cand:
        break
if cand is None:
    cand = img
print('Using detect image candidate:', cand)
# For test simplicity, simulate kps as 17 repeated normalized points
kps = [[0.5, 0.2, 1.0]] * 17
angle = compute_torso_angle_from_keypoints(kps, (h, w))
print('Simulated keypoints angle:', angle)

print('Done')
