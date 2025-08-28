"""Clean Streamlit demo for macOS local inference.

Simpler, compact demo intended as the canonical, non-duplicated example
that prefers ONNX (if available) and falls back to MediaPipe pose.

This script accepts a small set of optional CLI flags when launched with
`streamlit run` (pass them after `--`). Example:

    streamlit run src/infer_demo_Mac/live_demo_mac.py -- --camera_id 1 --resolution 640x480

Recognized flags (best-effort, non-intrusive):
    --camera_id INT       default camera index used by the demo (overrides sidebar default)
    --resolution WxH      preferred resolution string
    --no_display          hints to the demo to run without UI display (best-effort)
    --onnx_model PATH     preselect an ONNX model path (if found)

Run:
    pip install -r src/infer_demo_Mac/requirements_inferMac.txt
    streamlit run src/infer_demo_Mac/live_demo_mac.py
"""

from typing import Optional, Tuple, List
import tempfile
from collections import deque
import io
import csv
import os
import glob
import time
import threading
import subprocess
import cv2
import numpy as np
import streamlit as st
from PIL import Image
import mediapipe as mp
import traceback
import sys
import argparse
from pathlib import Path
from adapters.pose_adapter import PoseAdapter
from features.fall_features import extract_basic_features
import logging
import json

# prefer wide layout for PC demo
try:
    st.set_page_config(layout='wide')
except Exception:
    pass

from detectors.fall_detector import FallDetector
from detectors.fusion_trigger import FusionTrigger

try:
    import onnxruntime as ort
except Exception:
    ort = None

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models', 'qaihub_optimized')
DEPLOY_DIR = os.path.join(BASE_DIR, 'models', 'deploy')

# Parse best-effort CLI args passed after `--` when running with streamlit.
# Use parse_known_args so unknown Streamlit args are ignored.
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument('--camera_id', type=int, default=None)
_parser.add_argument('--resolution', type=str, default=None)
_parser.add_argument('--no_display', action='store_true')
_parser.add_argument('--onnx_model', type=str, default=None)
try:
    _args, _unknown = _parser.parse_known_args(sys.argv[1:])
except Exception:
    # fallback to defaults if parsing fails
    class _A: pass
    _args = _A()
    _args.camera_id = None
    _args.resolution = None
    _args.no_display = False
    _args.onnx_model = None

# module-level defaults used inside Streamlit UI as initial values
DEFAULT_CAMERA_INDEX = _args.camera_id if getattr(_args, 'camera_id', None) is not None else 0
DEFAULT_RESOLUTION = _args.resolution if getattr(_args, 'resolution', None) else '640x480'
DEFAULT_NO_DISPLAY = bool(getattr(_args, 'no_display', False))
DEFAULT_ONNX_MODEL = _args.onnx_model if getattr(_args, 'onnx_model', None) else None


def find_onnx_models() -> tuple:
    """Search for ONNX models.

    Preference order: `src/models/deploy/` then `src/models/qaihub_optimized/`.
    Returns a tuple: (models_list, base_dir_used)
    """
    search_dirs = [DEPLOY_DIR, MODELS_DIR]
    for base in search_dirs:
        if not os.path.isdir(base):
            continue
        candidates = sorted(glob.glob(os.path.join(base, '**', '*'), recursive=True))
        models = []
        for p in candidates:
            try:
                if os.path.isfile(p) and p.lower().endswith('.onnx'):
                    models.append(p)
                elif os.path.isdir(p) and p.lower().endswith('.onnx'):
                    # prefer model.onnx inside a .onnx-named directory
                    m = os.path.join(p, 'model.onnx')
                    if os.path.isfile(m):
                        models.append(m)
                    else:
                        inner = glob.glob(os.path.join(p, '**', '*.onnx'), recursive=True)
                        for ip in sorted(inner):
                            if os.path.isfile(ip):
                                models.append(ip)
            except Exception:
                continue
        # unique & sorted
        seen = set()
        out = []
        for m in models:
            if m not in seen:
                seen.add(m)
                out.append(m)
        if out:
            return out, base
    # nothing found
    return [], MODELS_DIR


def can_load_onnx(path: str) -> bool:
    """Quick check whether onnxruntime can create a session for this model.

    This is best-effort and fast-fails on exceptions. We don't run full inference.
    """
    # lightweight check: file exists and non-zero size
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except Exception:
        return False


class ONNXRunner:
    """Small, best-effort ONNX runner."""
    def __init__(self, path: str, providers: Optional[List[str]] = None):
        # lightweight constructor: don't create heavy InferenceSession here.
        self.path = path
        self.requested_providers = providers
        self.sess = None
        self.provider_used = None
        self.input_name = None
        self.input_shape = None
        self.input_dtype = None
        self.metadata = {'path': path}

    def _create_session(self):
        # create the InferenceSession lazily and populate metadata
        if self.sess is not None:
            return
        if ort is None:
            raise RuntimeError('onnxruntime missing')
        avail = []
        try:
            avail = ort.get_available_providers() or []
        except Exception:
            avail = []
        pref = [
            'CoreMLExecutionProvider',
            'SNPEExecutionProvider',
            'QNNExecutionProvider',
            'CUDAExecutionProvider',
            'TensorrtExecutionProvider',
            'DMLExecutionProvider',
            'OpenVINOExecutionProvider',
            'CPUExecutionProvider'
        ]
        if self.requested_providers:
            used = [p for p in self.requested_providers if p in avail]
        else:
            used = [p for p in pref if p in avail]
        if not used:
            used = avail or ['CPUExecutionProvider']
        # quick scan for quantized ops that typical ort builds don't implement (e.g., ConvInteger)
        try:
            import onnx
            try:
                m = onnx.load(self.path)
                op_types = set(n.op_type for n in m.graph.node)
                quant_ops = [op for op in op_types if 'ConvInteger' in op or 'Integer' in op or 'Quant' in op or 'QLinear' in op]
                if quant_ops:
                    # persist metadata and raise a clear error so UI can show helpful message
                    self.metadata.update({'quant_ops': quant_ops})
                    raise RuntimeError(f'Model contains quantized ops not supported by this runtime: {quant_ops}')
            except Exception:
                # if onnx parsing fails, continue to try session creation and let ort report the error
                pass
        except Exception:
            # onnx library not available; skip op scanning
            pass
        try:
            self.sess = ort.InferenceSession(self.path, providers=used)
            self.provider_used = used[0] if used else 'CPUExecutionProvider'
        except Exception:
            # fallback to CPU explicitly
            self.sess = ort.InferenceSession(self.path, providers=['CPUExecutionProvider'])
            self.provider_used = 'CPUExecutionProvider'
        try:
            inp = self.sess.get_inputs()
            self.input_name = inp[0].name if inp else None
            first = inp[0] if inp else None
            if first is not None:
                self.input_shape = [None if (isinstance(d, str) and d == 'None') else d for d in list(first.shape)]
                self.input_dtype = str(first.type)
        except Exception:
            self.input_name = None
            self.input_shape = None
            self.input_dtype = None
        # collect metadata
        try:
            self.metadata = {
                'path': self.path,
                'provider': self.provider_used,
                'inputs': [
                    {'name': i.name, 'shape': [d for d in i.shape], 'dtype': str(i.type)} for i in self.sess.get_inputs()
                ],
                'outputs': [
                    {'name': o.name, 'shape': [d for d in o.shape], 'dtype': str(o.type)} for o in self.sess.get_outputs()
                ]
            }
        except Exception:
            self.metadata = {'path': self.path, 'provider': self.provider_used, 'inputs': [], 'outputs': []}

    def run(self, rgb: np.ndarray):
        # Ensure session exists (lazy create at inference time)
        if self.sess is None:
            self._create_session()

        # Best-effort preprocessing. Many ONNX models expect NCHW or NHWC with a fixed HxW.
        x = rgb.copy()
        # detect target H/W if provided in input_shape
        try:
            target_h = None
            target_w = None
            if self.input_shape and len(self.input_shape) >= 3:
                # common patterns: [N,C,H,W] or [N,H,W,C]
                s = self.input_shape
                if len(s) == 4:
                    # try to detect which pos is H/W by finding small ints
                    if isinstance(s[2], int) and isinstance(s[3], int):
                        # assume N,C,H,W
                        target_h, target_w = int(s[2]), int(s[3])
                    elif isinstance(s[1], int) and isinstance(s[2], int):
                        # assume N,H,W,C
                        target_h, target_w = int(s[1]), int(s[2])
                elif len(s) == 3:
                    # assume [C,H,W] or [H,W,C]
                    if isinstance(s[1], int) and isinstance(s[2], int):
                        target_h, target_w = int(s[1]), int(s[2])
        except Exception:
            target_h = None
            target_w = None

        if target_h is not None and target_w is not None:
            x = cv2.resize(x, (target_w, target_h))

        x = x.astype('float32')
        # normalize to 0..1 for float inputs (best-effort)
        if self.input_dtype and ('float' in self.input_dtype.lower()):
            x = x / 255.0

        # arrange channels: prefer CHW layout if input shape suggests it
        if x.ndim == 3:
            # detect if model expects CHW by checking if first non-batch dim is channels
            if self.input_shape and len(self.input_shape) >= 3:
                s = self.input_shape
                # heuristic: if first non-batch dim equals 3, assume NCHW
                if len(s) == 4 and s[1] == 3:
                    x = np.transpose(x, (2, 0, 1))
            # default to expand batch dim at axis 0
            x = np.expand_dims(x, 0)

        return self.sess.run(None, {self.input_name: x})


