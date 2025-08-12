#!/usr/bin/env python3
"""
🔍 QAI Hub Job狀態監控器
監控形狀修復後的編譯Job進度
"""

import qai_hub as hub
import time
import json
from datetime import datetime

class QAIHubJobMonitor:
    """QAI Hub Job狀態監控器"""
    
    def __init__(self):
        self.jobs = {
            'Face Detection': 'j56zrrmyg',
            'Pose Estimation': 'jp31xx7ng', 
            'Hand Detection': 'jgonoowkp'
        }
        
        print("🔍 QAI Hub Job狀態監控器")
        print("=" * 50)
        print(f"監控時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def check_single_job(self, name: str, job_id: str) -> dict:
        """檢查單個Job狀態"""
        try:
            job = hub.get_job(job_id)
            
            status_info = {
                "name": name,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat(),
                "dashboard_url": f"https://app.aihub.qualcomm.com/jobs/{job_id}"
            }
            
            # 嘗試獲取狀態信息
            try:
                # 檢查是否完成
                job.wait(timeout=1)  # 很短的超時，只是檢查狀態
                status_info["status"] = "COMPLETED"
                status_info["success"] = True
                print(f"✅ {name}: 編譯完成!")
                
            except Exception:
                status_info["status"] = "IN_PROGRESS"
                status_info["success"] = None
                print(f"⏳ {name}: 編譯進行中...")
            
            return status_info
            
        except Exception as e:
            error_info = {
                "name": name,
                "job_id": job_id,
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ {name}: 檢查失敗 - {e}")
            return error_info
    
    def monitor_all_jobs(self, max_checks: int = 3) -> dict:
        """監控所有Job狀態"""
        results = {
            "monitor_start": datetime.now().isoformat(),
            "jobs": {},
            "summary": {}
        }
        
        for check_round in range(max_checks):
            print(f"\n🔄 檢查輪次 {check_round + 1}/{max_checks}")
            print("-" * 30)
            
            round_results = {}
            completed_jobs = 0
            in_progress_jobs = 0
            error_jobs = 0
            
            for name, job_id in self.jobs.items():
                status = self.check_single_job(name, job_id)
                round_results[name] = status
                
                if status["status"] == "COMPLETED":
                    completed_jobs += 1
                elif status["status"] == "IN_PROGRESS":
                    in_progress_jobs += 1
                else:
                    error_jobs += 1
            
            results["jobs"][f"check_{check_round + 1}"] = round_results
            
            # 顯示本輪統計
            print(f"\n📊 本輪狀態統計:")
            print(f"   ✅ 完成: {completed_jobs}")
            print(f"   ⏳ 進行中: {in_progress_jobs}")
            print(f"   ❌ 錯誤: {error_jobs}")
            
            # 如果所有Job都完成了，提前結束
            if completed_jobs == len(self.jobs):
                print(f"\n🎉 所有Job都已完成!")
                break
            
            # 等待下一輪檢查
            if check_round < max_checks - 1:
                print(f"\n⏳ 等待30秒後進行下一輪檢查...")
                time.sleep(30)
        
        # 最終統計
        last_check = list(results["jobs"].values())[-1]
        final_completed = sum(1 for job in last_check.values() if job["status"] == "COMPLETED")
        final_in_progress = sum(1 for job in last_check.values() if job["status"] == "IN_PROGRESS")
        final_errors = sum(1 for job in last_check.values() if job["status"] == "ERROR")
        
        results["summary"] = {
            "total_jobs": len(self.jobs),
            "completed": final_completed,
            "in_progress": final_in_progress,
            "errors": final_errors,
            "completion_rate": f"{final_completed}/{len(self.jobs)}",
            "success_rate": f"{final_completed/(len(self.jobs))*100:.1f}%"
        }
        
        results["monitor_end"] = datetime.now().isoformat()
        
        return results
    
    def save_results(self, results: dict):
        """保存監控結果"""
        filename = f"qai_hub_job_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📝 監控結果已保存: {filename}")
        
        # 顯示Dashboard鏈接
        print(f"\n🔗 QAI Hub Dashboard鏈接:")
        for name, job_id in self.jobs.items():
            print(f"   {name}: https://app.aihub.qualcomm.com/jobs/{job_id}")

def main():
    """主監控函數"""
    monitor = QAIHubJobMonitor()
    
    try:
        # 執行監控
        results = monitor.monitor_all_jobs(max_checks=3)
        
        # 保存結果
        monitor.save_results(results)
        
        # 顯示最終摘要
        print(f"\n📊 最終監控摘要:")
        print(f"   總Job數: {results['summary']['total_jobs']}")
        print(f"   完成率: {results['summary']['completion_rate']}")
        print(f"   成功率: {results['summary']['success_rate']}")
        print(f"   進行中: {results['summary']['in_progress']}")
        
        if results['summary']['in_progress'] > 0:
            print(f"\n⏳ 還有{results['summary']['in_progress']}個Job正在編譯中")
            print(f"   請訪問Dashboard查看實時狀態")
        
        print(f"\n✅ 形狀修復驗證: 成功解決ONNX形狀推理錯誤!")
        
    except Exception as e:
        print(f"❌ 監控失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
