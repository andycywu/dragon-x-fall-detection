from typing import List, Optional


def compute_delta_from_history(angle_history: List[float]) -> float:
    """Return absolute difference between last two angles in history, or 0.0 if unavailable."""
    try:
        if not angle_history or len(angle_history) < 2:
            return 0.0
        return abs(float(angle_history[-1]) - float(angle_history[-2]))
    except Exception:
        return 0.0


def compute_fall_decision(prob: Optional[float], angle: Optional[float], conf: float, angle_thresh: float, confidence_threshold: float, delta: float = 0.0, fall_delta_thresh: float = 40.0, min_conf_for_action: float = 0.25) -> bool:
    """Heuristic fall decision used by the demo.

    Logic:
      - If model provides `prob`, use prob >= confidence_threshold
      - Else, fall if (angle > angle_thresh AND conf >= confidence_threshold)
        OR (delta > fall_delta_thresh AND conf >= min_conf_for_action)

    Returns True for fall, False otherwise.
    """
    try:
        if prob is not None:
            try:
                return float(prob) >= float(confidence_threshold)
            except Exception:
                return False

        # No prob: require either angle-based threshold OR sudden delta-based trigger
        a = None
        if angle is not None:
            try:
                a = float(angle)
            except Exception:
                a = None

        if a is not None and a > float(angle_thresh) and float(conf) >= float(confidence_threshold):
            return True

        if float(delta) > float(fall_delta_thresh) and float(conf) >= float(min_conf_for_action):
            return True

        return False
    except Exception:
        return False
