"""Smoke-test: run fall inference on images in src/test_data/img

This script prefers ONNX models from deploy/qaihub_optimized (same logic as demo).
It processes images, computes angle/conf/risk/fall, records per-image results to CSV
and records alerts when FusionTrigger decides to trigger an alert.

Run inside demo venv:
  src/infer_demo_Mac/.venv_mac/bin/python3 src/infer_demo_Mac/smoke_test_images.py --max 200
"""

import os
import sys
import time
import argparse
import csv
from pathlib import Path

# ensure imports find demo modules
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from live_demo_mac import find_onnx_models, ONNXRunner, interpret_onnx_output, compute_torso_angle_from_keypoints, compute_torso_angle_from_results, compute_confidence_from_results
from detectors.fall_detector import FallDetector
from detectors.fusion_trigger import FusionTrigger

import cv2
import numpy as np


def process_images(img_dir: Path, out_dir: Path, max_images: int = 200):
    out_dir.mkdir(parents=True, exist_ok=True)
    results_csv = out_dir / 'smoke_test_results.csv'
    alerts_csv = out_dir / 'alerts_sent.csv'

    models, models_base = find_onnx_models()
    onnx_runner = None
    if models:
        # pick first model that looks loadable
        for m in models:
            try:
                # quick size check
                if os.path.isfile(m) and os.path.getsize(m) > 0:
                    onnx_runner = ONNXRunner(m)
                    try:
                        onnx_runner._create_session()
                        print(f"Loaded ONNX runner: {m} (provider={onnx_runner.provider_used})")
                        break
                    except Exception as e:
                        print(f"ONNX session creation failed for {m}: {e}")
                        onnx_runner = None
            except Exception:
                continue

    fd = FallDetector()
    fusion = FusionTrigger(cooldown_seconds=5.0)

    img_paths = sorted([p for p in img_dir.glob('**/*') if p.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    if not img_paths:
        print('No images found in', img_dir)
        return

    if max_images and max_images > 0:
        img_paths = img_paths[:max_images]

    angles_window = []
    sway_window = 8
    sway_scale = 8.0

    # open CSV writers
    with open(results_csv, 'w', newline='') as rf, open(alerts_csv, 'w', newline='') as af:
        rwriter = csv.writer(rf)
        awriter = csv.writer(af)
        rwriter.writerow(['filename', 'engine', 'angle', 'confidence', 'risk_score', 'fall'])
        awriter.writerow(['ts', 'filename', 'score', 'engine'])

        for i, p in enumerate(img_paths, 1):
            try:
                img = cv2.imread(str(p))
                if img is None:
                    print('skipping unreadable', p)
                    continue
                h, w = img.shape[0], img.shape[1]
                engine = 'MediaPipe'
                angle = None
                conf = 0.0
                risk_score = 0.0
                fall = False

                onnx_used = False
                if onnx_runner is not None:
                    try:
                        onnx_out = onnx_runner.run(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                        onnx_used = True
                        parsed = interpret_onnx_output(onnx_out)
                        prob = parsed.get('prob') if parsed.get('prob') is not None else None
                        if parsed.get('keypoints') is not None:
                            kps = parsed.get('keypoints')
                            angle = compute_torso_angle_from_keypoints(kps, img.shape)
                            try:
                                confs = [float(p[2]) for p in kps if len(p) >= 3]
                                conf = float(np.clip(np.mean(confs), 0.0, 1.0)) if confs else 1.0
                            except Exception:
                                conf = 1.0
                            risk_score = float(prob) if prob is not None else ((float(angle) / 180.0) * conf if angle is not None else 0.0)
                            fall = (float(prob) >= 0.5) if prob is not None else ((float(angle) > 80) if angle is not None else False)
                        elif prob is not None:
                            # fallback: use mediapipe to compute angle
                            res = fd.pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                            angle = compute_torso_angle_from_results(res, img.shape)
                            conf = float(prob)
                            risk_score = float(prob)
                            fall = (prob >= 0.5)
                        else:
                            res = fd.pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                            angle = compute_torso_angle_from_results(res, img.shape)
                            conf = compute_confidence_from_results(res)
                            risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                            fall = (float(angle) > 80 and conf >= 0.5) if angle is not None else False
                        engine = 'ONNX'
                    except Exception as e:
                        onnx_used = False
                        print(f'ONNX runtime error for {p.name}:', e)

                if not onnx_used:
                    res = fd.pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                    angle = compute_torso_angle_from_results(res, img.shape)
                    conf = compute_confidence_from_results(res)
                    risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                    fall = (float(angle) > 80 and conf >= 0.5) if angle is not None else False
                    engine = 'MediaPipe'

                # sway history
                try:
                    if angle is not None:
                        angles_window.append(float(angle))
                        window = angles_window[-sway_window:]
                        if len(window) <= 1:
                            sway_score = 0.0
                        else:
                            sway_score = float(np.clip(np.std(np.array(window)) / sway_scale, 0.0, 1.0))
                    else:
                        sway_score = 0.0
                except Exception:
                    sway_score = 0.0

                # record result
                rwriter.writerow([p.name, engine, angle if angle is not None else '', conf, risk_score, bool(fall)])

                # check fusion alert
                if fusion.should_trigger_alert(fall_detected=bool(fall), help_detected=False):
                    ts = time.time()
                    awriter.writerow([ts, p.name, risk_score, engine])
                    print(f'ALERT at {p.name} score={risk_score} engine={engine}')

                if i % 50 == 0:
                    print(f'Processed {i}/{len(img_paths)}')

            except Exception as e:
                print('Error processing', p, e)

    print('Done. Results:', results_csv, 'Alerts:', alerts_csv)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--img-dir', default=os.path.join(str(HERE.parent), 'test_data', 'img'))
    ap.add_argument('--out-dir', default=os.path.join(str(HERE), 'smoke_test_output'))
    ap.add_argument('--max', type=int, default=200)
    args = ap.parse_args()
    process_images(Path(args.img_dir), Path(args.out_dir), max_images=args.max)
