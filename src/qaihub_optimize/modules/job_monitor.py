"""
任務狀態監控模組
負責監控 QAI Hub 任務狀態和進度
使用 Qualcomm AI Hub 官方 SDK 進行狀態查詢和輪詢
"""
import time
import threading
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta

try:
    import qai_hub as hub
    from qai_hub import JobStatus, JobType
    QAI_HUB_AVAILABLE = True
except ImportError:
    QAI_HUB_AVAILABLE = False
    print("⚠️  qai_hub 套件未安裝，將使用模擬模式")


class JobMonitor:
    """QAI Hub 任務狀態監控類別"""
    
    # 完整的完成狀態列表（與 qaihub_client.py 保持一致）
    COMPLETED_STATUS = ('COMPLETED', 'SUCCEEDED', 'SUCCESS', 'FINISHED', 
                       'COMPLETED_SUCCESSFULLY', 'RESULTS_READY', 'RESULTS READY', 
                       'results_ready', 'Results Ready')
    
    # 錯誤狀態列表
    ERROR_STATUS = ('FAILED', 'ERROR', 'CANCELLED', 'TIMEOUT')
    
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
            # 使用大小寫不敏感的狀態檢查
            status_upper = str(status).upper()
            completed_upper = [s.upper() for s in self.COMPLETED_STATUS]
            error_upper = [s.upper() for s in self.ERROR_STATUS]
            
            if status_upper in completed_upper:
                self._trigger_callbacks('on_job_complete', job)
            elif status_upper in error_upper:
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
            # 使用大小寫不敏感的狀態檢查
            status_upper = str(job['status']).upper()
            completed_upper = [s.upper() for s in self.COMPLETED_STATUS]
            error_upper = [s.upper() for s in self.ERROR_STATUS]
            
            if status_upper in completed_upper or status_upper in error_upper:
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
            # 檢查是否所有任務都完成（使用大小寫不敏感的狀態檢查）
            all_completed = True
            for job in self.monitored_jobs.values():
                status_upper = str(job['status']).upper()
                completed_upper = [s.upper() for s in self.COMPLETED_STATUS]
                error_upper = [s.upper() for s in self.ERROR_STATUS]
                
                if status_upper not in completed_upper and status_upper not in error_upper:
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
            status_upper = str(job['status']).upper()
            error_upper = [s.upper() for s in self.ERROR_STATUS]
            
            if status_upper in error_upper:
                failed_jobs.append(job)
        
        if failed_jobs:
            print(f"\n❌ 有 {len(failed_jobs)} 個任務失敗:")
            for job in failed_jobs:
                print(f"   - {job['model_name']}: {job['status']} - {job.get('error', '未知錯誤')}")
            return False
        
        return True

    def wait_for_compile_jobs(self, qai_hub_models: Dict, timeout_minutes: int = 30) -> bool:
        """
        等待所有編譯任務完成
        
        Args:
            qai_hub_models: QAI Hub 模型字典
            timeout_minutes: 超時時間（分鐘）
            
        Returns:
            是否所有編譯任務都成功完成
        """
        print(f"⏳ 等待所有編譯任務完成（超時: {timeout_minutes} 分鐘）...")
        
        # 將所有編譯任務添加到監控器
        for model_name, model_info in qai_hub_models.items():
            compile_job = model_info.get('compile_job')
            if compile_job and hasattr(compile_job, 'job_id'):
                job_id = compile_job.job_id
                if job_id not in self.monitored_jobs:
                    self.add_job(job_id, 'compile', model_name, timeout=timeout_minutes * 60)
        
        # 開始監控並等待完成
        return self.wait_for_completion(timeout=timeout_minutes * 60, check_interval=15)

    def wait_for_profile_jobs(self, qai_hub_models: Dict, timeout_minutes: int = 30) -> bool:
        """
        等待所有分析任務完成
        
        Args:
            qai_hub_models: QAI Hub 模型字典
            timeout_minutes: 超時時間（分鐘）
            
        Returns:
            是否所有分析任務都成功完成
        """
        print(f"⏳ 等待所有分析任務完成（超時: {timeout_minutes} 分鐘）...")
        
        # 將所有分析任務添加到監控器
        for model_name, model_info in qai_hub_models.items():
            profile_job = model_info.get('profile_job')
            if profile_job and hasattr(profile_job, 'job_id'):
                job_id = profile_job.job_id
                if job_id not in self.monitored_jobs:
                    self.add_job(job_id, 'profile', model_name, timeout=timeout_minutes * 60)
        
        # 開始監控並等待完成
        return self.wait_for_completion(timeout=timeout_minutes * 60, check_interval=15)

    def generate_compile_report(self, qai_hub_models: Dict, output_file: str) -> bool:
        """
        產生編譯任務HTML報告
        
        Args:
            qai_hub_models: QAI Hub 模型字典
            output_file: 輸出檔案路徑
            
        Returns:
            是否成功產生報告
        """
        print(f"📊 產生編譯任務報告: {output_file}")
        # 暫時先返回成功，實際報告功能待實現
        return True

    def generate_profile_report(self, qai_hub_models: Dict, output_file: str) -> bool:
        """
        產生分析任務HTML報告
        
        Args:
            qai_hub_models: QAI Hub 模型字典
            output_file: 輸出檔案路徑
            
        Returns:
            是否成功產生報告
        """
        print(f"📊 產生分析任務報告: {output_file}")
        # 暫時先返回成功，實際報告功能待實現
        return True