def compute_torso_angle_from_results(results, frame_shape: Tuple[int, int], key_mode='average', mode='simple') -> Optional[float]:
    if not results or not getattr(results, 'pose_landmarks', None):
        return None
    h, w = frame_shape[0], frame_shape[1]
    lm = results.pose_landmarks.landmark

    def to_xy(p):
        return np.array([p.x * w, p.y * h])

    try:
        ls = to_xy(lm[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER])
        rs = to_xy(lm[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER])
        lh = to_xy(lm[mp.solutions.pose.PoseLandmark.LEFT_HIP])
        rh = to_xy(lm[mp.solutions.pose.PoseLandmark.RIGHT_HIP])
    except Exception:
        return None

    if key_mode == 'left':
        shoulder, hip = ls, lh
    elif key_mode == 'right':
        shoulder, hip = rs, rh
    else:
        shoulder = (ls + rs) / 2.0
        hip = (lh + rh) / 2.0

    # angle between torso vector and vertical
    torso = shoulder - hip
    vert = np.array([0, -1.0])
    cos = np.dot(torso, vert) / (np.linalg.norm(torso) * np.linalg.norm(vert) + 1e-8)
    cos = np.clip(cos, -1.0, 1.0)
    # currently mode is a placeholder for alternate calculation strategies
    return float(np.degrees(np.arccos(cos)))


def compute_confidence_from_results(results) -> float:
    """Best-effort confidence from MediaPipe results (0.0-1.0).

    Uses shoulder/hip landmark visibility when available. Falls back to 1.0
    when visibility/presence not given but landmarks exist.
    """
    if not results or not getattr(results, 'pose_landmarks', None):
        return 0.0
    lm = results.pose_landmarks.landmark
    keys = [
        mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
        mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
        mp.solutions.pose.PoseLandmark.LEFT_HIP,
        mp.solutions.pose.PoseLandmark.RIGHT_HIP,
    ]
    vals = []
    for k in keys:
        v = getattr(lm[k], 'visibility', None)
        if v is None:
            v = getattr(lm[k], 'presence', None)
        if v is None:
            # assume present if landmark exists
            v = 1.0
        vals.append(float(v))
    if not vals:
        return 0.0
    return float(np.clip(np.mean(vals), 0.0, 1.0))


def interpret_onnx_output(onnx_out) -> dict:
    """Best-effort parse of ONNX outputs.

    Returns a dict with possible keys: 'prob' (0..1), 'raw'.
    """
    res = {'prob': None, 'raw': onnx_out, 'shapes': [], 'keypoints': None}
    try:
        if not onnx_out:
            return res
        first = onnx_out[0]
        arr = np.array(first)
        res['shapes'] = [np.array(o).shape for o in onnx_out]
        # scalar
        if arr.size == 1:
            prob = float(arr.flatten()[0])
            # clamp to [0,1]
            prob = float(np.clip(prob, 0.0, 1.0))
            res['prob'] = prob
            return res
        # vector -> try first element
        if arr.ndim == 1 and arr.size <= 4:
            prob = float(arr.flatten()[0])
            prob = float(np.clip(prob, 0.0, 1.0))
            res['prob'] = prob
            return res
        # attempt to detect keypoints: common encodings are [1, N*2] or [1, N*3] or [N,3]
        flat = arr.flatten().astype('float32')
        if arr.ndim == 2 and arr.shape[0] == 1 and flat.size in (34, 51, 68, 102):
            # 34 -> 17*2 (x,y), 51 -> 17*3 (x,y,conf)
            if flat.size % 3 == 0:
                n = flat.size // 3
                pts = flat.reshape((n, 3))
                res['keypoints'] = pts.tolist()
                return res
            if flat.size % 2 == 0:
                n = flat.size // 2
                pts = flat.reshape((n, 2))
                # append dummy confidence=1.0
                pts3 = np.concatenate([pts, np.ones((n, 1), dtype='float32')], axis=1)
                res['keypoints'] = pts3.tolist()
                return res
        # otherwise, normalize mean to 0..1 as fallback
        flat = arr.flatten().astype('float32')
        if flat.size > 0:
            mn, mx = float(flat.min()), float(flat.max())
            if mx - mn > 1e-6:
                norm = (flat - mn) / (mx - mn)
                res['prob'] = float(np.clip(float(np.mean(norm)), 0.0, 1.0))
            else:
                res['prob'] = float(np.clip(float(np.mean(flat)), 0.0, 1.0))
    except Exception:
        pass
    return res


def safe_download_button(label: str, data, file_name: str, use_sidebar: bool = False):
    """Wrapper for st.download_button that fails gracefully when Streamlit media storage is unavailable.

    Many Streamlit versions can raise a MediaFileStorageError or similar when an internal media id
    is missing (racey session state or removed temp file). Use this wrapper to catch and show
    a friendly error instead of letting a traceback bubble up.
    """
    try:
        if use_sidebar:
            # prefer sidebar context when caller expects it
            st.sidebar.download_button(label, data, file_name=file_name)
        else:
            st.download_button(label, data, file_name=file_name)
    except Exception as e:
        # show a short, user-friendly message (avoid showing full traceback)
        try:
            st.error(f'Unable to prepare download "{file_name}": {e}')
        except Exception:
            # if even st.error fails, silently ignore to avoid crashing the app
            pass


