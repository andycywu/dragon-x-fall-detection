#!/usr/bin/env python3
import qai_hub as hub
import time

print("🔍 檢查QAI Hub編譯狀態...")

job_ids = ['jp8m66nq5', 'jgkqoo1vg', 'j5qrzznep', 'jgl2ood2p', 'j56zrrxng', 'jp31xxdmg']

for job_id in job_ids:
    try:
        job = hub.get_job(job_id)
        print(f"📊 Job {job_id}: {job.status}")
        if hasattr(job, 'target_device'):
            print(f"   設備: {job.target_device.name}")
        print(f"   Dashboard: https://app.aihub.qualcomm.com/jobs/{job_id}")
    except Exception as e:
        print(f"❌ Job {job_id} 檢查失敗: {e}")
    
    time.sleep(1)

print("✅ 狀態檢查完成！")
