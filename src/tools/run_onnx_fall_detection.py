#!/usr/bin/env python3
"""
Run ONNX inference over test data and produce a fall-detection report.

Behaviour summary:
- Loads ONNX models from src/models/onnx via PracticalQAIHubONNX
- Loads local MediaPipe-based FallDetector (src/fall_detector.py) to decide fall/no-fall
- Iterates images and videos under a test directory and records per-file results
- Produces JSON report and a minimal HTML summary

Assumptions / notes:
- If you want to use a different ONNX directory, pass --model_dir relative to repo root (default: models/onnx)
- If you want to rely solely on ONNX pose outputs to decide falls, we need a model-specific postprocess mapping. This script uses MediaPipe FallDetector as the final decision and includes ONNX outputs for comparison/benchmarking.
"""
import argparse
import json
import os
import time
from pathlib import Path
from typing import List, Any, Optional

import cv2
import numpy as np

import sys
from pathlib import Path as _Path

# Ensure repo src/ is on sys.path so local package imports work when running the script directly
_THIS_FILE = _Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[2]
_SRC_DIR = str(_REPO_ROOT / 'src')
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# import project classes (use absolute imports relative to repo src in PYTHONPATH)
from qaihub_optimize.practical_qai_hub_onnx import PracticalQAIHubONNX
try:
    from fall_detector import FallDetector
except Exception:
    FallDetector = None


def find_test_files(test_dir: Path) -> List[Path]:
    exts_img = {'.jpg', '.jpeg', '.png', '.bmp'}
    exts_vid = {'.mp4', '.avi', '.mov', '.mkv'}
    files = []
    if not test_dir.exists():
        return files
    for p in sorted(test_dir.rglob('*')):
        if p.is_file() and p.suffix.lower() in exts_img.union(exts_vid):
            files.append(p)
    return files


def process_image_file(path: Path, system: PracticalQAIHubONNX, fall_detector: Optional[Any], per_model_specs: dict = None, ensemble_votes: int = 2):
    image = cv2.imread(str(path))
    if image is None:
        return {'path': str(path), 'error': 'cannot_load'}

    entry = {'path': str(path), 'type': 'image', 'timestamp': time.time(), 'onnx': {}, 'fall': {}}

    # Run ONNX models (if any) and attempt ONNX-based fall detection
    for model_name, session_info in system.onnx_sessions.items():
        t0 = time.time()
        try:
            session = session_info['session']
            config = session_info.get('config', {'input_size': (224, 224)})
            input_name = session.get_inputs()[0].name
            # prefer per-model spec if available
            spec = (per_model_specs or {}).get(model_name)
            pre = preprocess_for_session(session, image, fallback_size=config['input_size'], per_model_spec=spec)
            raw_outputs = session.run(None, {input_name: pre})
            dt = (time.time() - t0) * 1000

            # Store raw ONNX inference summary
            entry['onnx'][model_name] = {'time_ms': round(dt, 2), 'raw_output_shapes': [o.shape for o in raw_outputs]}

            # Try to parse landmarks from raw outputs and detect fall using ONNX outputs
            onnx_fall = detect_fall_from_onnx(raw_outputs, image.shape)
            entry['onnx'][model_name]['onnx_fall'] = onnx_fall

            # Note: skip calling system.detect_with_onnx here to avoid wrapper's internal
            # preprocessing which may mismatch our per-model preprocessing.

        except Exception as e:
            entry['onnx'][model_name] = {'error': str(e)}

    # Run MediaPipe-based fall detector for comparison (optional)
    try:
        fall, angle = fall_detector.detect_fall_from_frame(image)
        entry['fall'] = {'detected_mediapipe': bool(fall), 'angle_mediapipe': float(angle) if angle is not None else None}
    except Exception as e:
        entry['fall'] = {'error_mediapipe': str(e)}

    # ensemble across ONNX models
    try:
        entry['ensemble'] = ensemble_on_entry(entry.get('onnx', {}), min_group_votes=ensemble_votes)
    except Exception:
        entry['ensemble'] = {'error': 'ensemble_failed'}

    return entry



