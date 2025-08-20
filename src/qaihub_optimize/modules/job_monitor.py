"""
任務狀態監控模組
負責監控 QAI Hub 任務狀態和進度
"""
import time
import threading
import sys
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta


class JobMonitor:
    """QAI Hub 任務狀態監控類別"""
    
    def __init__(self):
        """初始化任務監控器"""
        self.monitored_jobs = {}
        self.is_monitoring = False
        self.monitor_thread = None
        self.callbacks = {
            'on_job_start': [],
            'on_job_progress': [],
            'on_job_complete': [],
            'on_job_error': [],
            'on_timeout': []
        }
    
    def add_job(self, job_id: str, job_type: str, model_name: str, 
                timeout: int = 1800, metadata: Optional[Dict] = None):
        """
        新增要監控的任務
        
        Args:
            job_id: 任務ID
            job_type: 任務類型 ('compile', 'profile')
            model_name: 模型名稱
            timeout: 超時時間（秒）
            metadata: 額外元數據
        """
        self.monitored_jobs[job_id] = {
            'job_id': job_id,
            'job_type': job_type,
            'model_name': model_name,
            'status': 'PENDING',
            'start_time': datetime.now(),
            'timeout': timeout,
            'last_check': None,
            'progress': 0,
            'metadata': metadata or {},
            'error': None
        }
        
        # 觸發任務開始回調
        self._trigger_callbacks('on_job_start', self.monitored_jobs[job_id])
    
    def remove_job(self, job_id: str):
        """移除監控的任務"""
        if job_id in self.monitored_jobs:
            del self.monitored_jobs[job_id]
    
    def update_job_status(self, job_id: str, status: str, progress: int = 0, 
                         error: Optional[str] = None):
        """
        更新任務狀態
        
        Args:
            job_id: 任務ID
            status: 狀態
            progress: 進度百分比 (0-100)
            error: 錯誤訊息
        """
        if job_id not in self.monitored_jobs:
            return
        
        job = self.monitored_jobs[job_id]
        old_status = job['status']
        job['status'] = status
        job['progress'] = progress
        job['last_check'] = datetime.now()
        
        if error:
            job['error'] = error
        
        # 觸發進度回調
        self._trigger_callbacks('on_job_progress', job)
        
        # 檢查狀態變化
        if old_status != status:
            if status in ['COMPLETED', 'SUCCEEDED', 'SUCCESS']:
                self._trigger_callbacks('on_job_complete', job)
            elif status in ['FAILED', 'ERROR', 'CANCELLED']:
                self._trigger_callbacks('on_job_error', job)
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """取得任務狀態"""
        return self.monitored_jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, Dict]:
        """取得所有監控中的任務"""
        return self.monitored_jobs.copy()
    
    def get_jobs_by_status(self, status: str) -> List[Dict]:
        """根據狀態篩選任務"""
        return [job for job in self.monitored_jobs.values() if job['status'] == status]
    
    def get_jobs_by_type(self, job_type: str) -> List[Dict]:
        """根據類型篩選任務"""
        return [job for job in self.monitored_jobs.values() if job['job_type'] == job_type]
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        註冊回調函數
        
        Args:
            event_type: 事件類型 ('on_job_start', 'on_job_progress', 'on_job_complete', 'on_job_error', 'on_timeout')
            callback: 回調函數
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type: str, job_data: Dict):
        """觸發回調函數"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(job_data)
            except Exception as e:
                print(f"❌ 回調函數執行失敗: {e}")
    
    def start_monitoring(self, interval: int = 10):
        """
        開始監控任務
        
        Args:
            interval: 檢查間隔（秒）
        """
        if self.is_monitoring:
            print("⚠️ 監控已經在執行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        print("✅ 開始監控任務狀態...")
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        print("⏹️ 停止監控任務狀態")
    
    def _monitor_loop(self, interval: int):
        """監控循環"""
        while self.is_monitoring:
            try:
                self._check_jobs_status()
                self._check_timeouts()
                time.sleep(interval)
            except Exception as e:
                print(f"❌ 監控循環發生錯誤: {e}")
                time.sleep(interval)  # 繼續執行
    
    def _check_jobs_status(self):
        """檢查任務狀態（需要子類別實作）"""
        # 這個方法應該由具體的實作來覆寫，例如使用 QAI Hub API 查詢狀態
        pass
    
    def _check_timeouts(self):
        """檢查超時任務"""
        current_time = datetime.now()
        timed_out_jobs = []
        
        for job_id, job in self.monitored_jobs.items():
            if job['status'] in ['COMPLETED', 'FAILED', 'ERROR', 'CANCELLED']:
                continue
            
            elapsed = (current_time - job['start_time']).total_seconds()
            if elapsed > job['timeout']:
                job['status'] = 'TIMEOUT'
                job['error'] = f"任務超時 ({elapsed:.0f}秒 > {job['timeout']}秒)"
                timed_out_jobs.append(job)
        
        for job in timed_out_jobs:
            self._trigger_callbacks('on_timeout', job)
    
    def generate_status_report(self) -> str:
        """
        產生狀態報告
        
        Returns:
            狀態報告文字
        """
        report_lines = []
        current_time = datetime.now()
        
        report_lines.append(f"📊 任務狀態報告 - {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 60)
        
        # 按類型分組
        compile_jobs = self.get_jobs_by_type('compile')
        profile_jobs = self.get_jobs_by_type('profile')
        
        if compile_jobs:
            report_lines.append("\n🛠️ 編譯任務:")
            report_lines.append("-" * 40)
            for job in compile_jobs:
                elapsed = (current_time - job['start_time']).total_seconds()
                report_lines.append(
                    f"  {job['model_name']}: {job['status']} "
                    f"(進度: {job['progress']}%, 耗時: {elapsed:.0f}秒)"
                )
        
        if profile_jobs:
            report_lines.append("\n📈 分析任務:")
            report_lines.append("-" * 40)
            for job in profile_jobs:
                elapsed = (current_time - job['start_time']).total_seconds()
                report_lines.append(
                    f"  {job['model_name']}: {job['status']} "
                    f"(進度: {job['progress']}%, 耗時: {elapsed:.0f}秒)"
                )
        
        # 統計資訊
        total_jobs = len(self.monitored_jobs)
        completed = len(self.get_jobs_by_status('COMPLETED'))
        failed = len(self.get_jobs_by_status('FAILED')) + len(self.get_jobs_by_status('ERROR'))
        pending = len(self.get_jobs_by_status('PENDING')) + len(self.get_jobs_by_status('RUNNING'))
        
        report_lines.append("\n📈 統計資訊:")
        report_lines.append("-" * 40)
        report_lines.append(f"  總任務數: {total_jobs}")
        report_lines.append(f"  已完成: {completed}")
        report_lines.append(f"  失敗: {failed}")
        report_lines.append(f"  進行中: {pending}")
        
        if total_jobs > 0:
            success_rate = (completed / total_jobs) * 100
            report_lines.append(f"  成功率: {success_rate:.1f}%")
        
        return "\n".join(report_lines)
    
    def print_status(self):
        """打印當前狀態"""
        print(self.generate_status_report())
    
    def wait_for_completion(self, timeout: Optional[int] = None, 
                          check_interval: int = 10) -> bool:
        """
        等待所有任務完成
        
        Args:
            timeout: 總超時時間（秒）
            check_interval: 檢查間隔（秒）
            
        Returns:
            是否所有任務都成功完成
        """
        start_time = time.time()
        
        if not self.is_monitoring:
            self.start_monitoring(check_interval)
        
        print("⏳ 等待所有任務完成...")
        
        while True:
            # 檢查是否所有任務都完成
            all_completed = True
            for job in self.monitored_jobs.values():
                if job['status'] not in ['COMPLETED', 'FAILED', 'ERROR', 'CANCELLED', 'TIMEOUT']:
                    all_completed = False
                    break
            
            if all_completed:
                break
            
            # 檢查總超時
            if timeout and (time.time() - start_time) > timeout:
                print("⚠️ 等待超時，強制結束")
                break
            
            # 打印當前狀態
            self.print_status()
            time.sleep(check_interval)
        
        # 最終狀態報告
        print("\n🎯 任務完成最終狀態:")
        self.print_status()
        
        # 檢查是否有失敗的任務
        failed_jobs = []
        for job in self.monitored_jobs.values():
            if job['status'] in ['FAILED', 'ERROR', 'CANCELLED', 'TIMEOUT']:
                failed_jobs.append(job)
        
        if failed_jobs:
            print(f"\n❌ 有 {len(failed_jobs)} 個任務失敗:")
            for job in failed_jobs:
                print(f"   - {job['model_name']}: {job['status']} - {job.get('error', '未知錯誤')}")
            return False
        
        return True


class QAIHubJobMonitor(JobMonitor):
    """QAI Hub 專用的任務監控器"""
    
    def __init__(self, qaihub_client):
        """
        初始化 QAI Hub 任務監控器
        
        Args:
            qaihub_client: QAIHubClient 實例
        """
        super().__init__()
        self.qaihub_client = qaihub_client
    
    def _check_jobs_status(self):
        """檢查 QAI Hub 任務狀態"""
        try:
            for job_id, job_info in self.monitored_jobs.items():
                if job_info['status'] in ['COMPLETED', 'FAILED', 'ERROR', 'CANCELLED']:
                    continue
                
                # 根據任務類型取得對應的 job 物件
                job_type = job_info['job_type']
                model_name = job_info['model_name']
                
                # 從 qaihub_client 取得對應的 job
                qaihub_model = self.qaihub_client.qai_hub_models.get(model_name, {})
                job = qaihub_model.get(f'{job_type}_job')
                
                if job:
                    try:
                        # 刷新狀態
                        if hasattr(job, 'refresh'):
                            job.refresh()
                        
                        status = getattr(job, 'status', None) or getattr(job, 'state', None)
                        progress = self._estimate_progress(status)
                        
                        self.update_job_status(job_id, str(status), progress)
                        
                    except Exception as e:
                        print(f"❌ 檢查任務狀態失敗 {job_id}: {e}")
                        self.update_job_status(job_id, 'ERROR', 0, str(e))
        
        except Exception as e:
            print(f"❌ 監控循環發生錯誤: {e}")
    
    def _estimate_progress(self, status: str) -> int:
        """
        根據狀態估計進度百分比
        
        Args:
            status: 任務狀態
            
        Returns:
            進度百分比 (0-100)
        """
        status = str(status).upper()
        
        progress_map = {
            'PENDING': 0,
            'QUEUED': 10,
            'RUNNING': 50,
            'PROCESSING': 70,
            'COMPLETED': 100,
            'SUCCEEDED': 100,
            'SUCCESS': 100,
            'FAILED': 100,
            'ERROR': 100,
            'CANCELLED': 100
        }
        
        for key, value in progress_map.items():
            if key in status:
                return value
        
        return 0  # 未知狀態


# 單例模式實例
_job_monitor_instance = None

def get_job_monitor(qaihub_client=None) -> JobMonitor:
    """
    取得任務監控器實例（單例模式）
    
    Args:
        qaihub_client: QAIHubClient 實例（可選）
        
    Returns:
        JobMonitor 實例
    """
    global _job_monitor_instance
    if _job_monitor_instance is None:
        if qaihub_client:
            _job_monitor_instance = QAIHubJobMonitor(qaihub_client)
        else:
            _job_monitor_instance = JobMonitor()
    return _job_monitor_instance
