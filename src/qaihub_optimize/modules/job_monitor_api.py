"""簡易 FastAPI endpoint 提供 job monitor 的狀態與列表。"""
from fastapi import FastAPI, HTTPException
from typing import Any

from .job_monitor import get_job_monitor

app = FastAPI(title="Job Monitor API")

@app.get('/')
def root():
    return {"status":"ok", "service":"job_monitor"}

@app.get('/jobs')
def list_jobs():
    jm = get_job_monitor()
    return jm.get_all_jobs()

@app.get('/status')
def status_report():
    jm = get_job_monitor()
    return {"report": jm.generate_status_report()}

@app.post('/add')
def add_job(job_id: str, job_type: str = 'compile', model_name: str = '', timeout: int = 1800):
    jm = get_job_monitor()
    jm.add_job(job_id, job_type, model_name, timeout=timeout)
    return {"added": job_id}