def process_video_file(path: Path, system: PracticalQAIHubONNX, fall_detector: Optional[Any], frame_stride: int = 30, per_model_specs: dict = None, ensemble_votes: int = 2):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {'path': str(path), 'error': 'cannot_open_video'}

    results = []
    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_stride == 0:
                entry = {'path': str(path), 'type': 'video_frame', 'frame_idx': frame_idx, 'timestamp': time.time(), 'onnx': {}, 'fall': {}}
                for model_name, session_info in system.onnx_sessions.items():
                    t0 = time.time()
                    try:
                        session = session_info.get('session')
                        config = session_info.get('config', {'input_size': (224, 224)})
                        # use per-session preprocessing to match expected input shape/order
                        input_name = session.get_inputs()[0].name
                        spec = (per_model_specs or {}).get(model_name)
                        pre = preprocess_for_session(session, frame, fallback_size=config.get('input_size', (224, 224)), per_model_spec=spec)
                        raw = session.run(None, {input_name: pre})
                        dt = (time.time() - t0) * 1000
                        entry['onnx'][model_name] = {'time_ms': round(dt, 2), 'raw_output_shapes': [o.shape for o in raw]}
                        # Note: skip calling system.detect_with_onnx here to avoid wrapper's internal
                        # preprocessing which may mismatch our per-model preprocessing.
                    except Exception as e:
                        entry['onnx'][model_name] = {'error': str(e)}

                try:
                    fall, angle = fall_detector.detect_fall_from_frame(frame)
                    entry['fall'] = {'detected': bool(fall), 'angle': float(angle) if angle is not None else None}
                except Exception as e:
                    entry['fall'] = {'error_mediapipe': str(e)}

                try:
                    entry['ensemble'] = ensemble_on_entry(entry.get('onnx', {}), min_group_votes=ensemble_votes)
                except Exception:
                    entry['ensemble'] = {'error': 'ensemble_failed'}

                results.append(entry)
            frame_idx += 1
    finally:
        cap.release()

    return results


def preprocess_for_session(session, image: Any, fallback_size=(224, 224), per_model_spec: dict = None):
    """
    Heuristic per-session preprocessing: read session input shape and produce a numpy array
    matching (batch,channels,height,width) or (batch,height,width,channels) depending on model.

    - If the session input shape is (N, C, H, W) or (N, H, W, C) we resize accordingly.
    - If any dimension is None or <=0, fallback to fallback_size for spatial dims and 3 channels.
    - Convert BGR->RGB and normalize to float32 [0,1].
    Returns an ndarray suitable for passing directly to session.run.
    """
    # default: use PracticalQAIHubONNX style (N, C, H, W)
    try:
        inputs = session.get_inputs()
        if not inputs:
            raise RuntimeError('session has no inputs')
        inp = inputs[0]
        shape = getattr(inp, 'shape', None)
    except Exception:
        shape = None

    h_img, w_img = image.shape[0], image.shape[1]
    # resolve spatial dims and channel ordering
    # default target H,W
    target_h, target_w = fallback_size[1], fallback_size[0]
    channels = 3
    is_nhwc = False

    # if a per-model spec provided, prefer it
    if per_model_spec and isinstance(per_model_spec, dict):
        try:
            if 'target_h' in per_model_spec and 'target_w' in per_model_spec:
                target_h = int(per_model_spec['target_h'])
                target_w = int(per_model_spec['target_w'])
            if 'channels' in per_model_spec:
                channels = int(per_model_spec['channels'])
            if 'is_nhwc' in per_model_spec:
                is_nhwc = bool(per_model_spec['is_nhwc'])
        except Exception:
            pass

    if shape and isinstance(shape, (list, tuple)) and len(shape) >= 4:
        # try to interpret (N, C, H, W) or (N, H, W, C)
        s = [int(x) if isinstance(x, (int, float)) and x > 0 else None for x in shape]
        # common detection: if second dim is 1 or 3 -> NCHW
        if s[1] in (1, 3):
            channels = s[1] or 3
            if s[2] and s[3]:
                target_h, target_w = int(s[2]), int(s[3])
        else:
            # if last dim is 1 or 3 -> NHWC
            if s[-1] in (1, 3):
                is_nhwc = True
                channels = s[-1] or 3
                if s[1] and s[2]:
                    target_h, target_w = int(s[1]), int(s[2])

    # fallback if unresolved
    if target_h is None or target_w is None:
        target_h, target_w = fallback_size[1], fallback_size[0]

    # resize image to target (width,height) for cv2
    resized = cv2.resize(image, (target_w, target_h))

    # convert BGR->RGB if channels==3
    if channels == 3 and len(resized.shape) == 3:
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    arr = resized.astype('float32') / 255.0

    if is_nhwc:
        # add batch dim -> (1,H,W,C)
        arr = np.expand_dims(arr, axis=0)
    else:
        # convert HWC -> CHW
        if arr.ndim == 3:
            arr = np.transpose(arr, (2, 0, 1))
        arr = np.expand_dims(arr, axis=0)

    return arr