def compute_torso_angle_from_keypoints(keypoints: list, frame_shape: Tuple[int, int], key_mode='average') -> Optional[float]:
    """Compute torso angle from keypoints list (list of [x,y,conf]) where x,y are normalized [0..1] or pixel coords.

    This function attempts to handle both normalized (0..1) or pixel coordinates.
    """
    # guard against ambiguous truth-value for numpy arrays
    if keypoints is None:
        return None
    # coerce to numpy array for robust checks
    arr = np.array(keypoints, dtype='float32')
    # empty input
    if arr.size == 0:
        return None
    # ensure we have at least 2 columns (x,y)
    if arr.ndim == 1 or arr.shape[-1] < 2:
        return None
    h, w = frame_shape[0], frame_shape[1]
    # if values are in 0..1 assume normalized
    if np.max(arr[:, 0]) <= 1.0 and np.max(arr[:, 1]) <= 1.0:
        pts = np.copy(arr)
        pts[:, 0] = pts[:, 0] * w
        pts[:, 1] = pts[:, 1] * h
    else:
        pts = arr

    # try to index common pose layout: assume 17 keypoints layout (COCO-like) where
    # shoulders and hips are around indices 5,6,11,12 (approx) — fallback to first/last
    # Best-effort: look for left/right shoulder/hip by confidence ordering
    if pts.shape[0] >= 17:
        # common MPII/COCO ordering may differ — try common positions
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
        # fallback: pick top-most (shoulders) and lower-most (hips) by y coordinate
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


