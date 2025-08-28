import sys
import os
import importlib
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import alert_utils


def test_send_rescue_webhook_requests_success(monkeypatch):
    class DummyResp:
        status_code = 201
    def fake_post(url, json=None, timeout=5):
        return DummyResp()
    monkeypatch.setattr(alert_utils, 'requests', types.SimpleNamespace(post=fake_post))
    sent, msg = alert_utils.send_rescue_webhook('http://example.com', {'a':1})
    assert sent is True
    assert 'http_status=201' in msg


def test_send_rescue_webhook_requests_failure(monkeypatch):
    def fake_post(url, json=None, timeout=5):
        raise Exception('boom')
    monkeypatch.setattr(alert_utils, 'requests', types.SimpleNamespace(post=fake_post))
    sent, msg = alert_utils.send_rescue_webhook('http://example.com', {'a':1})
    assert sent is False
    assert 'boom' in msg


def test_send_rescue_webhook_urllib(monkeypatch):
    # simulate no requests available
    monkeypatch.setattr(alert_utils, 'requests', None)
    class DummyResp:
        def __init__(self, code):
            self._code = code
        def getcode(self):
            return self._code
    def fake_urlopen(req, timeout=5):
        return DummyResp(200)
    # patch the names used inside alert_utils for urllib; module defines _urllib_request in our implementation
    # ensure _urllib_request exists on module so code path can call it
    monkeypatch.setattr(alert_utils, '_urllib_request', types.SimpleNamespace(Request=lambda *a, **k: None, urlopen=fake_urlopen), raising=False)
    monkeypatch.setattr(alert_utils, '_urllib_error', types.SimpleNamespace(), raising=False)
    sent, msg = alert_utils.send_rescue_webhook('http://example.com', {'a':1})
    assert sent is True
    assert 'http_status=200' in msg