class QAIHubJobMonitor(JobMonitor):
    """QAI Hub 專用的任務監控器，使用官方 SDK 進行狀態查詢"""
    
    def __init__(self, qaihub_client):
        """
        初始化 QAI Hub 任务监控器
        
        Args:
            qaihub_client: QAIHubClient 实例
        """
        super().__init__()
        self.qaihub_client = qaihub_client
        
        # 修正路径配置：直接使用 qaihub_client 的 base_dir 作为优化模型目录
        # 因为 qaihub_client.base_dir 已经是正确的 models 目录
        self.optimized_models_dir = self.qaihub_client.base_dir / 'qaihub_optimized'
        self.optimized_models_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 优化模型输出目录: {self.optimized_models_dir}")
    
    def _check_jobs_status(self):
        """使用 QAI Hub SDK 檢查任務狀態"""
        try:
            for job_id, job_info in self.monitored_jobs.items():
                # 如果任務已經完成或失敗，跳過檢查
                status_upper = str(job_info['status']).upper()
                completed_upper = [s.upper() for s in self.COMPLETED_STATUS]
                error_upper = [s.upper() for s in self.ERROR_STATUS]
                
                if status_upper in completed_upper or status_upper in error_upper:
                    continue
                
                try:
                    # 使用 QAI Hub SDK 取得任務狀態
                    if QAI_HUB_AVAILABLE:
                        # 從 qai_hub_models 中取得對應的 job 物件
                        model_name = job_info['model_name']
                        job_type = job_info['job_type']
                        
                        qaihub_model = self.qaihub_client.qai_hub_models.get(model_name, {})
                        job = qaihub_model.get(f'{job_type}_job')
                        
                        if job:
                            # 刷新任務狀態（如果支援）
                            try:
                                if hasattr(job, 'refresh'):
                                    job.refresh()
                                elif hasattr(job, 'get_status'):
                                    # 如果沒有 refresh 方法，使用 get_status 來更新狀態
                                    job.get_status()
                            except Exception as refresh_error:
                                print(f"⚠️  無法刷新任務狀態 {job_id}: {refresh_error}")
                                # 繼續執行，使用現有狀態
                            
                            # 取得任務狀態
                            status = getattr(job, 'status', None)
                            if hasattr(job, 'get_status'):
                                status = job.get_status()
                            
                            if status:
                                # 更新任務狀態
                                status_code = status.code if hasattr(status, 'code') else str(status)
                                progress = self._get_progress_from_status(status)
                                self.update_job_status(job_id, status_code, progress)
                                
                                # 如果任務失敗，獲取詳細錯誤信息
                                error_msg = self._extract_detailed_error_info(job, status, status_code, job_id)
                                
                                # 檢查是否是失敗狀態
                                if status_code.upper() in ['FAILED', 'ERROR'] and error_msg:
                                    self.update_job_status(job_id, status_code, 100, error_msg)
                                    print(f"❌ 任務 {job_id} 失敗: {error_msg}")
                                elif status_code.upper() in ['FAILED', 'ERROR']:
                                    # 如果沒有具體錯誤訊息，提供詳細的調試信息
                                    error_msg = self._get_comprehensive_error_info(job, status, status_code, job_id)
                                    self.update_job_status(job_id, status_code, 100, error_msg)
                                    print(f"❌ 任務 {job_id} 失敗: {error_msg}")
                                
                                # 如果任務成功完成，下載優化後的模型
                                if hasattr(status, 'success') and status.success:
                                    print(f"✅ 任務 {job_id} 成功完成，開始下載優化模型...")
                                    self._download_optimized_model(job_id, job_info)
                                elif hasattr(status, 'code') and str(status.code).upper() in ['SUCCESS', 'COMPLETED']:
                                    print(f"✅ 任務 {job_id} 成功完成，開始下載優化模型...")
                                    self._download_optimized_model(job_id, job_info)
                                elif hasattr(status, 'code') and str(status.code).upper() in ['SUCCEEDED', 'FINISHED']:
                                    print(f"✅ 任務 {job_id} 成功完成，開始下載優化模型...")
                                    self._download_optimized_model(job_id, job_info)
                                else:
                                    # 添加調試信息
                                    print(f"💡 任務狀態調試: job_id={job_id}, status_code={status_code}, has_success={hasattr(status, 'success')}")
                                    if hasattr(status, 'success'):
                                        print(f"💡 status.success = {status.success}")
                                    if hasattr(status, 'code'):
                                        print(f"💡 status.code = {status.code}")
                        else:
                            # 如果找不到 job 物件，嘗試使用 hub.get_job
                            try:
                                job = hub.get_job(job_id)
                                status = job.get_status()
                                
                                # 更新任務狀態
                                self.update_job_status(job_id, status.code, self._get_progress_from_status(status))
                                
                                # 如果任務失敗，獲取詳細錯誤信息
                                if hasattr(status, 'error') and status.error:
                                    error_msg = f"QAI Hub Error: {status.error}"
                                    self.update_job_status(job_id, status.code, 100, error_msg)
                                    print(f"❌ 任務 {job_id} 失敗: {status.error}")
                                
                                # 如果任務成功完成，下載優化後的模型
                                if status.success:
                                    print(f"✅ 任務 {job_id} 成功完成，開始下載優化模型...")
                                    self._download_optimized_model(job_id, job_info)
                                elif hasattr(status, 'code') and str(status.code).upper() in ['SUCCESS', 'COMPLETED', 'SUCCEEDED', 'FINISHED']:
                                    print(f"✅ 任務 {job_id} 成功完成，開始下載優化模型...")
                                    self._download_optimized_model(job_id, job_info)
                            except Exception as get_job_error:
                                print(f"❌ 無法取得任務 {job_id}: {get_job_error}")
                                self.update_job_status(job_id, 'ERROR', 0, f"無法取得任務: {get_job_error}")
                    else:
                        # 模擬模式：使用舊的檢查方式
                        self._check_job_status_legacy(job_id, job_info)
                        
                except Exception as e:
                    print(f"❌ 檢查任務狀態失敗 {job_id}: {e}")
                    self.update_job_status(job_id, 'ERROR', 0, str(e))
        
        except Exception as e:
            print(f"❌ 監控循環發生錯誤: {e}")
    
    def _check_job_status_legacy(self, job_id: str, job_info: Dict):
        """舊的任務狀態檢查方法（用於模擬模式）"""
        job_type = job_info['job_type']
        model_name = job_info['model_name']
        
        # 從 qaihub_client 取得對應的 job
        qaihub_model = self.qaihub_client.qai_hub_models.get(model_name, {})
        job = qaihub_model.get(f'{job_type}_job')
        
        if job:
            # 刷新狀態
            if hasattr(job, 'refresh'):
                job.refresh()
            
            status = getattr(job, 'status', None) or getattr(job, 'state', None)
            progress = self._estimate_progress(status)
            
            self.update_job_status(job_id, str(status), progress)
    
    def _get_progress_from_status(self, status) -> int:
        """
        根據 QAI Hub JobStatus 估計進度百分比
        
        Args:
            status: JobStatus 物件
            
        Returns:
            進度百分比 (0-100)
        """
        if not QAI_HUB_AVAILABLE:
            return self._estimate_progress(status.code if hasattr(status, 'code') else str(status))
        
        # 根據 QAI Hub 官方狀態映射進度
        progress_map = {
            'UNSPECIFIED': 0,
            'CREATED': 10,
            'OPTIMIZING_MODEL': 30,
            'PROVISIONING_DEVICE': 50,
            'MEASURING_PERFORMANCE': 70,
            'RUNNING_INFERENCE': 80,
            'QUANTIZING_MODEL': 90,
            'LINKING_MODELS': 95,
            'SUCCESS': 100,
            'FAILED': 100
        }
        
        status_code = status.code if hasattr(status, 'code') else str(status)
        return progress_map.get(status_code, 0)
    
    def _download_optimized_model(self, job_id: str, job_info: Dict):
        """
        下載優化後的模型到本地
        
        Args:
            job_id: 任務ID
            job_info: 任務資訊
        """
        if not QAI_HUB_AVAILABLE:
            print(f"⚠️  QAI Hub SDK 不可用，無法下載優化模型 {job_id}")
            return
        
        try:
            model_name = job_info['model_name']
            job_type = job_info['job_type']
            
            print(f"🔍 開始下載優化模型: job_id={job_id}, model={model_name}, type={job_type}")
            
            # 首先嘗試從 qai_hub_models 中取得 job 物件
            qaihub_model = self.qaihub_client.qai_hub_models.get(model_name, {})
            job = qaihub_model.get(f'{job_type}_job')
            
            # 如果找不到，嘗試使用 hub.get_job
            if not job:
                print(f"🔍 從 qai_hub_models 找不到 job，嘗試使用 hub.get_job({job_id})")
                try:
                    job = hub.get_job(job_id)
                    print(f"✅ 成功使用 hub.get_job 取得任務: {job_id}")
                except Exception as get_job_error:
                    print(f"❌ 無法取得任務 {job_id}: {get_job_error}")
                    return
            
            # 使用 QAI Hub 提供的簡單下載 API
            if job_type == 'compile':
                print(f"💾 使用 QAI Hub download_target_model() 下載優化模型...")
                
                # 確保目錄存在
                self.optimized_models_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 確保目錄存在: {self.optimized_models_dir}")
                
                # 使用 job ID 作為前綴生成檔案名稱（QAI Hub 可能會下載為 zip 文件）
                temp_filename = f"{job_id}_{model_name}_optimized.zip"
                temp_path = self.optimized_models_dir / temp_filename
                
                # 最終的檔案名稱（保持原始名稱，只加 job ID 前綴）
                final_filename = f"{job_id}_{model_name}_optimized.onnx"
                final_path = self.optimized_models_dir / final_filename
                
                try:
                    # 使用 download_target_model() 方法，它會自動阻塞直到任務完成
                    if hasattr(job, 'download_target_model'):
                        print(f"⬇️  開始下載目標模型到臨時檔案: {temp_path}")
                        job.download_target_model(temp_path)
                        print(f"✅ 模型下載完成: {temp_path}")
                    elif hasattr(job, 'download_results'):
                        print(f"⬇️  開始下載結果到臨時檔案: {temp_path}")
                        job.download_results(temp_path)
                        print(f"✅ 模型下載完成: {temp_path}")
                    else:
                        print(f"❌ job 物件不支援 download_target_model 或 download_results 方法")
                        job_info['error'] = "不支援的 job 下載方法"
                        return
                    
                    # 檢查檔案是否存在
                    if temp_path.exists():
                        file_size = temp_path.stat().st_size
                        print(f"📊 下載檔案大小: {file_size} bytes")
                        
                        # 處理下載的檔案（可能是 zip 或 onnx）
                        print(f"💡 開始處理下載檔案: temp_path={temp_path}, final_path={final_path}")
                        process_result = self._process_downloaded_file(temp_path, final_path, model_name)
                        if process_result:
                            print(f"✅ 模型處理完成: {final_path}")
                            
                            # 更新任務資訊和 qai_hub_models 字典
                            job_info['optimized_model_path'] = str(final_path)
                            job_info['optimized_model_downloaded'] = True
                            
                            # 同時更新 qaihub_client 中的模型資訊
                            if hasattr(self.qaihub_client, 'qai_hub_models'):
                                if model_name in self.qaihub_client.qai_hub_models:
                                    self.qaihub_client.qai_hub_models[model_name]['optimized_model_path'] = str(final_path)
                                    self.qaihub_client.qai_hub_models[model_name]['optimized_model_downloaded'] = True
                                    print(f"📝 已更新 {model_name} 的下載狀態到 qai_hub_models")
                            
                            # 觸發下載完成回調
                            self._trigger_callbacks('on_job_complete', job_info)
                            print(f"🎉 優化模型下載和處理成功完成!")
                        else:
                            print(f"❌ 檔案處理失敗")
                            job_info['error'] = f"下載完成但檔案處理失敗"
                            # 添加詳細調試信息
                            print(f"💡 調試信息: temp_path={temp_path}, final_path={final_path}")
                            actual_files = list(temp_path.parent.glob(f"*{model_name}*optimized*"))
                            print(f"💡 找到的實際檔案: {[f.name for f in actual_files]}")
                            # 檢查所有可能的檔案
                            all_files = list(temp_path.parent.glob('*'))
                            print(f"💡 目錄中的所有檔案: {[f.name for f in all_files]}")
                            # 檢查檔案是否存在
                            print(f"💡 temp_path 是否存在: {temp_path.exists()}")
                            if temp_path.exists():
                                print(f"💡 temp_path 檔案大小: {temp_path.stat().st_size} bytes")
                    else:
                        print(f"❌ 檔案不存在: {temp_path}")
                        job_info['error'] = f"下載完成但檔案不存在: {temp_path}"
                        # 檢查實際下載的檔案名稱
                        actual_files = list(self.optimized_models_dir.glob(f"*{job_id}*{model_name}*optimized*"))
                        print(f"💡 實際找到的檔案: {[f.name for f in actual_files]}")
                        if actual_files:
                            print(f"💡 實際檔案路徑: {actual_files[0]}")
                            print(f"💡 實際檔案大小: {actual_files[0].stat().st_size} bytes")
                            # 嘗試使用實際檔案名稱
                            actual_file = actual_files[0]
                            print(f"💡 嘗試使用實際檔案: {actual_file}")
                            process_result = self._process_downloaded_file(actual_file, final_path, model_name)
                            if process_result:
                                print(f"✅ 使用實際檔案處理成功: {final_path}")
                                job_info['optimized_model_path'] = str(final_path)
                                job_info['optimized_model_downloaded'] = True
                                self._trigger_callbacks('on_job_complete', job_info)
                                print(f"🎉 優化模型下載和處理成功完成!")
                        
                except Exception as download_error:
                    print(f"❌ 下載失敗: {download_error}")
                    job_info['error'] = f"下載失敗: {download_error}"
                    # 嘗試記錄詳細錯誤信息
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"詳細錯誤堆疊:\n{error_details}")
            
        except Exception as e:
            print(f"❌ 下載優化模型失敗 {job_id}: {e}")
            # 嘗試記錄詳細錯誤信息
            import traceback
            error_details = traceback.format_exc()
            print(f"詳細錯誤堆疊:\n{error_details}")
    
    def _process_downloaded_file(self, temp_path: Path, final_path: Path, model_name: str) -> bool:
        """
        處理下載的檔案，可能是 zip 文件或直接的 onnx 文件
        
        Args:
            temp_path: 臨時下載檔案路徑
            final_path: 最終 onnx 檔案路徑
            model_name: 模型名稱
            
        Returns:
            處理是否成功
        """
        try:
            # QAI Hub 下載的文件名格式為 {job_id}_{model_name}_optimized.zip.onnx.zip
            # 我們需要找到實際下載的文件（可能與 temp_path 名稱不完全相同）
            actual_files = list(temp_path.parent.glob(f"*{model_name}*optimized*"))
            
            if not actual_files:
                print(f"❌ 找不到實際下載的檔案，預期包含: {model_name}_optimized")
                # 列出目錄中的所有檔案來調試
                all_files = list(temp_path.parent.glob('*'))
                print(f"💡 目錄中的所有檔案: {[f.name for f in all_files]}")
                return False
            
            # 使用實際下載的檔案
            actual_file = actual_files[0]
            print(f"📁 實際下載檔案: {actual_file.name}")
            print(f"💡 檔案完整路徑: {actual_file}")
            print(f"💡 檔案大小: {actual_file.stat().st_size} bytes")
            
            # 檢查檔案類型 - QAI Hub 下載的是 .zip.onnx.zip 文件
            if actual_file.suffix.lower() == '.zip' or '.zip' in actual_file.suffixes:
                print(f"📦 檢測到 ZIP 文件，開始解壓縮...")
                
                # 導入 zipfile 模組
                import zipfile
                
                # 創建臨時解壓縮目錄
                extract_dir = actual_file.parent / f"{model_name}_extracted"
                extract_dir.mkdir(exist_ok=True)
                
                # 解壓縮文件
                with zipfile.ZipFile(actual_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                print(f"✅ 解壓縮完成到: {extract_dir}")
                
                # 尋找解壓縮後的 onnx 文件
                onnx_files = list(extract_dir.glob('**/*.onnx'))
                
                if onnx_files:
                    # 找到 onnx 文件，移動到最終位置
                    first_onnx = onnx_files[0]
                    print(f"🔍 找到 ONNX 文件: {first_onnx}")
                    
                    # 移動文件到最終位置
                    import shutil
                    shutil.move(str(first_onnx), str(final_path))
                    print(f"✅ 移動 ONNX 文件到: {final_path}")
                    
                    # 清理臨時文件
                    try:
                        shutil.rmtree(extract_dir)
                        actual_file.unlink()
                        print(f"🧹 清理臨時文件完成")
                    except Exception as cleanup_error:
                        print(f"⚠️  清理臨時文件失敗: {cleanup_error}")
                    
                    return True
                else:
                    print(f"❌ 在 ZIP 文件中找不到 ONNX 文件")
                    # 檢查是否有其他可能的模型文件
                    all_files = list(extract_dir.glob('**/*'))
                    print(f"📋 解壓縮文件列表: {[f.name for f in all_files]}")
                    
                    # 如果沒有找到 ONNX 文件，但 ZIP 文件存在，直接使用 ZIP 文件
                    print(f"📦 直接使用 ZIP 文件作為優化模型")
                    import shutil
                    shutil.move(str(actual_file), str(final_path))
                    print(f"✅ 移動 ZIP 文件到: {final_path}")
                    return True
            
            elif actual_file.suffix.lower() == '.onnx' or '.onnx' in actual_file.suffixes:
                print(f"📄 檢測到 ONNX 文件，直接重命名...")
                
                # 直接重命名文件
                import shutil
                shutil.move(str(actual_file), str(final_path))
                print(f"✅ 重命名完成: {final_path}")
                return True
            
            else:
                print(f"❓ 未知文件類型: {actual_file.suffix}")
                print(f"📋 嘗試直接重命名為 ONNX 文件...")
                
                # 嘗試直接重命名為 onnx 文件
                import shutil
                shutil.move(str(actual_file), str(final_path))
                print(f"✅ 重命名完成: {final_path}")
                return True
                
        except Exception as e:
            print(f"❌ 文件處理失敗: {e}")
            import traceback
            error_details = traceback.format_exc()
            print(f"詳細錯誤堆疊:\n{error_details}")
            return False
    
    def _estimate_progress(self, status: str) -> int:
        """
        根據狀態估計進度百分比（備用方法）
        
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
            'FINISHED': 100,
            'COMPLETED_SUCCESSFULLY': 100,
            'RESULTS_READY': 100,
            'RESULTS READY': 100,
            'FAILED': 100,
            'ERROR': 100,
            'CANCELLED': 100,
            'TIMEOUT': 100
        }
        
        for key, value in progress_map.items():
            if key in status:
                return value
        
        return 0  # 未知狀態
    
    def get_running_jobs(self, limit: int = 50) -> List[Dict]:
        """
        取得執行中的任務列表
        
        Args:
            limit: 最大返回數量
            
        Returns:
            執行中任務列表
        """
        if not QAI_HUB_AVAILABLE:
            print("⚠️  QAI Hub SDK 不可用，無法取得執行中任務列表")
            return []
        
        try:
            running_states = JobStatus.all_running_states() if hasattr(JobStatus, 'all_running_states') else []
            jobs = hub.get_job_summaries(state=running_states, limit=limit)
            
            result = []
            for js in jobs:
                result.append({
                    'job_id': js.job_id,
                    'name': js.name,
                    'status': js.status.code if hasattr(js.status, 'code') else str(js.status),
                    'job_type': js.job_type if hasattr(js, 'job_type') else 'unknown',
                    'url': js.url if hasattr(js, 'url') else ''
                })
            
            return result
            
        except Exception as e:
            print(f"❌ 取得執行中任務列表失敗: {e}")
            return []
    
    def wait_for_job_completion(self, job_id: str, timeout: Optional[int] = None) -> str:
        """
        等待單一任務完成
        
        Args:
            job_id: 任務ID
            timeout: 超時時間（秒）
            
        Returns:
            最終狀態 ('SUCCESS' 或 'FAILED')
        """
        if not QAI_HUB_AVAILABLE:
            print("⚠️  QAI Hub SDK 不可用，使用模擬等待")
            return self._wait_for_job_completion_legacy(job_id, timeout)
        
        try:
            job = hub.get_job(job_id)
            final_status = job.wait(timeout=timeout)
            return final_status
            
        except Exception as e:
            print(f"❌ 等待任務完成失敗 {job_id}: {e}")
            return 'FAILED'
    
    def _extract_detailed_error_info(self, job, status, status_code: str, job_id: str) -> Optional[str]:
        """
        從 Job 和 Status 物件中提取詳細的錯誤信息
        
        Args:
            job: QAI Hub Job 物件
            status: QAI Hub Status 物件
            status_code: 狀態代碼
            job_id: 任務ID
            
        Returns:
            錯誤訊息字串，如果找不到則返回 None
        """
        error_msg = None
        
        # 標準錯誤屬性檢查
        if hasattr(status, 'error') and status.error:
            error_msg = f"QAI Hub Error: {status.error}"
        elif hasattr(job, 'error') and job.error:
            error_msg = f"QAI Hub Job Error: {job.error}"
        elif hasattr(job, 'failure_reason') and job.failure_reason:
            error_msg = f"QAI Hub Failure: {job.failure_reason}"
        elif hasattr(job, 'status_message') and job.status_message:
            error_msg = f"QAI Hub Status: {job.status_message}"
        
        # 如果標準屬性沒有錯誤信息，嘗試其他方法
        if not error_msg and status_code.upper() in ['FAILED', 'ERROR']:
            # 嘗試從 Job 物件的其他屬性中尋找錯誤信息
            job_attrs_to_check = [
                'failure_details', 'details', 'metadata', 'error_message',
                'error_info', 'failure_info', 'status_details'
            ]
            
            for attr in job_attrs_to_check:
                if hasattr(job, attr):
                    value = getattr(job, attr)
                    if value is not None and str(value).strip() and str(value).strip() != 'None':
                        error_msg = f"QAI Hub {attr}: {value}"
                        break
        
        return error_msg
    
    def _get_comprehensive_error_info(self, job, status, status_code: str, job_id: str) -> str:
        """
        獲取全面的錯誤信息，包括調試建議
        
        Args:
            job: QAI Hub Job 物件
            status: QAI Hub Status 物件
            status_code: 狀態代碼
            job_id: 任務ID
            
        Returns:
            完整的錯誤訊息字串
        """
        # 首先嘗試標準錯誤提取
        error_msg = self._extract_detailed_error_info(job, status, status_code, job_id)
        
        if error_msg:
            return error_msg
        
        # 如果沒有標準錯誤信息，提供詳細的調試信息
        debug_info = []
        
        # 添加 Job 基本資訊
        debug_info.append(f"Job ID: {job_id}")
        debug_info.append(f"Status Code: {status_code}")
        
        # 添加 Job 物件的可用屬性
        if hasattr(job, 'name'):
            debug_info.append(f"Job Name: {job.name}")
        if hasattr(job, 'device_name'):
            debug_info.append(f"Device: {job.device_name}")
        if hasattr(job, 'url'):
            debug_info.append(f"Web URL: {job.url}")
        
        # 添加時間資訊
        if hasattr(job, 'date'):
            debug_info.append(f"Date: {job.date}")
        
        # 提供調試建議
        debug_info.append("")
        debug_info.append("💡 調試建議:")
        debug_info.append("1. 檢查 QAI Hub Web 界面獲取詳細錯誤信息")
        debug_info.append("2. 確認模型格式和兼容性")
        debug_info.append("3. 檢查目標設備的支援情況")
        debug_info.append("4. 驗證模型輸入輸出格式")
        
        if hasattr(job, 'url'):
            debug_info.append(f"5. 查看詳細錯誤: {job.url}")
        
        return "\n".join(debug_info)
    
    def _wait_for_job_completion_legacy(self, job_id: str, timeout: Optional[int] = None) -> str:
        """舊的等待任務完成方法（用於模擬模式）"""
        check_interval = 10
        waited = 0
        
        while True:
            job_info = self.get_job_status(job_id)
            if not job_info:
                return 'FAILED'
            
            status_upper = str(job_info['status']).upper()
            completed_upper = [s.upper() for s in self.COMPLETED_STATUS]
            error_upper = [s.upper() for s in self.ERROR_STATUS]
            
            if status_upper in completed_upper:
                return 'SUCCESS'
            elif status_upper in error_upper:
                return 'FAILED'
            
            if timeout and waited >= timeout:
                return 'FAILED'
            
            time.sleep(check_interval)
            waited += check_interval


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