def main():
    st.title('SnapGuard AI Live Demo')

    # configure basic logging so adapter logs appear in Streamlit logs
    try:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger('infer_demo')
        logger.setLevel(logging.INFO)
    except Exception:
        pass

    # Sidebar: model selection and hyperparameters
    # Input controls moved to sidebar top (so model select + input are together)

    st.sidebar.header('Input Data Source')
    mode = st.sidebar.radio('Mode', ['Image', 'Video', 'Camera'])
    # use parsed default camera index when provided via CLI or env
    use_index = st.sidebar.number_input('Camera index', min_value=0, max_value=4, value=int(DEFAULT_CAMERA_INDEX))
    st.sidebar.markdown('---')
    
    st.sidebar.header('Model & Settings')
    # show last smoke test summary if available
    try:
        rpt = os.path.join(os.getcwd(), 'reports', 'onnx_smoke_test.json')
        if os.path.isfile(rpt):
            try:
                with open(rpt, 'r', encoding='utf-8') as f:
                    _j = json.load(f)
                # show a concise summary for the most recent entry
                if isinstance(_j, dict) and 'models_tested' in _j and len(_j['models_tested']) > 0:
                    st.sidebar.markdown('**Last ONNX smoke test**')
                    for m in _j['models_tested']:
                        try:
                            name = os.path.basename(m.get('model') or 'unknown')
                            # if file was missing or clearly invalid, show a friendly note
                            if m.get('file_ok') is False:
                                st.sidebar.write(f"{name} — skipped (file missing or invalid) — {m.get('error')}")
                                continue
                            prov = m.get('provider_used') or 'n/a'
                            infer_ok = bool(m.get('inference_ok'))
                            adapt_ok = bool(m.get('adapt_ok'))
                            st.sidebar.write(f"{name} — provider={prov} — infer_ok={infer_ok} — adapt_ok={adapt_ok}")
                        except Exception:
                            continue
            except Exception:
                pass
    except Exception:
        pass
    models, models_base = find_onnx_models()
    # Resolution selector (non-intrusive UI default)
    res_choices = ['320x240', '640x480', '1280x720']
    try:
        default_idx = res_choices.index(DEFAULT_RESOLUTION) if DEFAULT_RESOLUTION in res_choices else 1
    except Exception:
        default_idx = 1
    chosen_resolution = st.sidebar.selectbox('Resolution', res_choices, index=default_idx)
    # expose chosen_resolution to session (useful for downstream code or display)
    st.session_state['preferred_resolution'] = chosen_resolution
    # show which base directory we used (deploy preferred) and how many models found
    try:
        base_label = 'deploy' if os.path.normpath(models_base).endswith(os.path.normpath(DEPLOY_DIR)) else os.path.basename(models_base)
    except Exception:
        base_label = models_base
    st.sidebar.markdown('**Model source**')
    st.sidebar.info(f'{base_label} — {len(models)} model(s) found')

    show_all = st.sidebar.checkbox('Show all models (including ones that may not load)', value=False)

    # prepare usable/unusable lists
    usable = []
    unusable = []
    for m in models:
        if show_all:
            usable.append((m, True))
        else:
            ok = can_load_onnx(m)
            if ok:
                usable.append((m, True))
            else:
                unusable.append((m, False))

    display_items = []
    for m, ok in usable:
        try:
            rel = os.path.relpath(m, models_base)
        except Exception:
            rel = os.path.basename(m)
        display_items.append((rel, m, ok))
    if show_all:
        for m, ok in unusable:
            try:
                rel = os.path.relpath(m, models_base)
            except Exception:
                rel = os.path.basename(m)
            display_items.append((rel + ' (may not load)', m, ok))

    # Build a nicer label for the ONNX model select box: include status and size
    def _fmt_label(item):
        rel, path, ok = item
        try:
            sz = os.path.getsize(path)
            sz_kb = int(sz / 1024)
            size_str = f"{sz_kb}KB"
        except Exception:
            size_str = 'n/a'
        status = 'OK' if ok else 'may not load'
        return f"{rel} — {status} ({size_str})"

    if not display_items:
        display_models = ['MediaPipe (fallback)']
    else:
        display_models = ['MediaPipe (fallback)'] + [_fmt_label(d) for d in display_items]

    selected_model_display = st.sidebar.selectbox('ONNX Model (preferred)', display_models)
    if selected_model_display and selected_model_display != 'MediaPipe (fallback)':
        idx = display_models.index(selected_model_display) - 1
        if 0 <= idx < len(display_items):
            selected_path = display_items[idx][1]
        else:
            selected_path = None
    else:
        selected_path = None

    if 'onnx_runner' not in st.session_state:
        st.session_state.onnx_runner = None

    # sway/RISK controls
    st.sidebar.markdown('---')
    st.sidebar.header('Sway & Risk settings')
    sway_window = st.sidebar.number_input('Sway window (frames)', min_value=2, max_value=60, value=8)
    sway_scale = st.sidebar.slider('Sway normalization (deg)', 1, 30, 8)
    sway_threshold = st.sidebar.slider('Sway alert threshold (0..1)', 0.0, 1.0, 0.3)
    chart_metric = st.sidebar.selectbox('Chart metric', ['Risk score', 'Sway score', 'Both'])
    chart_history = st.sidebar.slider('Chart history (points)', 10, 1000, 100)
    # Auto-create session immediately when user changes selected model (so UI shows provider/inputs/outputs)
    if selected_path and ort is not None:
        prev_sel = st.session_state.get('onnx_selected_path')
        if prev_sel != selected_path:
            # record new selection
            st.session_state['onnx_selected_path'] = selected_path
            try:
                st.sidebar.info('Creating ONNX session for selected model...')
                st.session_state.onnx_runner = ONNXRunner(selected_path)
                try:
                    st.session_state.onnx_runner._create_session()
                    st.sidebar.success(f'ONNX session created (provider: {st.session_state.onnx_runner.provider_used})')
                except Exception as e:
                    tb = traceback.format_exc()
                    # persist traceback for inspection
                    try:
                        st.session_state.onnx_runner.metadata.update({'load_error': tb})
                    except Exception:
                        st.session_state.onnx_runner.metadata = {'path': selected_path, 'load_error': tb}
                    st.sidebar.error('ONNX session creation failed — see metadata for traceback')
            except Exception as e:
                st.sidebar.error(f'Unexpected error creating ONNX runner: {e}')

    if selected_path and ort is not None:
        auto_load = st.sidebar.checkbox('Auto-load selected ONNX', value=False)
        if st.sidebar.button('Load ONNX') or auto_load:
            try:
                if st.session_state.onnx_runner is None or st.session_state.onnx_runner.metadata.get('path') != selected_path:
                    # create runner and eagerly create the session so provider/inputs/outputs are available
                    st.session_state.onnx_runner = ONNXRunner(selected_path)
                    try:
                        st.session_state.onnx_runner._create_session()
                    except Exception as e:
                        # keep runner but report session creation failure
                        st.session_state.onnx_runner.metadata.update({'load_error': str(e)})
                        st.sidebar.error(f'ONNX session creation failed: {e}')
                        raise
                st.sidebar.success('ONNX loaded')
            except Exception as e:
                st.sidebar.error(f'ONNX load failed: {e}')

    # allow user to run a quick smoke test for the selected model and show report
    try:
        # initialize session_state keys if missing
        if 'smoke_test_status' not in st.session_state:
            st.session_state.smoke_test_status = 'idle'  # idle | running | done | error
            st.session_state.smoke_test_stdout = ''
            st.session_state.smoke_test_stderr = ''
            st.session_state.smoke_test_report = None

        def _run_smoke_test(model_path: str):
            """Background worker to run the smoke test script and capture streamed outputs into session_state.

            Uses subprocess.Popen so the main thread can request cancellation. Progress is heuristic.
            """
            try:
                st.session_state.smoke_test_status = 'running'
                st.session_state.smoke_test_stdout = ''
                st.session_state.smoke_test_stderr = ''
                st.session_state.smoke_test_progress = 0.0
                st.session_state.smoke_test_cancel = False
                script = os.path.join(os.getcwd(), 'scripts', 'onnx_smoke_test.py')
                py = sys.executable or 'python3'
                # ensure previous proc key cleared
                st.session_state.smoke_test_proc = None
                proc = None
                try:
                    proc = subprocess.Popen([py, script, model_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    st.session_state.smoke_test_proc = proc
                except Exception as e:
                    st.session_state.smoke_test_status = 'error'
                    st.session_state.smoke_test_stderr = str(e) + '\n' + traceback.format_exc()
                    return

                # stream stdout and stderr incrementally
                stdout_lines = []
                stderr_lines = []
                # non-blocking read loop: read lines as they arrive
                while True:
                    if proc.stdout is not None:
                        line = proc.stdout.readline()
                        if line:
                            stdout_lines.append(line)
                            # keep last ~20000 chars
                            st.session_state.smoke_test_stdout = (st.session_state.smoke_test_stdout + line)[-20000:]
                    if proc.stderr is not None:
                        el = proc.stderr.readline()
                        if el:
                            stderr_lines.append(el)
                            st.session_state.smoke_test_stderr = (st.session_state.smoke_test_stderr + el)[-20000:]

                    # heuristic progress update (bump slowly while running)
                    try:
                        p = st.session_state.get('smoke_test_progress', 0.0)
                        # increase by small amount until 0.9
                        if p < 0.9:
                            p = min(0.9, p + 0.03)
                        st.session_state.smoke_test_progress = p
                    except Exception:
                        pass

                    # check cancellation flag
                    if st.session_state.get('smoke_test_cancel'):
                        try:
                            proc.terminate()
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass
                        st.session_state.smoke_test_status = 'cancelled'
                        break

                    # check if process ended
                    ret = proc.poll()
                    if ret is not None:
                        # drain any remaining output
                        try:
                            out_tail = proc.stdout.read() if proc.stdout is not None else ''
                            err_tail = proc.stderr.read() if proc.stderr is not None else ''
                            if out_tail:
                                st.session_state.smoke_test_stdout = (st.session_state.smoke_test_stdout + out_tail)[-20000:]
                            if err_tail:
                                st.session_state.smoke_test_stderr = (st.session_state.smoke_test_stderr + err_tail)[-20000:]
                        except Exception:
                            pass
                        # attempt to load generated report
                        rpt = os.path.join(os.getcwd(), 'reports', 'onnx_smoke_test.json')
                        if os.path.isfile(rpt):
                            try:
                                with open(rpt, 'r', encoding='utf-8') as f:
                                    st.session_state.smoke_test_report = json.load(f)
                            except Exception:
                                st.session_state.smoke_test_report = None
                        # final progress
                        st.session_state.smoke_test_progress = 1.0
                        # success vs error
                        if ret == 0:
                            st.session_state.smoke_test_status = 'done'
                        else:
                            st.session_state.smoke_test_status = 'error'
                        break

                # cleanup
                try:
                    if proc and proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass
            except Exception as e:
                st.session_state.smoke_test_status = 'error'
                st.session_state.smoke_test_stderr = str(e) + '\n' + traceback.format_exc()

            if selected_path:
                col = st.sidebar
                # if a test is running, show status and allow cancel (cancel is best-effort)
                if st.session_state.get('smoke_test_status') == 'running':
                    col.info('Smoke test running...')
                    # progress bar
                    prog = float(st.session_state.get('smoke_test_progress', 0.0))
                    try:
                        col.progress(min(max(prog, 0.0), 1.0))
                    except Exception:
                        pass
                    if col.button('Cancel smoke test'):
                        st.session_state.smoke_test_cancel = True
                else:
                    if col.button('Run smoke test for selected model'):
                        # reset cancel and start background thread
                        st.session_state.smoke_test_cancel = False
                        th = threading.Thread(target=_run_smoke_test, args=(selected_path,), daemon=True)
                        th.start()

                # show last outputs and report if available
                status = st.session_state.get('smoke_test_status')
                if status and status != 'idle':
                    st.sidebar.markdown(f'**Smoke test status:** {status}')
                if st.session_state.get('smoke_test_stdout'):
                    with st.sidebar.expander('Smoke test stdout (recent)'):
                        st.code(st.session_state.get('smoke_test_stdout')[:8000])
                if st.session_state.get('smoke_test_stderr'):
                    with st.sidebar.expander('Smoke test stderr (recent)'):
                        st.code(st.session_state.get('smoke_test_stderr')[:8000])
                if st.session_state.get('smoke_test_report'):
                    try:
                        st.sidebar.markdown('**Smoke test report (recent)**')
                        for m in st.session_state.get('smoke_test_report', {}).get('models_tested', []):
                            st.sidebar.write(f"{os.path.basename(m.get('model'))} | provider={m.get('provider_used')} | infer_ok={m.get('inference_ok')} | adapt_ok={m.get('adapt_ok')}")
                    except Exception:
                        pass
                # show detailed report and allow download
                try:
                    rpt_path = os.path.join(os.getcwd(), 'reports', 'onnx_smoke_test.json')
                    if os.path.isfile(rpt_path):
                        if st.sidebar.button('Show detailed smoke report'):
                            try:
                                with open(rpt_path, 'r', encoding='utf-8') as f:
                                    full = f.read()
                                # open in an expander for readability
                                with st.expander('Full ONNX smoke test JSON'):
                                    st.code(full)
                                # offer download
                                try:
                                    safe_download_button('Download full smoke report', full.encode('utf-8'), file_name='onnx_smoke_test.json', use_sidebar=False)
                                except Exception:
                                    pass
                            except Exception:
                                st.sidebar.error('Failed to read smoke test report')

                    # Auto-resolve missing file entries: find entries in report with file_ok False and suggest inner model.onnx
                    if os.path.isfile(rpt_path) and st.sidebar.button('Auto-resolve missing models'):
                        try:
                            with open(rpt_path, 'r', encoding='utf-8') as f:
                                rep = json.load(f)
                        except Exception:
                            rep = None
                        resolved = []
                        if rep:
                            for e in rep.get('models_tested', []):
                                if e.get('file_ok') is False:
                                    p = e.get('model')
                                    try:
                                        # if path is a directory, look for model.onnx or first inner .onnx
                                        if os.path.isdir(p):
                                            cand = os.path.join(p, 'model.onnx')
                                            if os.path.isfile(cand):
                                                resolved.append((p, cand))
                                                continue
                                            inner = sorted(glob.glob(os.path.join(p, '**', '*.onnx'), recursive=True))
                                            for ip in inner:
                                                if os.path.isfile(ip):
                                                    resolved.append((p, ip))
                                                    break
                                        else:
                                            # maybe the report listed a path that doesn't exist but sibling model exists
                                            base = os.path.basename(p)
                                            parent = os.path.dirname(p)
                                            if os.path.isdir(parent):
                                                inner = sorted(glob.glob(os.path.join(parent, '**', '*.onnx'), recursive=True))
                                                for ip in inner:
                                                    if os.path.isfile(ip):
                                                        resolved.append((p, ip))
                                                        break
                                    except Exception:
                                        continue
                        # present results and allow per-item run
                        if not resolved:
                            st.sidebar.info('No auto-resolve candidates found')
                        else:
                            st.sidebar.markdown('**Auto-resolve suggestions**')
                            for orig, newp in resolved:
                                st.sidebar.write(f'{os.path.basename(orig)} -> {os.path.basename(newp)}')
                                if st.sidebar.button(f'Run smoke test for {os.path.basename(newp)}'):
                                    # start background run using existing runner
                                    th = threading.Thread(target=_run_smoke_test, args=(newp,), daemon=True)
                                    th.start()
                except Exception:
                    pass
    except Exception:
        pass

    # Model preview: look for a preview image next to the model file
    try:
        preview_shown = False
        if selected_path:
            mdir = os.path.dirname(selected_path)
            base = os.path.splitext(os.path.basename(selected_path))[0]
            candidates = [os.path.join(mdir, 'preview.png'), os.path.join(mdir, 'thumbnail.png'), os.path.join(mdir, f'{base}.png')]
            for c in candidates:
                if os.path.isfile(c):
                    try:
                        # open via PIL first to avoid relying on Streamlit's internal media id mapping
                        try:
                            img = Image.open(c).convert('RGB')
                            st.sidebar.image(img, caption='Model preview', use_column_width=True)
                        except Exception:
                            # fallback: let streamlit try to open the path directly
                            st.sidebar.image(c, caption='Model preview', use_column_width=True)
                        preview_shown = True
                        break
                    except Exception:
                        preview_shown = False
        if not preview_shown:
            # small helper: show model path short form
            if selected_path:
                st.sidebar.write(f'Model: {os.path.basename(selected_path)}')
    except Exception:
        pass

    # If an ONNX path was provided via CLI env (`DEFAULT_ONNX_MODEL`) try to pre-select it
    try:
        if DEFAULT_ONNX_MODEL:
            # if the DEFAULT_ONNX_MODEL path exists in detected models, select it
            found = None
            for rel, m, ok in display_items:
                if os.path.abspath(m) == os.path.abspath(DEFAULT_ONNX_MODEL) or os.path.basename(m) == os.path.basename(DEFAULT_ONNX_MODEL):
                    found = m
                    break
            if found and (st.session_state.get('onnx_selected_path') != found):
                st.session_state['onnx_selected_path'] = found
                st.session_state.onnx_runner = ONNXRunner(found)
                try:
                    st.session_state.onnx_runner._create_session()
                    st.sidebar.success(f'Auto-loaded ONNX (provider: {st.session_state.onnx_runner.provider_used})')
                except Exception as e:
                    st.sidebar.error(f'Auto-load ONNX failed: {e}')
            else:
                # if DEFAULT_ONNX_MODEL refers to a path not listed, try to create a runner directly
                if os.path.isfile(DEFAULT_ONNX_MODEL) and st.session_state.get('onnx_runner') is None:
                    try:
                        st.session_state.onnx_runner = ONNXRunner(DEFAULT_ONNX_MODEL)
                        st.session_state.onnx_runner._create_session()
                        st.sidebar.success(f'Auto-loaded ONNX (provider: {st.session_state.onnx_runner.provider_used})')
                        st.session_state['onnx_selected_path'] = DEFAULT_ONNX_MODEL
                    except Exception as e:
                        st.sidebar.error(f'Auto-load ONNX direct path failed: {e}')
    except Exception:
        pass

    if st.session_state.onnx_runner is not None:
        md = st.session_state.onnx_runner.metadata
        st.sidebar.markdown('**Loaded ONNX model**')
        st.sidebar.write(md.get('path'))
        st.sidebar.write('Inputs:')
        st.sidebar.json(md.get('inputs'))
        st.sidebar.write('Outputs:')
        st.sidebar.json(md.get('outputs'))
        # if loader stored a traceback, show a short excerpt
        if md.get('load_error'):
            st.sidebar.markdown('**ONNX load traceback (excerpt)**')
            st.sidebar.code(md.get('load_error')[:2000])
            # full traceback in an expander with download
            with st.sidebar.expander('Show full ONNX load traceback'):
                st.code(md.get('load_error'))
                try:
                    safe_download_button('Download load traceback', md.get('load_error').encode('utf-8'), file_name='onnx_load_trace.txt', use_sidebar=True)
                except Exception:
                    # some streamlit versions require different args; ignore if unavailable
                    pass

        # allow marking currently loaded model as default for start.sh auto-load
        try:
            cfg_dir = os.path.join(BASE_DIR, '..', '..', 'config')
            cfg_dir = os.path.normpath(os.path.abspath(cfg_dir))
            cfg_file = os.path.join(cfg_dir, 'default_onnx.txt')
            if st.sidebar.button('Mark this model as default'):
                try:
                    os.makedirs(cfg_dir, exist_ok=True)
                    with open(cfg_file, 'w', encoding='utf-8') as f:
                        f.write(str(md.get('path')))
                    st.sidebar.success(f'Marked as default: {os.path.basename(md.get("path"))}')
                except Exception as e:
                    st.sidebar.error(f'Failed to mark default: {e}')
            # show current default if exists
            if os.path.isfile(cfg_file):
                try:
                    with open(cfg_file, 'r', encoding='utf-8') as f:
                        cur = f.read().strip()
                    if cur:
                        st.sidebar.caption(f'Current default model: {os.path.basename(cur)}')
                except Exception:
                    pass
        except Exception:
            pass

    # show last runtime error if available
    if st.session_state.get('last_onnx_error'):
        st.sidebar.markdown('**Last ONNX runtime error**')
        with st.sidebar.expander('Show last ONNX runtime traceback'):
            st.code(st.session_state.get('last_onnx_error'))
            try:
                safe_download_button('Download runtime traceback', st.session_state.get('last_onnx_error').encode('utf-8'), file_name='onnx_runtime_trace.txt', use_sidebar=True)
            except Exception:
                pass

    # Allow user to test-load the currently selected ONNX model on-demand.
    if selected_path:
        if st.sidebar.button('Test ONNX model now'):
            try:
                tester = ONNXRunner(selected_path)
                try:
                    tester._create_session()
                    st.sidebar.success(f'Loaded with provider: {tester.provider_used}')
                    st.sidebar.write('Inputs:')
                    st.sidebar.json(tester.metadata.get('inputs'))
                    st.sidebar.write('Outputs:')
                    st.sidebar.json(tester.metadata.get('outputs'))

                    # try a quick dummy inference if possible
                    try:
                        sess = tester.sess
                        inputs = sess.get_inputs()
                        if inputs:
                            inp = inputs[0]
                            # replace unknown dims with 1
                            shape = [1 if (not isinstance(d, int) or d <= 0) else int(d) for d in inp.shape]
                            arr = np.zeros(tuple(shape), dtype=np.float32)
                            try:
                                _res = sess.run(None, {inp.name: arr})
                                st.sidebar.success(f'Dummy inference OK, outputs: {len(_res)}')
                            except Exception as e:
                                st.sidebar.error(f'Dummy inference failed: {e}')
                        else:
                            st.sidebar.info('Model has no inputs listed; skipping dummy inference')
                    except Exception as e:
                        st.sidebar.error(f'Inference check failed: {e}')
                except Exception as e:
                    st.sidebar.error(f'Failed to create session: {e}')
            except Exception as e:
                st.sidebar.error(f'Unexpected error during test: {e}')

    st.sidebar.markdown('---')
    st.sidebar.header('Hyperparams')
    key_mode = st.sidebar.selectbox('Torso keypoint', ['average', 'left', 'right'])
    angle_calc_mode = st.sidebar.selectbox('Angle calc mode', ['simple', 'advanced'])
    angle_thresh = st.sidebar.slider('Angle thresh', 20, 180, 80)
    confidence_threshold = st.sidebar.slider('Confidence thresh', 0.0, 1.0, 0.5, step=0.05)
    cooldown = st.sidebar.number_input('Cooldown (s)', min_value=1, max_value=30, value=5)
    st.sidebar.markdown('---')

    # create main layout columns: center = inference image/video, right = chart/engine info
    col_main, col_right = st.columns([3, 1])
    # persistent display slots inside columns
    onnx_output_slot = col_main.empty()
    engine_info_slot = col_right.empty()
    chart_slot_outer = col_right.empty()
    # bottom-fixed alert container so alerts don't push content
    bottom_alert = st.empty()
    fd = FallDetector()
    fusion = FusionTrigger(cooldown_seconds=float(cooldown))
    adapter = PoseAdapter()

    # camera toggle in sidebar (keeps state)
    camera_on = st.sidebar.checkbox('Camera on', value=False)
    # Notifications history / alerts (shown in sidebar)
    with st.sidebar.expander('Notifications (alerts sent)'):
        if 'alerts_sent' not in st.session_state or not st.session_state.get('alerts_sent'):
            st.write('No alerts sent yet')
        else:
            # display recent alerts
            for a in reversed(st.session_state.get('alerts_sent', [])[-10:]):
                try:
                    ts = a.get('ts')
                    timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) if ts else str(ts)
                    st.write(f"{timestr} — score={a.get('score')} — engine={a.get('engine')}")
                except Exception:
                    st.write(str(a))
        # CSV download for alerts
        try:
            if 'alerts_sent' in st.session_state and st.session_state.get('alerts_sent'):
                buf = io.StringIO()
                w = csv.writer(buf)
                w.writerow(['ts', 'score', 'engine'])
                for a in st.session_state.get('alerts_sent', []):
                    w.writerow([a.get('ts'), a.get('score'), a.get('engine')])
                try:
                    safe_download_button('Download alerts CSV', buf.getvalue().encode('utf-8'), file_name='alerts_sent.csv')
                except Exception:
                    pass
        except Exception:
            pass

    # risk history (pre-fall risk index over time)
    if 'risk_history' not in st.session_state:
        st.session_state.risk_history = []  # list of dicts: {ts, risk, sway, engine}
    if 'angle_window' not in st.session_state:
        st.session_state.angle_window = deque(maxlen=50)

    def push_risk(risk_score: float, sway_score: float, engine: str):
        st.session_state.risk_history.append({'ts': time.time(), 'risk': float(risk_score), 'sway': float(sway_score), 'engine': engine})

    def recent_risk_series():
        return [entry.get('risk', 0.0) for entry in st.session_state.risk_history]

    def recent_sway_series():
        return [entry.get('sway', 0.0) for entry in st.session_state.risk_history]

    def recent_series(metric='risk'):
        return recent_risk_series() if metric == 'risk' else recent_sway_series()

    if mode == 'Image':
        up = st.file_uploader('Upload image', type=['jpg', 'png', 'jpeg'])
        if up is not None:
            img = Image.open(up).convert('RGB')
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            # try ONNX first
            onnx_runner = st.session_state.onnx_runner
            onnx_used = False
            res = None
            angle = None
            conf = 0.0
            if onnx_runner is not None:
                try:
                    onnx_out = onnx_runner.run(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    # persist raw output for debugging and mark as used
                    st.session_state['last_onnx_output'] = onnx_out
                    onnx_used = True
                    parsed = interpret_onnx_output(onnx_out)
                    prob = parsed.get('prob') if parsed.get('prob') is not None else None
                    # prefer ONNX keypoints when available; try adapter if not directly provided
                    try:
                        kps = parsed.get('keypoints')
                        if kps is None:
                            kps = adapter.detect_and_adapt(parsed.get('raw'), frame.shape[1], frame.shape[0])
                    except Exception:
                        kps = None

                    if kps is not None:
                        # we have keypoints from ONNX (or adapted)
                        angle = compute_torso_angle_from_keypoints(kps, frame.shape, key_mode=key_mode)
                        try:
                            confs = [float(p[2]) for p in kps if len(p) >= 3]
                            conf = float(np.clip(np.mean(confs), 0.0, 1.0)) if confs else 1.0
                        except Exception:
                            conf = 1.0
                        risk_score = float(prob) if prob is not None else ((float(angle) / 180.0) * conf if angle is not None else 0.0)
                        fall = (float(prob) >= float(confidence_threshold)) if prob is not None else ((float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False)
                        # still run mediapipe for visualization
                        res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    elif prob is not None:
                        res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                        conf = float(prob)
                        fall = (prob >= float(confidence_threshold))
                        risk_score = float(prob)
                    else:
                        # run succeeded but output not recognized; fall back to mediapipe-derived metrics
                        res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                        conf = compute_confidence_from_results(res)
                        risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                        fall = (float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False
                    try:
                        onnx_output_slot.markdown('**ONNX output (raw)**')
                        onnx_output_slot.text(str(parsed.get('raw'))[:500])
                    except Exception:
                        pass
                    # adapt ONNX keypoints to canonical schema if available
                    try:
                        kps = parsed.get('keypoints')
                        if kps is not None:
                            adapted = adapter.adapt_keypoint_list(kps, frame.shape[1], frame.shape[0])
                            if adapted is not None:
                                # compute features on a single-frame window
                                feats = extract_basic_features(adapted[np.newaxis, ...], fps=25.0)
                                st.session_state['last_adapter_summary'] = feats.get('summary')
                    except Exception:
                        pass
                except Exception:
                    onnx_used = False
                    st.session_state['last_onnx_error'] = traceback.format_exc()
            # determine engine label
            engine_label = 'ONNX' if onnx_used else 'MediaPipe'

            if not onnx_used:
                res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                conf = compute_confidence_from_results(res)
                risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                fall = (float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False
                risk_score = float(risk_score)
                onnx_used = False

            # adapt MediaPipe landmarks if present and compute basic features
            try:
                if getattr(res, 'pose_landmarks', None):
                    adapted = adapter.adapt_mediapipe(getattr(res, 'pose_landmarks'), frame.shape[1], frame.shape[0])
                    if adapted is not None:
                        feats = extract_basic_features(adapted[np.newaxis, ...], fps=25.0)
                        st.session_state['last_adapter_summary'] = feats.get('summary')
                        # show a small summary in sidebar
                        try:
                            st.sidebar.write('Adapter summary (latest frame):')
                            st.sidebar.json(feats.get('summary'))
                        except Exception:
                            pass
            except Exception:
                pass

            # compute sway score from recent angle window
            try:
                if angle is None:
                    sway_score = 0.0
                else:
                    st.session_state.angle_window.append(float(angle))
                    # use last `sway_window` frames
                    window = list(st.session_state.angle_window)[-int(sway_window):]
                    if len(window) <= 1:
                        sway_score = 0.0
                    else:
                        s = float(np.std(np.array(window)))
                        sway_score = float(np.clip(s / float(sway_scale), 0.0, 1.0))
            except Exception:
                sway_score = 0.0

            push_risk(risk_score, sway_score, engine_label)
            risk = {'level': 'high' if fall else 'low', 'score': float(risk_score)}

            out = fd.draw_pose_landmarks(frame.copy(), getattr(res, 'pose_landmarks', None))
            out = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
            col_main.image(out)
            # write single items to column to avoid Streamlit error about replacing with multiple elements
            col_main.write(f'Angle: {angle}')
            col_main.write(f'Fall: {fall}')
            # show small history chart in right column (slice to history length)
            try:
                if chart_metric == 'Risk score':
                    chart_slot_outer.line_chart(recent_risk_series()[-int(chart_history):])
                elif chart_metric == 'Sway score':
                    chart_slot_outer.line_chart(recent_sway_series()[-int(chart_history):])
                else:
                    chart_slot_outer.write('Risk (blue) and Sway (orange)')
                    chart_slot_outer.line_chart({'risk': recent_risk_series()[-int(chart_history):], 'sway': recent_sway_series()[-int(chart_history):]})
            except Exception:
                pass
            col_main.write('Risk')
            col_main.write(risk)
            # CSV download
            try:
                csv_buf = io.StringIO()
                w = csv.writer(csv_buf)
                w.writerow(['ts', 'risk', 'sway', 'engine'])
                for r in st.session_state.risk_history:
                    w.writerow([r.get('ts'), r.get('risk'), r.get('sway'), r.get('engine')])
                try:
                    safe_download_button('Download risk history CSV', csv_buf.getvalue().encode('utf-8'), file_name='risk_history.csv')
                except Exception:
                    pass
            except Exception:
                pass
            if onnx_used:
                engine_info_slot.info(f'Inference engine: ONNX ({getattr(st.session_state.get("onnx_runner"), "provider_used", "unknown")})')
            else:
                engine_info_slot.info('Inference engine: MediaPipe (fallback)')
            # bottom-fixed alert
            bottom_alert.empty()
            if fusion.should_trigger_alert(fall_detected=fall, help_detected=False):
                bottom_alert.warning('ALERT')
    elif mode == 'Video':
        up = st.file_uploader('Upload video', type=['mp4', 'mov', 'avi'])
        if up is not None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tmp.write(up.read())
            tmp.flush()
            cap = cv2.VideoCapture(tmp.name)
            frame_slot = col_main.empty()
            chart_slot = col_right.empty()
            stop = st.button('Stop')
            while cap.isOpened() and not stop:
                ret, frame = cap.read()
                if not ret:
                    break
                onnx_runner = st.session_state.onnx_runner
                onnx_used = False
                res = None
                angle = None
                conf = 0.0
                if onnx_runner is not None:
                    try:
                        onnx_out = onnx_runner.run(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        st.session_state['last_onnx_output'] = onnx_out
                        onnx_used = True
                        parsed = interpret_onnx_output(onnx_out)
                        prob = parsed.get('prob') if parsed.get('prob') is not None else None
                        if parsed.get('keypoints') is not None:
                            kps = parsed.get('keypoints')
                            angle = compute_torso_angle_from_keypoints(kps, frame.shape, key_mode=key_mode)
                            try:
                                confs = [float(p[2]) for p in kps if len(p) >= 3]
                                conf = float(np.clip(np.mean(confs), 0.0, 1.0)) if confs else 1.0
                            except Exception:
                                conf = 1.0
                            risk_score = float(prob) if prob is not None else ((float(angle) / 180.0) * conf if angle is not None else 0.0)
                            fall = (float(prob) >= float(confidence_threshold)) if prob is not None else ((float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False)
                            res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        elif prob is not None:
                            res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                            conf = float(prob)
                            fall = (prob >= float(confidence_threshold))
                            risk_score = float(prob)
                        else:
                            res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                            conf = compute_confidence_from_results(res)
                            risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                            fall = (float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False
                        try:
                            onnx_output_slot.markdown('**ONNX output (raw)**')
                            onnx_output_slot.text(str(parsed.get('raw'))[:500])
                        except Exception:
                            pass
                        try:
                            kps = parsed.get('keypoints')
                            if kps is None:
                                kps = adapter.detect_and_adapt(parsed.get('raw'), frame.shape[1], frame.shape[0])
                            if kps is not None:
                                adapted = adapter.adapt_keypoint_list(kps, frame.shape[1], frame.shape[0])
                                if adapted is not None:
                                    # append to per-video sequence buffer
                                    if 'video_kp_seq' not in st.session_state:
                                        st.session_state['video_kp_seq'] = []
                                    st.session_state['video_kp_seq'].append(adapted)
                                    # compute per-frame minimal features as well
                                    feats = extract_basic_features(adapted[np.newaxis, ...], fps=25.0)
                                    st.session_state['last_adapter_summary'] = feats.get('summary')
                        except Exception:
                            pass
                    except Exception:
                        onnx_used = False
                        st.session_state['last_onnx_error'] = traceback.format_exc()

                if not onnx_used:
                    res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                    conf = compute_confidence_from_results(res)
                    risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                    fall = (float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False
                    risk_score = float(risk_score)
                    onnx_used = False

                # MediaPipe adapt + feature extraction for video frame
                try:
                    if getattr(res, 'pose_landmarks', None):
                        adapted = adapter.adapt_mediapipe(getattr(res, 'pose_landmarks'), frame.shape[1], frame.shape[0])
                        if adapted is not None:
                            feats = extract_basic_features(adapted[np.newaxis, ...], fps=25.0)
                            st.session_state['last_adapter_summary'] = feats.get('summary')
                except Exception:
                    pass

                # compute engine label and sway_score (same logic as Image mode)
                engine_label = 'ONNX' if onnx_used else 'MediaPipe'
                try:
                    if angle is None:
                        sway_score = 0.0
                    else:
                        st.session_state.angle_window.append(float(angle))
                        window = list(st.session_state.angle_window)[-int(sway_window):]
                        if len(window) <= 1:
                            sway_score = 0.0
                        else:
                            s = float(np.std(np.array(window)))
                            sway_score = float(np.clip(s / float(sway_scale), 0.0, 1.0))
                except Exception:
                    sway_score = 0.0

                push_risk(risk_score, sway_score, engine_label)
                annotated = fd.draw_pose_landmarks(frame.copy(), getattr(res, 'pose_landmarks', None))
                annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_slot.image(annotated)
                chart_slot.line_chart(recent_series()[-int(chart_history):])
                # show risk level
                try:
                    level = 'HIGH' if risk.get('level') == 'high' else 'LOW'
                    if level == 'HIGH':
                        col_main.error(f'Risk level: {level} (score={risk.get("score")})')
                    else:
                        col_main.info(f'Risk level: {level} (score={risk.get("score")})')
                except Exception:
                    pass
                # bottom-fixed alert and fall notification
                bottom_alert.empty()
                if fusion.should_trigger_alert(fall_detected=fall, help_detected=False):
                    # red alert for actual fall
                    bottom_alert.error('FALL DETECTED!')
                    # record notification (placeholder) so we don't actually call external services
                    def record_and_notify(ts, score, engine):
                        if 'alerts_sent' not in st.session_state:
                            st.session_state.alerts_sent = []
                        st.session_state.alerts_sent.append({'ts': ts, 'score': score, 'engine': engine})
                    try:
                        record_and_notify(time.time(), risk.get('score'), engine_label)
                    except Exception:
                        pass
                if onnx_used:
                    engine_info_slot.info(f'Inference engine: ONNX ({getattr(st.session_state.get("onnx_runner"), "provider_used", "unknown")})')
                else:
                    engine_info_slot.info('Inference engine: MediaPipe (fallback)')
                time.sleep(0.03)
            cap.release()
            # video processing done: if we have a sequence, resample to 25fps and compute sequence features
            try:
                seq = st.session_state.pop('video_kp_seq', None)
                if seq is not None and len(seq) > 0:
                    seq_arr = np.stack(seq, axis=0)  # T x 17 x 3
                    # try to read video fps; fallback to 25
                    try:
                        src_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                    except Exception:
                        src_fps = 25.0
                    resampled = adapter.resample_time_series(seq_arr, src_fps=src_fps, target_fps=25.0)
                    if resampled is not None:
                        # optional smoothing
                        smooth = adapter.temporal_smooth(resampled, alpha=0.6)
                        feats = extract_basic_features(smooth, fps=25.0)
                        st.session_state['last_adapter_summary'] = feats.get('summary')
                        # expose sequence length
                        st.sidebar.write(f'Video frames processed: {seq_arr.shape[0]} -> resampled: {smooth.shape[0]}')
            except Exception:
                pass

    else:
        # live camera via OpenCV (server-side streaming)
        # camera index and toggle are in sidebar; use checkbox camera_on to control loop
        if camera_on:
            cap = cv2.VideoCapture(int(use_index))
            # apply preferred resolution to capture if provided
            pref = st.session_state.get('preferred_resolution', DEFAULT_RESOLUTION)
            try:
                parts = str(pref).lower().split('x')
                targ_w = int(parts[0])
                targ_h = int(parts[1])
            except Exception:
                targ_w, targ_h = None, None
            try:
                if targ_w and targ_h:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, targ_w)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, targ_h)
                    # store target dims for loop resizing
                    st.session_state['_cap_target'] = (targ_w, targ_h)
            except Exception:
                pass
            frame_slot = col_main.empty()
            chart_slot = col_right.empty()
            # ensure the keep_camera widget exists once in the sidebar
            if 'keep_camera' not in st.session_state:
                st.session_state['keep_camera'] = True
            # create the checkbox widget once (key ensures single element)
            st.sidebar.checkbox('Keep camera running', value=st.session_state['keep_camera'], key='keep_camera')
            while cap.isOpened() and st.session_state.get('keep_camera', True):
                ret, frame = cap.read()
                if not ret:
                    break
                # enforce preferred resolution to the frame (resize as needed)
                try:
                    target = st.session_state.get('_cap_target')
                    if target and frame is not None:
                        tw, th = target
                        # OpenCV uses width x height for resize
                        frame = cv2.resize(frame, (int(tw), int(th)))
                except Exception:
                    pass
                onnx_runner = st.session_state.onnx_runner
                onnx_used = False
                res = None
                angle = None
                conf = 0.0
                if onnx_runner is not None:
                    try:
                        onnx_out = onnx_runner.run(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        st.session_state['last_onnx_output'] = onnx_out
                        onnx_used = True
                        parsed = interpret_onnx_output(onnx_out)
                        prob = parsed.get('prob') if parsed.get('prob') is not None else None
                        if parsed.get('keypoints') is not None:
                            kps = parsed.get('keypoints')
                            angle = compute_torso_angle_from_keypoints(kps, frame.shape, key_mode=key_mode)
                            try:
                                confs = [float(p[2]) for p in kps if len(p) >= 3]
                                conf = float(np.clip(np.mean(confs), 0.0, 1.0)) if confs else 1.0
                            except Exception:
                                conf = 1.0
                            risk_score = float(prob) if prob is not None else ((float(angle) / 180.0) * conf if angle is not None else 0.0)
                            fall = (float(prob) >= float(confidence_threshold)) if prob is not None else ((float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False)
                            res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        elif prob is not None:
                            res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                            conf = float(prob)
                            fall = (prob >= float(confidence_threshold))
                            risk_score = float(prob)
                        else:
                            res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                            conf = compute_confidence_from_results(res)
                            risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                            fall = (float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False
                        try:
                            onnx_output_slot.markdown('**ONNX output (raw)**')
                            onnx_output_slot.text(str(parsed.get('raw'))[:500])
                        except Exception:
                            pass
                        try:
                            kps = parsed.get('keypoints')
                            if kps is None:
                                kps = adapter.detect_and_adapt(parsed.get('raw'), frame.shape[1], frame.shape[0])
                            if kps is not None:
                                adapted = adapter.adapt_keypoint_list(kps, frame.shape[1], frame.shape[0])
                                if adapted is not None:
                                    feats = extract_basic_features(adapted[np.newaxis, ...], fps=25.0)
                                    st.session_state['last_adapter_summary'] = feats.get('summary')
                        except Exception:
                            pass
                    except Exception:
                        onnx_used = False
                        st.session_state['last_onnx_error'] = traceback.format_exc()

                if not onnx_used:
                    res = fd.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    angle = compute_torso_angle_from_results(res, frame.shape, key_mode=key_mode, mode=angle_calc_mode)
                    conf = compute_confidence_from_results(res)
                    risk_score = (float(angle) / 180.0) * conf if angle is not None else 0.0
                    fall = (float(angle) > float(angle_thresh) and conf >= float(confidence_threshold)) if angle is not None else False
                    risk_score = float(risk_score)
                    onnx_used = False

                # MediaPipe adapt + feature extraction for live camera frame
                try:
                    if getattr(res, 'pose_landmarks', None):
                        adapted = adapter.adapt_mediapipe(getattr(res, 'pose_landmarks'), frame.shape[1], frame.shape[0])
                        if adapted is not None:
                            feats = extract_basic_features(adapted[np.newaxis, ...], fps=25.0)
                            st.session_state['last_adapter_summary'] = feats.get('summary')
                except Exception:
                    pass

                # compute engine label and sway_score (same logic as Image mode)
                engine_label = 'ONNX' if onnx_used else 'MediaPipe'
                try:
                    if angle is None:
                        sway_score = 0.0
                    else:
                        st.session_state.angle_window.append(float(angle))
                        window = list(st.session_state.angle_window)[-int(sway_window):]
                        if len(window) <= 1:
                            sway_score = 0.0
                        else:
                            s = float(np.std(np.array(window)))
                            sway_score = float(np.clip(s / float(sway_scale), 0.0, 1.0))
                except Exception:
                    sway_score = 0.0

                push_risk(risk_score, sway_score, engine_label)
                annotated = fd.draw_pose_landmarks(frame.copy(), getattr(res, 'pose_landmarks', None))
                annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_slot.image(annotated)
                chart_slot.line_chart(recent_series()[-int(chart_history):])
                # show risk level
                try:
                    level = 'HIGH' if risk.get('level') == 'high' else 'LOW'
                    if level == 'HIGH':
                        col_main.error(f'Risk level: {level} (score={risk.get("score")})')
                    else:
                        col_main.info(f'Risk level: {level} (score={risk.get("score")})')
                except Exception:
                    pass
                # bottom-fixed alert and fall notification
                bottom_alert.empty()
                if fusion.should_trigger_alert(fall_detected=fall, help_detected=False):
                    bottom_alert.error('FALL DETECTED!')
                    try:
                        record_and_notify(time.time(), risk.get('score'), engine_label)
                    except Exception:
                        pass
                if onnx_used:
                    engine_info_slot.info(f'Inference engine: ONNX ({getattr(st.session_state.get("onnx_runner"), "provider_used", "unknown")})')
                else:
                    engine_info_slot.info('Inference engine: MediaPipe (fallback)')
                # keep loop until checkbox in sidebar is unchecked
                if not st.session_state.get('keep_camera', True):
                    break
                time.sleep(0.03)
            cap.release()


if __name__ == '__main__':
    main()