def build_input_spec_from_verbose_entry(ins: list):
    """Given a verbose 'inputs' list for a model, return a dict with keys:
    target_h, target_w, channels, is_nhwc
    """
    # default
    spec = {'target_h': fallback_dim(fallback_size=(224,224))[1], 'target_w': fallback_dim(fallback_size=(224,224))[0], 'channels': 3, 'is_nhwc': False}
    try:
        if not ins:
            return spec
        inp = ins[0]
        shape = inp.get('shape') if isinstance(inp, dict) else None
        if not shape:
            return spec
        # shape may be list like [1,3,224,224] or ['batch',3,256,256]
        s = [int(x) if isinstance(x, (int, float)) and x > 0 else None for x in shape]
        # common: (N,C,H,W)
        if len(s) >= 4:
            if s[1] in (1, 3):
                spec['channels'] = s[1] or 3
                if s[2] and s[3]:
                    spec['target_h'], spec['target_w'] = int(s[2]), int(s[3])
                spec['is_nhwc'] = False
            elif s[-1] in (1, 3):
                spec['channels'] = s[-1] or 3
                if s[1] and s[2]:
                    spec['target_h'], spec['target_w'] = int(s[1]), int(s[2])
                spec['is_nhwc'] = True
    except Exception:
        pass
    return spec


def fallback_dim(fallback_size=(224, 224)):
    # helper to return fallback size as (w,h)
    return fallback_size



def _extract_landmarks_from_outputs(outputs, image_shape):
    """
    嘗試從常見 ONNX pose 模型輸出抽出 (x,y) landmarks。
    支援常見格式：
    - 直接輸出 landmark tensor shape (1, N, 3) 或 (N, 3)
    - heatmap + offsets (heuristic)
    返回: list of (x, y) 或空 list
    """
    h_img, w_img = image_shape[0], image_shape[1]
    # case 1: outputs contain a tensor with shape (1, N, 3) or (N, 3)
    for out in outputs:
        try:
            arr = np.array(out)
        except Exception:
            continue
        # case 1b: flattened landmark vector e.g. (1, N*3) or (N*3,)
        if arr.ndim == 2 and arr.shape[0] == 1 and arr.shape[1] > 3:
            flat = arr[0]
            if flat.size % 2 == 0 or flat.size % 3 == 0:
                # prefer interpreting as (N,3) where possible
                n = flat.size // 3
                try:
                    lm = flat.reshape(n, 3)
                    pts = [(float(x) * w_img, float(y) * h_img) for x, y in lm[:, :2]]
                    return pts
                except Exception:
                    pass
        if arr.ndim == 1 and arr.size > 3:
            flat = arr
            if flat.size % 3 == 0:
                n = flat.size // 3
                try:
                    lm = flat.reshape(n, 3)
                    pts = [(float(x) * w_img, float(y) * h_img) for x, y in lm[:, :2]]
                    return pts
                except Exception:
                    pass
        if arr.ndim == 3 and arr.shape[0] == 1 and arr.shape[2] >= 2:
            # assume (1, N, 2/3)
            lm = arr[0][:, :2]
            points = [(float(x) * w_img, float(y) * h_img) for x, y in lm]
            return points
        if arr.ndim == 2 and arr.shape[1] >= 2:
            # assume (N, 2/3)
            lm = arr[:, :2]
            points = [(float(x) * w_img, float(y) * h_img) for x, y in lm]
            return points

    # case 2: heatmap-like outputs (heuristic)
    # find largest 3D tensor with spatial dims
    heatmaps = None
    for out in outputs:
        arr = np.array(out)
        if arr.ndim == 4:
            # (1, C, H, W) or (B, C, H, W)
            heatmaps = arr
            break

    if heatmaps is not None:
        # take argmax per channel
        if heatmaps.shape[0] > 1:
            heatmaps = heatmaps[0]
        else:
            heatmaps = heatmaps[0]
        C, H, W = heatmaps.shape
        pts = []
        for c in range(C):
            ch = heatmaps[c]
            idx = np.unravel_index(np.argmax(ch), ch.shape)
            y, x = idx
            # normalize
            nx = x / float(W)
            ny = y / float(H)
            pts.append((nx * w_img, ny * h_img))
        return pts

    return []


