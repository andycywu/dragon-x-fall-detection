import os
import time
import sqlite3
import importlib
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import alert_persistence
ensure_alerts_db = alert_persistence.ensure_alerts_db
persist_alert_event = alert_persistence.persist_alert_event


def test_persist_and_read(tmp_path, monkeypatch):
    # run in isolated tmp cwd so we don't touch repo data
    monkeypatch.chdir(str(tmp_path))
    db = ensure_alerts_db()
    assert db is not None and os.path.isfile(db)

    ts = time.time()
    ok = persist_alert_event(ts=ts, user_id='test_user', score=0.9, engine='unittest', status='triggered')
    assert ok

    # read back
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT ts, user_id, score, engine, status FROM alerts ORDER BY id DESC LIMIT 1')
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert abs(row[0] - ts) < 2.0
    assert row[1] == 'test_user'
    assert abs(row[2] - 0.9) < 1e-6
    assert row[3] == 'unittest'
    assert row[4] == 'triggered'
