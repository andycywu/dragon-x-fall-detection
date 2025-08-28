"""Minimal PoseAdapter: map common model outputs to a canonical COCO-17 schema.

This is a small PoC: it provides helpers to adapt MediaPipe landmarks and
generic keypoint lists (e.g., ONNX outputs) into a (17,3) array: [x,y,conf]
with x,y normalized to [0,1].
"""
from typing import Optional
import numpy as np
import os
import json
import logging

# module-level logger for adapter
logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
except Exception:
    mp = None


class PoseAdapter:
    def __init__(self, schema: str = "coco17"):
        # currently only coco17 supported in PoC
        self.schema = schema
        # temperature for soft-argmax (higher -> sharper)
        self.softargmax_temp = 1.0
        # max heatmap channels to attempt decoding (protects from extremely large C)
        self.max_heatmap_ch = 64
        # per-model output name hints for common deploy models
        # keys: model short name -> dict with output name hints
        # Example: litehrnet exports tensors named 'keypoints' [1,17,2] and 'scores' [1,17]
        self.model_output_map = {
            'litehrnet': {
                'kps': ['keypoints', 'pred', 'keypoints_output', 'keypoint', 'keypoints:0'],
                'scores': ['scores', 'score', 'scores_output', 'score:0']
            },
            # generic hints for pose_landmarks-like deploy bundles scanned in repo
            'pose_landmarks_detector': {
                'kps': ['output_0', 'output_1', 'output_2', 'output_3', 'keypoints', 'heatmap', 'hm'],
                'scores': ['output_scores', 'scores', 'score']
            },
            # fallback generic names
            'generic_heatmap': {
                'kps': ['heatmap', 'hm', 'output_0', 'output_2'],
                'scores': []
            },
            # merged suggestions from batch scanner (model_mappings_patch.json)
            'model': {
                'kps': ['output_0', 'output_1'],
                'scores': []
            },
            'face_detector': {
                'kps': ['output_0', 'output_1'],
                'scores': []
            },
            'hand_landmarks_detector': {
                'kps': ['output_0', 'output_1'],
                'scores': []
            },
            'pose_detection': {
                'kps': ['output_0', 'output_1'],
                'scores': []
            },
            'pose_landmarks_detector_full': {
                'kps': ['keypoints', 'pred', 'keypoints_output'],
                'scores': ['scores']
            },
            'pose_landmarks_detector_heavy': {
                'kps': ['keypoints', 'pred', 'keypoints_output'],
                'scores': ['scores']
            },
            'pose_landmarks_detector_lite': {
                'kps': ['keypoints', 'pred', 'keypoints_output'],
                'scores': ['scores']
            },
            'test_simple_model_fixed': {
                'kps': ['output_0', 'keypoints', 'heatmap'],
                'scores': []
            },
            'test_simple_model_fixed.quant': {
                'kps': ['output_0', 'keypoints', 'heatmap'],
                'scores': []
            }
        }
    # merge external mappings from repo config/model_mappings.json into the
    # in-file `model_output_map`. This persists batch-generated suggestions
    # into the adapter at runtime by normalizing keys (strip .onnx, lowercase)
    # and merging entries. It's implemented here as a safe best-effort merge
    # (won't raise on malformed files).
        try:
            cfg_path = os.path.join(os.getcwd(), 'config', 'model_mappings.json')
            if os.path.exists(cfg_path):
                try:
                    with open(cfg_path, 'r', encoding='utf-8') as _f:
                        _data = json.load(_f)
                    if isinstance(_data, dict):
                        for _k, _v in _data.items():
                            try:
                                nk = str(_k).lower()
                                if nk.endswith('.onnx'):
                                    nk = nk[:-5]
                                # if value is a dict with kps/scores keys, merge/override
                                if isinstance(_v, dict):
                                    self.model_output_map[nk] = _v
                            except Exception:
                                continue
                except Exception:
                    # don't let malformed JSON stop adapter init
                    pass
        except Exception:
            pass
            # lightweight debug log to help Streamlit logs show which model mappings
            # were merged at runtime (useful during development). Use logger instead
            try:
                logger = logging.getLogger(__name__)
                merged_keys = sorted(list(self.model_output_map.keys()))
                logger.info("PoseAdapter: loaded model_output_map entries=%d", len(merged_keys))
            except Exception:
                pass
    # NOTE: 'litehrnet' entry above was auto-approved by the mapping scanner
    # based on observed outputs (keypoints shape [1,17,2] + scores [1,17]).
    # It's safe to treat this model as producing 17 (x,y) keypoints with
    # optional scores. If you want to change the exact output names, edit
    # this table or add a new model key.

    def adapt_mediapipe(self, landmarks, img_w: int, img_h: int) -> Optional[np.ndarray]:
        """Convert MediaPipe pose landmarks into COCO-17 (17,3) array.

        landmarks: MediaPipe LandmarkList (results.pose_landmarks)
        returns np.ndarray shape (17,3) with (x_norm, y_norm, conf)
        """
        if landmarks is None or mp is None:
            return None
        # COCO-17 order: nose, left_eye, right_eye, left_ear, right_ear,
        # left_shoulder, right_shoulder, left_elbow, right_elbow,
        # left_wrist, right_wrist, left_hip, right_hip, left_knee,
        # right_knee, left_ankle, right_ankle
        mp_idx = mp.solutions.pose.PoseLandmark
        mapping = [
            mp_idx.NOSE,
            mp_idx.LEFT_EYE,
            mp_idx.RIGHT_EYE,
            mp_idx.LEFT_EAR,
            mp_idx.RIGHT_EAR,
            mp_idx.LEFT_SHOULDER,
            mp_idx.RIGHT_SHOULDER,
            mp_idx.LEFT_ELBOW,
            mp_idx.RIGHT_ELBOW,
            mp_idx.LEFT_WRIST,
            mp_idx.RIGHT_WRIST,
            mp_idx.LEFT_HIP,
            mp_idx.RIGHT_HIP,
            mp_idx.LEFT_KNEE,
            mp_idx.RIGHT_KNEE,
            mp_idx.LEFT_ANKLE,
            mp_idx.RIGHT_ANKLE,
        ]

        out = np.zeros((17, 3), dtype=np.float32)
        for i, m in enumerate(mapping):
            try:
                lm = landmarks.landmark[m]
                x = float(lm.x)
                y = float(lm.y)
                # prefer visibility then presence then 1.0
                conf = getattr(lm, 'visibility', None)
                if conf is None:
                    conf = getattr(lm, 'presence', None)
                if conf is None:
                    conf = 1.0
                out[i, 0] = x
                out[i, 1] = y
                out[i, 2] = float(conf)
            except Exception:
                out[i, :] = 0.0
        return out

    def adapt_keypoint_list(self, kps, img_w: int, img_h: int) -> Optional[np.ndarray]:
        """Adapt a generic keypoint list (list of [x,y] or [x,y,conf]) to COCO-17.

        This function is best-effort: if kps has 17 points, treat as COCO; if 33,
        try to sample a COCO subset using common indices. If points are in pixel
        coordinates (values >1), normalize by img_w/img_h.
        """
        if kps is None:
            return None
        arr = np.array(kps)
        if arr.ndim == 1:
            # single flattened; give up
            return None
        n = arr.shape[0]
        # determine whether coords are normalized
        sample_x = float(arr[0, 0])
        normalized = (sample_x <= 1.0)
        def _get_xyc(idx):
            try:
                row = arr[idx]
                if row.size >= 3:
                    x, y, c = float(row[0]), float(row[1]), float(row[2])
                elif row.size >= 2:
                    x, y = float(row[0]), float(row[1])
                    c = 1.0
                else:
                    return 0.0, 0.0, 0.0
                if not normalized:
                    x = x / float(img_w) if img_w else 0.0
                    y = y / float(img_h) if img_h else 0.0
                return x, y, float(c)
            except Exception:
                return 0.0, 0.0, 0.0

        if n == 17:
            out = np.zeros((17, 3), dtype=np.float32)
            for i in range(17):
                out[i] = _get_xyc(i)
            return out
        if n == 33:
            # map a subset of 33->17 using MediaPipe indices for COCO canonical locations
            # approximate mapping using common landmarks
            mp_to_coco = {
                0: 0,   # nose
                1: 1,   # left eye
                2: 2,   # right eye
                3: 3,   # left ear
                4: 4,   # right ear
                11: 5,  # left shoulder
                12: 6,  # right shoulder
                13: 7,  # left elbow
                14: 8,  # right elbow
                15: 9,  # left wrist
                16: 10, # right wrist
                23: 11, # left hip
                24: 12, # right hip
                25: 13, # left knee
                26: 14, # right knee
                27: 15, # left ankle
                28: 16, # right ankle
            }
            out = np.zeros((17, 3), dtype=np.float32)
            for src_idx, coco_idx in mp_to_coco.items():
                if src_idx < n:
                    out[coco_idx] = _get_xyc(src_idx)
            return out

        # fallback: try to use first 17 points
        if n > 17:
            out = np.zeros((17, 3), dtype=np.float32)
            for i in range(17):
                out[i] = _get_xyc(i)
            return out

        return None

    def adapt_onnx_raw(self, onnx_raw, img_w: int, img_h: int) -> Optional[np.ndarray]:
        """Attempt to interpret common ONNX outputs and adapt them to COCO-17.

        Handles shapes like:
        - (1, N*2) or (1, N*3) flattened
        - (1, N, 2) or (1, N, 3)
        - (N, 2) or (N, 3)
        - MoveNet-like outputs (1,17,3)
        """
        if onnx_raw is None:
            return None
        try:
            arr = None
            # onnx_raw may be list of arrays
            if isinstance(onnx_raw, list) or isinstance(onnx_raw, tuple):
                # try to pick the largest-array element
                cand = None
                max_size = 0
                for el in onnx_raw:
                    try:
                        a = np.array(el)
                        if a.size > max_size:
                            max_size = a.size
                            cand = a
                    except Exception:
                        continue
                arr = cand
            else:
                arr = np.array(onnx_raw)

            if arr is None:
                return None

            # flatten to handle (1, N*2) etc
            if arr.ndim == 1:
                # too ambiguous
                return None

            # common case: (1, N, 2/3) or (N, 2/3)
            if arr.ndim == 3 and arr.shape[0] == 1 and arr.shape[2] in (2, 3):
                n = arr.shape[1]
                flat = arr.reshape((n, arr.shape[2]))
                return self.adapt_keypoint_list(flat, img_w, img_h)
            # common heatmap case: (1, C, H, W) or (1, H, W, C)
            if arr.ndim == 4:
                # prefer channel-first (1,C,H,W)
                if arr.shape[0] == 1 and arr.shape[1] >= 1 and arr.shape[2] >= 1:
                    C = arr.shape[1]
                    H = arr.shape[2]
                    W = arr.shape[3]
                    # if channels look like keypoint channels, decode via soft-argmax
                    if C >= 8 and C <= 256:
                        kps = []
                        for c in range(min(C, 64)):
                            hm = np.array(arr[0, c, :, :], dtype=np.float32)
                            x, y, conf = self._soft_argmax_2d(hm)
                            # normalized coords
                            kps.append([x, y, conf])
                        kps = np.array(kps, dtype=np.float32)
                        # return first 17 if many
                        return self.adapt_keypoint_list(kps[:17], img_w, img_h)
                # support NHWC (1,H,W,C)
                if arr.shape[0] == 1 and arr.shape[-1] >= 1:
                    C = arr.shape[-1]
                    H = arr.shape[1]
                    W = arr.shape[2]
                    if C >= 8 and C <= 256:
                        kps = []
                        for c in range(min(C, 64)):
                            hm = np.array(arr[0, :, :, c], dtype=np.float32)
                            x, y, conf = self._soft_argmax_2d(hm)
                            kps.append([x, y, conf])
                        kps = np.array(kps, dtype=np.float32)
                        return self.adapt_keypoint_list(kps[:17], img_w, img_h)
            if arr.ndim == 2 and arr.shape[1] in (2, 3) and arr.shape[0] >= 17:
                return self.adapt_keypoint_list(arr, img_w, img_h)

            # flattened vectors like (1, 34) or (1, 51)
            if arr.ndim == 2 and arr.shape[0] == 1 and arr.size in (34, 51, 68, 102):
                flat = arr.flatten()
                if flat.size % 3 == 0:
                    n = flat.size // 3
                    pts = flat.reshape((n, 3))
                    return self.adapt_keypoint_list(pts, img_w, img_h)
                if flat.size % 2 == 0:
                    n = flat.size // 2
                    pts = flat.reshape((n, 2))
                    pts3 = np.concatenate([pts, np.ones((n, 1), dtype='float32')], axis=1)
                    return self.adapt_keypoint_list(pts3, img_w, img_h)

            # MoveNet-style: (1,17,3) or similar
            if arr.ndim == 3 and arr.shape[1] >= 17 and arr.shape[2] in (2, 3):
                # pick first 17
                sub = arr[0, :17, :]
                return self.adapt_keypoint_list(sub, img_w, img_h)

            # fallback: try to coerce first axis
            if arr.ndim >= 2 and arr.shape[0] == 1 and arr.shape[1] >= 34:
                flat = arr.flatten()
                try:
                    if flat.size % 3 == 0:
                        n = flat.size // 3
                        pts = flat.reshape((n, 3))
                        return self.adapt_keypoint_list(pts, img_w, img_h)
                except Exception:
                    pass

        except Exception:
            return None
        return None

    def _soft_argmax_2d(self, heatmap: np.ndarray) -> tuple:
        """
        Compute soft-argmax over a 2D heatmap. Returns (x_norm, y_norm, confidence)
        where x_norm, y_norm are in [0,1] relative to width/height.
        """
        try:
            hm = np.asarray(heatmap, dtype=np.float32)
            if hm.size == 0:
                return 0.0, 0.0, 0.0
            # stabilize and exponentiate
            hm = hm - np.max(hm)
            exp = np.exp(hm)
            s = np.sum(exp)
            if s <= 0:
                # fallback to argmax
                ind = np.argmax(hm)
                y, x = divmod(ind, hm.shape[1])
                conf = float(np.max(hm))
                return float(x) / float(hm.shape[1] - 1), float(y) / float(hm.shape[0] - 1), float(conf)
            prob = exp / s
            # compute expected coordinates
            H, W = hm.shape
            xs = np.linspace(0, 1, num=W, dtype=np.float32)
            ys = np.linspace(0, 1, num=H, dtype=np.float32)
            px = np.sum(np.sum(prob, axis=0) * xs)
            py = np.sum(np.sum(prob, axis=1) * ys)
            conf = float(np.max(hm))
            return float(px), float(py), float(conf)
        except Exception:
            return 0.0, 0.0, 0.0

    def _load_model_mappings(self, path: str = None):
        """Load optional per-model mapping overrides from config/model_mappings.json.

        Expected format: a dict mapping model identifier (lowercased basename or short key)
        to a mapping dict compatible with self.model_output_map entries.
        Example:
        {
            "litehrnet.onnx": { "kps": ["keypoints"], "scores": ["scores"] }
        }
        """
        p = path or os.path.join(os.getcwd(), 'config', 'model_mappings.json')
        if not os.path.exists(p):
            return
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return
            for k, v in data.items():
                try:
                    key = str(k).lower()
                    if isinstance(v, dict):
                        # merge/override entry
                        self.model_output_map[key] = v
                except Exception:
                    continue
        except Exception:
            return

    def detect_and_adapt(self, onnx_raw, img_w: int, img_h: int) -> Optional[np.ndarray]:
        """Convenience: try interpreted ONNX raw outputs first, then fall back to keypoint list.
        """
        # try raw onnx parsing
        k = self.adapt_onnx_raw(onnx_raw, img_w, img_h)
        if k is not None:
            return k
        # if onnx_raw is a list with a keypoints-like element, try to find it
        try:
            if isinstance(onnx_raw, (list, tuple)):
                for el in onnx_raw:
                    try:
                        a = np.array(el)
                        if a.ndim in (2, 3) and a.size >= 34:
                            cand = self.adapt_keypoint_list(a, img_w, img_h)
                            if cand is not None:
                                return cand
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    def adapt_named_onnx_outputs(self, model_name: str, outputs: dict, img_w: int = None, img_h: int = None) -> Optional[np.ndarray]:
        """
        Given a mapping of ONNX output name->ndarray (or list), try to find
        keypoint and score tensors using known per-model hints and adapt them
        to COCO-17 normalized format.

        outputs: dict-like mapping (name->array)
        model_name: short name like 'litehrnet' (case-insensitive)
        """
        if outputs is None:
            return None
        mn = (model_name or '').lower()
        hints = self.model_output_map.get(mn, None)
        # attempt to find explicit keys
        kps_arr = None
        scores_arr = None
        if isinstance(outputs, dict):
            if hints:
                # search candidate names in order
                for cand in hints.get('kps', []):
                    if cand in outputs:
                        try:
                            kps_arr = np.array(outputs[cand])
                            break
                        except Exception:
                            continue
                for cand in hints.get('scores', []):
                    if cand in outputs:
                        try:
                            scores_arr = np.array(outputs[cand])
                            break
                        except Exception:
                            continue
            # fallback: look for obvious shapes in outputs
            if kps_arr is None or (kps_arr is not None and kps_arr.size == 0):
                for name, val in outputs.items():
                    try:
                        a = np.array(val)
                        # (1,17,2) or (1,17,3)
                        if a.ndim == 3 and a.shape[1] >= 17 and a.shape[2] in (2,3):
                            kps_arr = a
                            break
                        # (1,17,2) represented as (17,2)
                        if a.ndim == 2 and a.shape[0] >= 17 and a.shape[1] in (2,3):
                            kps_arr = a
                            break
                        # flattened (1,34) etc
                        if a.ndim == 2 and a.shape[0] == 1 and a.size in (34,51,68,102,195,117):
                            kps_arr = a
                            break
                    except Exception:
                        continue
            # try find score arrays by 1D shape==17
            if scores_arr is None:
                for name, val in outputs.items():
                    try:
                        a = np.array(val)
                        if a.ndim == 2 and a.shape[1] == 17:
                            scores_arr = a
                            break
                        if a.ndim == 1 and a.shape[0] == 17:
                            scores_arr = a
                            break
                    except Exception:
                        continue

    # If we have keypoints array, adapt using existing helpers
        if kps_arr is not None:
            # normalize shapes like (1,17,2) -> (17,2)
            try:
                a = np.array(kps_arr)
                if a.ndim == 3 and a.shape[0] == 1:
                    a = a[0]
                # if a is (17,2) and we have scores arr, append scores
                if a.ndim == 2 and a.shape[1] == 2:
                    if scores_arr is not None:
                        s = np.array(scores_arr)
                        if s.ndim == 2 and s.shape[0] == 1:
                            s = s[0]
                        if s.ndim == 1 and s.shape[0] >= 17:
                            s = s[:17]
                            pts3 = np.concatenate([a[:17], s.reshape((17,1))], axis=1)
                            return self.adapt_keypoint_list(pts3, img_w, img_h)
                    # no scores, assume conf=1
                    pts3 = np.concatenate([a[:17], np.ones((17,1),dtype='float32')], axis=1)
                    return self.adapt_keypoint_list(pts3, img_w, img_h)
                # if already (17,3)
                if a.ndim == 2 and a.shape[1] in (3,4):
                    return self.adapt_keypoint_list(a[:17], img_w, img_h)
                # if flattened vector
                if a.ndim == 1 or (a.ndim == 2 and a.shape[0] == 1):
                    flat = a.flatten()
                    if flat.size % 3 == 0:
                        n = flat.size // 3
                        pts = flat.reshape((n,3))
                        return self.adapt_keypoint_list(pts, img_w, img_h)
                    if flat.size % 2 == 0:
                        n = flat.size // 2
                        pts = flat.reshape((n,2))
                        pts3 = np.concatenate([pts, np.ones((n,1),dtype='float32')], axis=1)
                        return self.adapt_keypoint_list(pts3, img_w, img_h)
            except Exception:
                return None
        # debug: if we didn't find explicit kps_arr, print available output names
        if kps_arr is None:
            try:
                logger = logging.getLogger(__name__)
                outs = list(outputs.keys()) if isinstance(outputs, dict) else []
                logger.debug("adapt_named_onnx_outputs('%s') found outputs: %s%s", mn, outs[:8], '...' if len(outs) > 8 else '')
            except Exception:
                pass

        # If no explicit kps_arr but heatmap-like outputs exist in outputs dict, try soft-argmax decoding
        try:
            if isinstance(outputs, dict):
                for name, val in outputs.items():
                    try:
                        a = np.array(val)
                        # channel-first heatmap (1,C,H,W)
                        if a.ndim == 4 and a.shape[0] == 1 and a.shape[1] >= 8 and a.shape[1] <= self.max_heatmap_ch:
                            C = min(a.shape[1], self.max_heatmap_ch)
                            kps = []
                            for c in range(C):
                                hm = np.array(a[0, c, :, :], dtype=np.float32)
                                x, y, conf = self._soft_argmax_2d(hm)
                                kps.append([x, y, conf])
                            kps = np.array(kps, dtype=np.float32)
                            return self.adapt_keypoint_list(kps[:17], img_w, img_h)
                        # NHWC heatmap (1,H,W,C)
                        if a.ndim == 4 and a.shape[0] == 1 and a.shape[-1] >= 8 and a.shape[-1] <= self.max_heatmap_ch:
                            C = min(a.shape[-1], self.max_heatmap_ch)
                            kps = []
                            for c in range(C):
                                hm = np.array(a[0, :, :, c], dtype=np.float32)
                                x, y, conf = self._soft_argmax_2d(hm)
                                kps.append([x, y, conf])
                            kps = np.array(kps, dtype=np.float32)
                            return self.adapt_keypoint_list(kps[:17], img_w, img_h)
                    except Exception:
                        continue
        except Exception:
            pass

        return None

    def temporal_smooth(self, seq: np.ndarray, alpha: float = 0.6) -> np.ndarray:
        """Simple exponential moving average smoothing across time.

        seq: T x K x 3
        returns smoothed seq of same shape
        """
        if seq is None or len(seq) == 0:
            return seq
        out = np.copy(seq).astype('float32')
        for t in range(1, out.shape[0]):
            out[t] = alpha * out[t] + (1.0 - alpha) * out[t-1]
        return out

    def resample_time_series(self, seq: np.ndarray, src_fps: float, target_fps: float = 25.0) -> np.ndarray:
        """Resample a time-series of keypoints from src_fps -> target_fps using linear interpolation.

        seq: T x K x 3 (x,y,conf) where x,y normalized [0,1]
        returns: T2 x K x 3
        """
        if seq is None:
            return None
        try:
            seq = np.asarray(seq, dtype='float32')
            if seq.ndim != 3:
                return None
            T, K, C = seq.shape
            if T <= 1 or src_fps <= 0 or target_fps <= 0:
                return seq
            duration = float(T) / float(src_fps)
            t_src = np.linspace(0.0, duration, num=T)
            T_target = max(1, int(round(duration * float(target_fps))))
            t_target = np.linspace(0.0, duration, num=T_target)
            out = np.zeros((T_target, K, C), dtype='float32')
            # interpolate x,y,conf independently per joint
            for j in range(K):
                for c in range(C):
                    vals = seq[:, j, c]
                    # handle NaNs by filling with zeros
                    try:
                        out[:, j, c] = np.interp(t_target, t_src, vals)
                    except Exception:
                        out[:, j, c] = 0.0
            return out
        except Exception:
            return None
