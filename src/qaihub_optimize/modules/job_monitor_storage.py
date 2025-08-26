"""Simple persistence for job monitor using SQLite.

Provides save_jobs and load_jobs helpers. Stores jobs as JSON blob.
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any

DB_PATH = Path(__file__).parent / '.job_monitor.db'
TABLE_NAME = 'jobs'

def _get_conn(db_path: Path = None):
    p = db_path or DB_PATH
    conn = sqlite3.connect(str(p))
    return conn

def _ensure_table(conn):
    cur = conn.cursor()
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY,
        ts INTEGER,
        jobs_json TEXT
    )
    """)
    conn.commit()

def save_jobs(jobs: Dict[str, Any], db_path: Path = None) -> bool:
    try:
        conn = _get_conn(db_path)
        _ensure_table(conn)
        cur = conn.cursor()
        jobs_json = json.dumps(jobs, default=str)
        cur.execute(f"INSERT INTO {TABLE_NAME} (ts, jobs_json) VALUES (strftime('%s','now'), ?)", (jobs_json,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"⚠️ job_monitor_storage.save_jobs failed: {e}")
        return False

def load_jobs(db_path: Path = None) -> Dict[str, Any]:
    try:
        conn = _get_conn(db_path)
        _ensure_table(conn)
        cur = conn.cursor()
        cur.execute(f"SELECT jobs_json FROM {TABLE_NAME} ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return {}
    except Exception as e:
        print(f"⚠️ job_monitor_storage.load_jobs failed: {e}")
        return {}
