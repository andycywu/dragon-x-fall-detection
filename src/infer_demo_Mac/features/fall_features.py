"""Minimal fall feature extractor PoC.

Provides functions to compute COM (hip-based) vertical velocity/acceleration and
torso angle from a sequence of adapted keypoints (shape: T x 17 x 3).
"""
from typing import Tuple, Optional
import numpy as np


def hips_center(kps: np.ndarray) -> Tuple[float, float]:
    """Return (x,y) of hip center from a single frame adapted kps (17,3).
    If hips missing, fallback to mean of available lower-body joints.
    """
    try:
        l_hip = kps[11][:2]
        r_hip = kps[12][:2]
        return float((l_hip[0] + r_hip[0]) / 2.0), float((l_hip[1] + r_hip[1]) / 2.0)
    except Exception:
        valid = []
        for idx in [11,12,13,14,15,16]:
            try:
                v = kps[idx][:2]
                valid.append(v)
            except Exception:
                continue
        if not valid:
            return 0.0, 0.0
        arr = np.array(valid)
        return float(arr[:,0].mean()), float(arr[:,1].mean())


def torso_angle_from_kps(kps: np.ndarray) -> Optional[float]:
    """Compute torso angle (degrees) using shoulder and hip centers.
    Returns angle from vertical in degrees (0 = upright, larger = leaning).
    """
    try:
        ls = kps[5][:2]
        rs = kps[6][:2]
        lhip = kps[11][:2]
        rhip = kps[12][:2]
        shoulder = np.array([(ls[0]+rs[0])/2.0, (ls[1]+rs[1])/2.0])
        hip = np.array([(lhip[0]+rhip[0])/2.0, (lhip[1]+rhip[1])/2.0])
        torso = shoulder - hip
        vert = np.array([0.0, -1.0])
        cos = np.dot(torso, vert) / (np.linalg.norm(torso) * np.linalg.norm(vert) + 1e-8)
        cos = np.clip(cos, -1.0, 1.0)
        return float(np.degrees(np.arccos(cos)))
    except Exception:
        return None


def extract_basic_features(seq_kps: np.ndarray, fps: float = 25.0) -> dict:
    """Given seq_kps: T x 17 x 3 (normalized coords), compute basic features.

    Returns dict with:
      - com_v: vertical velocity time-series (pixels normalized units / s)
      - com_a: vertical acceleration time-series
      - torso_angles: per-frame torso angles
      - summary: simple summary stats
    """
    T = seq_kps.shape[0]
    ys = []
    torso_angles = []
    for t in range(T):
        cx, cy = hips_center(seq_kps[t])
        ys.append(cy)
        ta = torso_angle_from_kps(seq_kps[t])
        torso_angles.append(ta if ta is not None else 0.0)
    ys = np.array(ys, dtype=np.float32)
    dt = 1.0 / float(fps)
    # velocity (dy/dt) — positive downward if y increases downward
    v = np.gradient(ys, dt)
    a = np.gradient(v, dt)
    summary = {
        'com_y_start': float(ys[0]) if T>0 else 0.0,
        'com_y_min': float(np.min(ys)) if T>0 else 0.0,
        'com_y_max': float(np.max(ys)) if T>0 else 0.0,
        'max_v': float(np.max(np.abs(v))) if T>0 else 0.0,
        'max_a': float(np.max(np.abs(a))) if T>0 else 0.0,
        'torso_angle_mean': float(np.mean(torso_angles)) if T>0 else 0.0,
        'torso_angle_max': float(np.max(torso_angles)) if T>0 else 0.0,
    }
    return {'com_v': v, 'com_a': a, 'torso_angles': np.array(torso_angles), 'summary': summary}