def detect_fall_from_onnx(raw_outputs, image_shape):
    """
    使用簡化規則基於 ONNX pose landmarks 判定是否跌倒。
    規則：若肩膀-臀部的軀幹向量與垂直方向偏離角度超過閾值則判為跌倒。
    輸入：raw_outputs(list of numpy arrays), image_shape (h,w,c)
    回傳字典：{'detected':bool, 'angle':float, 'used_landmarks': int}
    """
    pts = _extract_landmarks_from_outputs(raw_outputs, image_shape)
    if not pts or len(pts) < 3:
        return {'detected': False, 'angle': None, 'used_landmarks': len(pts)}

    # Attempt to map common indices: use landmarks 11 (left_shoulder), 12 (right_shoulder), 23 (left_hip), 24 (right_hip)
    # If indexes exceed length, fallback to approximate center points
    def _get(idx):
        if idx < len(pts):
            return np.array(pts[idx])
        return None

    left_sh = _get(11)
    right_sh = _get(12)
    left_hip = _get(23)
    right_hip = _get(24)

    # compute torso midpoints
    shoulders = None
    hips = None
    if left_sh is not None and right_sh is not None:
        shoulders = (left_sh + right_sh) / 2.0
    elif left_sh is not None:
        shoulders = left_sh
    elif right_sh is not None:
        shoulders = right_sh

    if left_hip is not None and right_hip is not None:
        hips = (left_hip + right_hip) / 2.0
    elif left_hip is not None:
        hips = left_hip
    elif right_hip is not None:
        hips = right_hip

    if shoulders is None or hips is None:
        return {'detected': False, 'angle': None, 'used_landmarks': len(pts)}

    # torso vector from shoulders to hips
    vec = hips - shoulders
    # vertical vector pointing down
    vvert = np.array([0.0, 1.0])

    # compute angle between vec and vertical
    def angle_between(a, b):
        a = a.astype(np.float64)
        b = b.astype(np.float64)
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return None
        cosine = np.dot(a, b) / (na * nb)
        cosine = np.clip(cosine, -1.0, 1.0)
        ang = np.degrees(np.arccos(cosine))
        return ang

    ang = angle_between(vec, vvert)
    if ang is None:
        return {'detected': False, 'angle': None, 'used_landmarks': len(pts)}

    # Heuristic: if torso deviates more than 45 degrees from vertical -> fallen
    fallen = ang > 45

    return {'detected': bool(fallen), 'angle': float(ang), 'used_landmarks': len(pts)}


def _model_type_from_name(name: str):
    n = name.lower()
    if 'landmark' in n or 'landmarks' in n:
        return 'pose_landmarks'
    if 'pose' in n and 'landmark' not in n and 'posedetector' in n:
        return 'pose_detector'
    if 'face' in n or 'facedetector' in n:
        return 'face'
    if 'hand' in n or 'handdetector' in n:
        return 'hand'
    if 'detection' in n or 'detector' in n:
        return 'detection'
    return 'other'


