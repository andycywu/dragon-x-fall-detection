"""Small utilities for alert-related interactions (webhook send etc).

Contains a testable function send_rescue_webhook(url, payload, timeout=5)
that prefers requests if available and falls back to urllib.
Returns a tuple: (sent: bool, result_msg: Optional[str])
"""
import json
import logging

try:
    import requests
except Exception:
    requests = None
    import urllib.request as _urllib_request
    import urllib.error as _urllib_error


def send_rescue_webhook(url: str, payload: dict, timeout: int = 5):
    try:
        if requests:
            r = requests.post(url, json=payload, timeout=timeout)
            sent = 200 <= getattr(r, 'status_code', 0) < 300
            return sent, f'http_status={getattr(r, "status_code", None)}'
        else:
            req = _urllib_request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            resp = _urllib_request.urlopen(req, timeout=timeout)
            code = resp.getcode() if hasattr(resp, 'getcode') else None
            sent = True if code and 200 <= code < 300 else False
            return sent, f'http_status={code}'
    except Exception as e:
        try:
            return False, str(e)
        except Exception:
            logging.exception('Webhook send failed with non-string error')
            return False, 'unknown error'


def safe_identify_user(predictor, frame):
    """Call predictor.identify_user(frame) if available, return user_id or None.

    This helper swallows exceptions so callers don't crash when predictor is absent
    or buggy. Returns str user_id or None.
    """
    if predictor is None:
        return None
    try:
        fn = getattr(predictor, 'identify_user', None)
        if not fn:
            return None
        try:
            uid = fn(frame)
            return uid
        except TypeError:
            # maybe identify_user expects no args
            try:
                return fn()
            except Exception:
                return None
        except Exception:
            return None
    except Exception:
        return None
