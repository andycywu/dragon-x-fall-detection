"""
Batch diagnostic: run all ONNX models under src/models on real example images
(reports/viz_pose1..7.jpg), apply PoseAdapter heuristics and heatmap soft-argmax,
write timestamped visualization outputs into reports/ and a JSON summary.

Usage (from repo root):
    python3 scripts/batch_realimg_diagnostics.py

This script is best-effort and intended for local verification. It avoids network
IO and writes outputs under reports/.
"""
import time, json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, 'src/infer_demo_Mac')
try:
    from adapters.pose_adapter import PoseAdapter
except Exception as e:
    print('Cannot import PoseAdapter:', e)
    raise

REPORTS = Path('reports')
REPORTS.mkdir(exist_ok=True)
MODELS_ROOT = Path('src/models')
# find onnx models recursively
onnx_files = [str(p) for p in MODELS_ROOT.rglob('*.onnx')]
if not onnx_files:
    print('No ONNX models under src/models found. Exiting.')
    sys.exit(0)

vizs = [REPORTS / f'viz_pose{i}.jpg' for i in range(1,8)]
vizs = [p for p in vizs if p.exists()]
if not vizs:
    print('No reports/viz_pose1..7.jpg found. Place representative images and retry.')
    sys.exit(1)

import onnxruntime as ort
ad = PoseAdapter()
# determine providers to try: prefer CoreML on macOS if available, else CPU
AVAILABLE_PROVIDERS = ort.get_available_providers()
PREFERRED_ORDER = []
if 'CoreMLExecutionProvider' in AVAILABLE_PROVIDERS:
    PREFERRED_ORDER.append('CoreMLExecutionProvider')
if 'CPUExecutionProvider' in AVAILABLE_PROVIDERS:
    PREFERRED_ORDER.append('CPUExecutionProvider')
if not PREFERRED_ORDER:
    PREFERRED_ORDER = AVAILABLE_PROVIDERS

def draw_keypoints(bg_path, kps, fname):
    img = Image.open(bg_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    for i,(x,y,c) in enumerate(kps):
        px = int(x*img.width)
        py = int(y*img.height)
        draw.ellipse((px-6,py-6,px+6,py+6), fill=(255,0,0))
        draw.text((px+8,py+8), str(i), fill=(0,0,0))
    img.save(fname)

summary = []
for idx, model_path in enumerate(sorted(onnx_files)):
    # if model_path is a directory (some exported bundles are folders), try inner model.onnx
    if os.path.isdir(model_path):
        inner = os.path.join(model_path, 'model.onnx')
        if os.path.exists(inner):
            model_path = inner
        else:
            print(' skipping directory without model.onnx:', model_path)
            summary.append({'model': model_path, 'wrote': []})
            continue
    print('\n===', model_path)
    wrote = []
    for img_idx, bg in enumerate(vizs[:3]):
        img = Image.open(bg).convert('RGB')
        try:
            # try preferred providers in order
            sess = None
            last_err = None
            for prov in PREFERRED_ORDER:
                try:
                    sess = ort.InferenceSession(model_path, providers=[prov])
                    break
                except Exception as e:
                    last_err = e
                    continue
            if sess is None:
                # final attempt with default provider list
                sess = ort.InferenceSession(model_path)
            inp = sess.get_inputs()
            if not inp:
                print(' model has no inputs listed; skipping input-run')
                continue
            inp0 = inp[0]
            # prepare input by resizing to model expected dims when known
            shape = [s if (isinstance(s, int) and s>0) else None for s in list(inp0.shape)]
            # build array from image using heuristics similar to demo
            if len(shape) == 4:
                # NCHW or NHWC heuristics
                if shape[1] in (1,3):
                    C = shape[1]
                    H = shape[2] or img.height
                    W = shape[3] or img.width
                    im = img.resize((W,H))
                    arr = np.array(im).astype(np.float32)/255.0
                    if C == 3:
                        arr = arr.transpose(2,0,1)
                    else:
                        arr = arr[np.newaxis,:,:]
                    arr = arr.reshape((1, C, H, W)).astype(np.float32)
                else:
                    # assume NHWC
                    H = shape[1] or img.height
                    W = shape[2] or img.width
                    im = img.resize((W,H))
                    arr = np.array(im).astype(np.float32)/255.0
                    arr = arr.reshape((1, H, W, arr.shape[2])).astype(np.float32)
            else:
                # fallback: flatten
                arr = np.array(img.resize((64,64)).convert('RGB')).astype(np.float32).ravel()/255.0
                arr = arr.reshape((1, arr.size)).astype(np.float32)
            res = sess.run(None, {inp0.name: arr})
            out_names = [o.name for o in sess.get_outputs()]
            outd = {n: v for n, v in zip(out_names, res)}
            ts = int(time.time())
            # try adapter named with litehrnet and generic
            try:
                k1 = ad.adapt_named_onnx_outputs('litehrnet', outd, img_w=img.width, img_h=img.height)
                if k1 is not None:
                    fname = REPORTS / f'viz_{Path(model_path).stem}_adapter_named_litehrnet_{ts}_{img_idx}.jpg'
                    draw_keypoints(bg, np.array(k1), fname)
                    wrote.append(str(fname))
            except Exception:
                pass
            try:
                k2 = ad.detect_and_adapt(list(outd.values()), img_w=img.width, img_h=img.height)
                if k2 is not None:
                    fname = REPORTS / f'viz_{Path(model_path).stem}_detect_and_adapt_{ts}_{img_idx}.jpg'
                    draw_keypoints(bg, np.array(k2), fname)
                    wrote.append(str(fname))
            except Exception:
                pass
            # inspect for heatmap-like tensors and use soft-argmax
            for name, arr in outd.items():
                a = np.array(arr)
                if a.ndim == 4:
                    # try channel-first
                    if a.shape[0] == 1 and a.shape[1] >= 8 and a.shape[2] <= 256 and a.shape[3] <= 256:
                        C = a.shape[1]
                        kps = []
                        for c in range(min(C, 64)):
                            hm = a[0,c,:,:]
                            x,y,conf = ad._soft_argmax_2d(hm)
                            kps.append([x,y,conf])
                        kps = np.array(kps)
                        fname = REPORTS / f'viz_{Path(model_path).stem}_{name}_softargmax_{ts}_{img_idx}.jpg'
                        draw_keypoints(bg, kps[:17], fname)
                        wrote.append(str(fname))
                # flattened arrays heuristics
                a1 = a.squeeze()
                if a1.ndim == 1:
                    if a1.size % 3 == 0 and a1.size // 3 >= 17:
                        pts = a1.reshape((-1,3))
                        fname = REPORTS / f'viz_{Path(model_path).stem}_{name}_flat3_{ts}_{img_idx}.jpg'
                        draw_keypoints(bg, pts[:17], fname)
                        wrote.append(str(fname))
                    if a1.size % 2 == 0 and a1.size // 2 >= 17:
                        pts = a1.reshape((-1,2))
                        pts3 = np.concatenate([pts, np.ones((pts.shape[0],1))], axis=1)
                        fname = REPORTS / f'viz_{Path(model_path).stem}_{name}_flat2_{ts}_{img_idx}.jpg'
                        draw_keypoints(bg, pts3[:17], fname)
                        wrote.append(str(fname))
        except Exception as e:
            print(' model run error:', e)
            continue
    summary.append({'model': model_path, 'wrote': wrote})
# write summary
with open(REPORTS / 'batch_diagnostic_summary.json','w') as f:
    json.dump(summary,f,indent=2)
print('\nBatch diagnostic complete. Summary written to reports/batch_diagnostic_summary.json')
