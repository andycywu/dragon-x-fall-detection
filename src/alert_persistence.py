"""Alert persistence helpers used by the Streamlit demo.

This small module centralizes the SQLite helpers so tests can import them
without depending on Streamlit UI internals.
"""
import os
import sqlite3
import time
import json


def ensure_alerts_db():
    try:
        # use repo-local elderly_data directory
        db_dir = os.path.join(os.getcwd(), 'elderly_data')
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'alerts.db')
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL,
                user_id TEXT,
                score REAL,
                engine TEXT,
                status TEXT,
                dismissed_by TEXT,
                dismissed_at REAL
            )
        ''')
        conn.commit()
        conn.close()
        return db_path
    except Exception:
        return None


def persist_alert_event(ts: float, user_id: str = None, score: float = None, engine: str = None, status: str = 'triggered', dismissed_by: str = None, dismissed_at: float = None):
    db_path = ensure_alerts_db()
    if not db_path:
        return False

    payload = (float(ts), user_id, float(score) if score is not None else None, engine, status, dismissed_by, float(dismissed_at) if dismissed_at is not None else None)
    attempts = 0
    last_exc = None
    while attempts < 2:
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('''INSERT INTO alerts (ts, user_id, score, engine, status, dismissed_by, dismissed_at) VALUES (?,?,?,?,?,?,?)''', payload)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            last_exc = e
            attempts += 1
            try:
                time.sleep(0.05)
            except Exception:
                pass

    # final fallback: append an append-only log for offline inspection
    try:
        fb = os.path.join(os.getcwd(), 'elderly_data', 'alerts_fallback.log')
        with open(fb, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': ts, 'user_id': user_id, 'score': score, 'engine': engine, 'status': status, 'dismissed_by': dismissed_by, 'dismissed_at': dismissed_at, 'error': str(last_exc)}) + '\n')
    except Exception:
        pass
    return False