def ensemble_on_entry(onnx_results: dict, min_group_votes: int = 2):
    """
    Simple ensemble across ONNX model groups.
    - Group models by simple name heuristics (pose_landmarks/pose_detector/face/hand/detection).
    - Count how many groups have at least one model voting 'detected'.
    - If number of groups with detection >= min_group_votes -> ensemble detected.
    Returns dict: {'detected':bool, 'groups_voted':int, 'group_details':{group:count}, 'best_model':name, 'best_angle':angle}
    """
    group_counts = {}
    best_angle = None
    best_model = None
    for mname, r in (onnx_results or {}).items():
        of = r.get('onnx_fall') if isinstance(r, dict) else None
        if not of:
            continue
        detected = of.get('detected')
        angle = of.get('angle')
        mtype = _model_type_from_name(mname)
        if detected:
            group_counts[mtype] = group_counts.get(mtype, 0) + 1
        if angle is not None:
            if best_angle is None or abs(angle) > abs(best_angle):
                best_angle = angle
                best_model = mname

    groups_voted = sum(1 for v in group_counts.values() if v > 0)
    ensemble_detected = groups_voted >= min_group_votes
    return {'detected': bool(ensemble_detected), 'groups_voted': groups_voted, 'group_details': group_counts, 'best_model': best_model, 'best_angle': best_angle}


