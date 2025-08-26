import pytest
from qaihub_optimize.modules.job_monitor import JobMonitor


def test_status_normalization_completed():
    jm = JobMonitor()
    jm.add_job('j1', 'compile', 'm1', timeout=10)
    jm.update_job_status('j1', 'Results Ready')
    completed = jm.get_jobs_by_status('COMPLETED')
    assert any(j['job_id'] == 'j1' for j in completed)


def test_status_normalization_failed():
    jm = JobMonitor()
    jm.add_job('j2', 'compile', 'm2', timeout=10)
    jm.update_job_status('j2', 'failed')
    failed = jm.get_jobs_by_status('FAILED')
    assert any(j['job_id'] == 'j2' for j in failed)


def test_status_case_insensitive():
    jm = JobMonitor()
    jm.add_job('j3', 'profile', 'm3', timeout=10)
    jm.update_job_status('j3', 'sUcCeEdEd')
    comp = jm.get_jobs_by_status('COMPLETED')
    assert any(j['job_id'] == 'j3' for j in comp)