def write_reports(json_path: Path, html_path: Path, entries: List[dict]):
    json_path.write_text(json.dumps(entries, indent=2, default=str))

    # Simple HTML summary
    total = len(entries)
    falls = sum(1 for e in entries if (e.get('fall') and e['fall'].get('detected')))
    with open(html_path, 'w') as f:
        f.write('<html><head><meta charset="utf-8"><title>ONNX Fall Detection Report</title></head><body>')
        f.write(f'<h1>ONNX Fall Detection Report</h1>')
        f.write(f'<p>Total samples (files/frames): <b>{total}</b></p>')
        f.write(f'<p>Fall detections by MediaPipe FallDetector: <b>{falls}</b></p>')
        f.write('<h2>Samples</h2><table border="1" cellpadding="4"><tr><th>path</th><th>type</th><th>fall</th><th>angle</th><th>onnx_models</th></tr>')
        for e in entries:
            path = e.get('path')
            typ = e.get('type')
            fall = e.get('fall', {}).get('detected')
            angle = e.get('fall', {}).get('angle')
            onnx_summary = ''
            if 'onnx' in e:
                parts = []
                for m, r in e['onnx'].items():
                    if 'time_ms' in r:
                        parts.append(f"{m}:{r['time_ms']}ms")
                    elif 'error' in r:
                        parts.append(f"{m}:ERR")
                onnx_summary = ', '.join(parts)
            f.write(f'<tr><td>{path}</td><td>{typ}</td><td>{fall}</td><td>{angle}</td><td>{onnx_summary}</td></tr>')
        f.write('</table></body></html>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dir', type=str, default='test_data', help='Test data directory (images/videos)')
    parser.add_argument('--model_dir', type=str, default='models/onnx', help='Relative models directory (default: models/onnx)')
    parser.add_argument('--frame_stride', type=int, default=30, help='Frame stride when scanning videos')
    parser.add_argument('--out_json', type=str, default='onnx_fall_report.json')
    parser.add_argument('--out_html', type=str, default='onnx_fall_report.html')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging for ONNX session outputs')
    parser.add_argument('--quick_n', type=int, default=20, help='Quick run: only process first N files (default: 20)')
    parser.add_argument('--ensemble_votes', type=int, default=2, help='Number of model groups required to vote for fall in ensemble')
    parser.add_argument('--video_vote_ratio', type=float, default=0.2, help='Fraction of sampled frames in a video that must vote fall to mark video-level fall (default 0.2)')
    parser.add_argument('--video_min_consec', type=int, default=2, help='Minimum consecutive sampled frames voting fall to mark video-level fall (default 2)')
    parser.add_argument('--video_window_k', type=int, default=3, help='Sliding window size (k) for temporal smoothing (default 3)')
    parser.add_argument('--video_weighted', action='store_true', help='Enable weighted sliding-window voting (center-weighted)')
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / args.test_dir
    model_dir = args.model_dir

    print(f"Loading ONNX system and models from {model_dir} (repo-root: {repo_root})")
    system = PracticalQAIHubONNX()
    # A) Provider handling: prefer CUDA if available, otherwise CPU. Set onnx_providers on the wrapper so
    # PracticalQAIHubONNX creates sessions with the chosen providers.
    try:
        import onnxruntime as ort
        available = []
        try:
            available = ort.get_available_providers() or []
        except Exception:
            available = []
        preferred = []
        if 'CUDAExecutionProvider' in available:
            preferred.append('CUDAExecutionProvider')
        if 'CPUExecutionProvider' in available:
            preferred.append('CPUExecutionProvider')
        # fallback to CPU if nothing else
        if not preferred:
            preferred = ['CPUExecutionProvider']
        try:
            system.onnx_providers = getattr(system, 'onnx_providers', preferred)
        except Exception:
            system.onnx_providers = preferred
        print(f"Using ONNX providers: {system.onnx_providers}")
    except Exception:
        # if onnxruntime not importable, force CPU provider list for wrapper
        try:
            system.onnx_providers = getattr(system, 'onnx_providers', ['CPUExecutionProvider'])
        except Exception:
            system.onnx_providers = ['CPUExecutionProvider']

    # Try to load models from the specified model_dir relative to repo root
    # PracticalQAIHubONNX.load_mediapipe_models expects a model_dir name under src/models; we will pass a relative path name
    # If you pass models/onnx, it will try to load from src/models/models/onnx, so we normalize
    normalized_model_dir = None
    if model_dir.startswith('models/'):
        normalized_model_dir = model_dir.split('/', 1)[1]
    else:
        normalized_model_dir = model_dir

    # load models
    try:
        system.load_mediapipe_models(source='onnx', model_dir=normalized_model_dir, ext='.onnx')
    except Exception as e:
        print('Warning: failed to auto-load models via PracticalQAIHubONNX:', e)

    # Ensure ONNX sessions loaded
    for model_name, model_info in list(system.qai_hub_models.items()):
        try:
            system._load_onnx_session(model_name, model_info['model_path'], model_info)
        except Exception:
            # ignore; continue
            pass

    print(f"Loaded ONNX sessions: {list(system.onnx_sessions.keys())}")

    # If verbose, dump ONNX session I/O info (output/input tensor names and shapes)
    if args.verbose:
        verbose_map = {}
        for model_name, info in system.onnx_sessions.items():
            try:
                session = info.get('session')
                outs = []
                ins = []
                if session is not None:
                    try:
                        for o in session.get_outputs():
                            name = getattr(o, 'name', None)
                            shape = getattr(o, 'shape', None)
                            outs.append({'name': name, 'shape': shape})
                    except Exception:
                        # fallback: try introspecting attributes
                        try:
                            outs = [{'name': getattr(o, 'name', None)} for o in session.get_outputs()]
                        except Exception:
                            outs = []
                    try:
                        for i in session.get_inputs():
                            in_name = getattr(i, 'name', None)
                            in_shape = getattr(i, 'shape', None)
                            ins.append({'name': in_name, 'shape': in_shape})
                    except Exception:
                        ins = []
                verbose_map[model_name] = {'inputs': ins, 'outputs': outs}
                print(f"VERBOSE: model={model_name} inputs={ins} outputs={outs}")
            except Exception as e:
                verbose_map[model_name] = {'error': str(e)}

        try:
            vfile = repo_root / 'onnx_session_verbose.json'
            vfile.write_text(json.dumps(verbose_map, indent=2, default=str, ensure_ascii=False))
            print(f"Wrote ONNX session verbose info: {vfile}")
        except Exception as e:
            print('Warning: failed to write onnx_session_verbose.json', e)

    # build per-model specs from verbose map if available
    per_model_specs = {}
    try:
        vfile = repo_root / 'onnx_session_verbose.json'
        if vfile.exists():
            vm = json.loads(vfile.read_text())
            for mn, info in vm.items():
                ins = info.get('inputs') if isinstance(info, dict) else None
                spec = build_input_spec_from_verbose_entry(ins or [])
                per_model_specs[mn] = spec
    except Exception:
        per_model_specs = {}

    fall_detector = None
    if FallDetector is not None:
        try:
            fall_detector = FallDetector()
        except Exception as e:
            print('Warning: failed to initialize MediaPipe FallDetector, will skip mediapipe checks:', e)
            fall_detector = None

    files = find_test_files(test_dir)
    if args.quick_n and args.quick_n > 0:
        files = files[:args.quick_n]
    if not files:
        print(f"No test files found in {test_dir}; try test_images or update --test_dir")
        return

    entries = []

    for p in files:
        print('Processing', p)
        if p.suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv'}:
            res = process_video_file(p, system, fall_detector, frame_stride=args.frame_stride, per_model_specs=per_model_specs, ensemble_votes=args.ensemble_votes)
            if isinstance(res, list):
                entries.extend(res)
            else:
                entries.append(res)
        else:
            res = process_image_file(p, system, fall_detector, per_model_specs=per_model_specs, ensemble_votes=args.ensemble_votes)
            entries.append(res)

    # Post-process video frames into per-video summaries using temporal smoothing
    try:
        from collections import defaultdict

        video_groups = defaultdict(list)
        for e in entries:
            if e.get('type') == 'video_frame':
                video_groups[e.get('path')].append(e)

        # For each video, compute vote stats and a smoothed decision
        for vpath, frames in video_groups.items():
            # frames are in capture order because we appended in processing order
            total = len(frames)
            votes = [1 if f.get('ensemble', {}).get('detected') else 0 for f in frames]
            detected_count = sum(votes)
            ratio = (detected_count / total) if total > 0 else 0.0

            # compute longest consecutive run among sampled frames (original rule)
            longest = 0
            cur = 0
            for v in votes:
                if v:
                    cur += 1
                else:
                    if cur > longest:
                        longest = cur
                    cur = 0
            if cur > longest:
                longest = cur

            # sliding-window smoothing: compute windowed votes
            k = max(1, int(getattr(args, 'video_window_k', 3)))
            weighted = bool(getattr(args, 'video_weighted', False))

            window_votes = []
            weights = None
            if weighted and k > 1:
                # center-weighted triangular window
                center = (k - 1) / 2.0
                weights = [1.0 + (1.0 - abs(i - center) / center) if center != 0 else 1.0 for i in range(k)]
            else:
                weights = [1.0] * k

            for i in range(total):
                # compute window range centered at i
                half = k // 2
                start = max(0, i - half)
                end = min(total, start + k)
                # adjust start when near end
                if end - start < k:
                    start = max(0, end - k)
                wsum = 0.0
                wtot = 0.0
                for j, widx in enumerate(range(start, end)):
                    w = weights[j - (start - max(0, i - half))] if weights else 1.0
                    wsum += votes[widx] * w
                    wtot += w
                window_votes.append((wsum / wtot) if wtot > 0 else 0.0)

            # convert window_votes to thresholded detections (>=0.5)
            window_detects = [1 if v >= 0.5 else 0 for v in window_votes]
            window_detected_count = sum(window_detects)
            window_ratio = (window_detected_count / total) if total > 0 else 0.0

            # final video-level decision: OR of existing rules and sliding-window result
            video_detected = (ratio >= float(args.video_vote_ratio)) or (longest >= int(args.video_min_consec)) or (window_ratio >= float(args.video_vote_ratio))
            first_detect = None
            # prefer first frame detected in windowed detection, else original
            for idx, v in enumerate(window_detects):
                if v:
                    first_detect = frames[idx]['frame_idx']
                    break
            if first_detect is None:
                detected_frames_idx = [i for i, f in enumerate(frames) if f.get('ensemble', {}).get('detected')]
                first_detect = frames[detected_frames_idx[0]]['frame_idx'] if detected_frames_idx else None

            summary = {
                'path': vpath,
                'type': 'video_summary',
                'timestamp': time.time(),
                'sampled_frames': total,
                'detected_frames_count': detected_count,
                'detected_frames_idx': [f.get('frame_idx') for f in frames if f.get('ensemble', {}).get('detected')],
                'detected_ratio': ratio,
                'longest_consecutive_detected': longest,
                'window_k': k,
                'window_weighted': weighted,
                'window_detected_count': window_detected_count,
                'window_detected_ratio': window_ratio,
                'detected_video': bool(video_detected),
                'first_detect_frame': first_detect,
                'vote_rule': {
                    'video_vote_ratio': args.video_vote_ratio,
                    'video_min_consec': args.video_min_consec,
                    'video_window_k': k,
                    'video_weighted': weighted
                }
            }
            entries.append(summary)
    except Exception:
        # don't fail report generation on summary errors
        pass

    write_reports(Path(args.out_json), Path(args.out_html), entries)
    print(f"Reports written: {args.out_json}, {args.out_html}")


if __name__ == '__main__':
    main()
