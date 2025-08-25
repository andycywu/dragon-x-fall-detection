"""
QAI Hub API 操作封裝模組
負責處理 QAI Hub 的 API 操作，包括模型上傳、任務提交、狀態監控等
"""
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import sys

try:
    from qai_hub.client import Device
except ImportError:
    print("警告: qai_hub 套件未安裝，部分功能可能無法使用")


class QAIHubClient:
    """QAI Hub API 操作封裝類別"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化 QAI Hub 客戶端
        
        Args:
            base_dir: 基礎目錄路徑，預設為當前目錄
        """
        self.base_dir = base_dir or Path.cwd()
        self.target_device = None
        self.qai_hub_models = {}
        self._initialize_device()
    
    def _initialize_device(self) -> bool:
        """初始化目標裝置"""
        try:
            from qai_hub.client import Device
            # 優先從環境變數讀取目標裝置設定
            target_device_name = os.getenv('TARGET_DEVICE', 'Snapdragon X Elite CRD')
            
            # 優先嘗試設定環境變數指定的裝置
            try:
                self.target_device = Device(target_device_name)
                print(f"✅ 目標裝置設定為: {self.target_device.name} (來自環境變數)")
                return True
            except Exception as e:
                print(f"⚠️  無法設定環境變數指定的裝置 '{target_device_name}': {e}")
            
            # 備用方案：嘗試設定 Snapdragon X Elite CRD
            try:
                self.target_device = Device("Snapdragon X Elite CRD")
                print(f"✅ 目標裝置設定為: {self.target_device.name} (備用方案)")
                return True
            except Exception as e:
                print(f"⚠️  無法設定 Snapdragon X Elite CRD: {e}")
            
            # 嘗試取得可用裝置 - 使用不同的方法
            try:
                # 方法1: 嘗試使用 hub.get_devices() (官方推薦方法)
                import qai_hub as hub
                devices = hub.get_devices()
            except Exception:
                # 方法2: 如果 hub.get_devices() 失敗，嘗試使用 Device.get_available_devices()
                try:
                    devices = Device.get_available_devices()
                except AttributeError:
                    # 方法3: 如果 get_available_devices 不存在，嘗試其他方法
                    try:
                        # 嘗試使用已知的裝置名稱
                        devices = [Device("Samsung Galaxy S23")]
                    except:
                        devices = []
            
            if devices:
                self.target_device = devices[0]  # 使用第一個可用裝置
                print(f"✅ 目標裝置設定為: {self.target_device.name}")
                return True
            else:
                print("❌ 找不到可用裝置，使用預設裝置")
                # 嘗試建立一個預設裝置
                try:
                    self.target_device = Device("Default Device")
                    return True
                except:
                    print("❌ 無法建立預設裝置")
                    return False
        except Exception as e:
            print(f"❌ 初始化裝置失敗: {e}")
            # 建立一個模擬裝置物件來避免後續錯誤
            class MockDevice:
                def __init__(self):
                    self.name = "Mock Device"
                    self.attributes = ["framework:onnx", "framework:tflite"]
            
            self.target_device = MockDevice()
            print("⚠️  使用模擬裝置繼續執行")
            return True
    
    def load_models(self, source: str, model_dir: str, ext: str) -> Dict[str, Any]:
        """
        載入模型檔案
        
        Args:
            source: 模型來源類型 ('onnx', 'tflite', 'dlc')
            model_dir: 模型目錄名稱
            ext: 檔案副檔名
            
        Returns:
            載入的模型資訊字典
        """
        # 檢查 base_dir 是否已經是 models 目錄
        if self.base_dir.name == 'models':
            models_dir = self.base_dir / model_dir
        else:
            models_dir = self.base_dir / 'models' / model_dir
            
        if not models_dir.exists():
            raise FileNotFoundError(f"找不到模型目錄: {models_dir}")
        
        model_files = list(models_dir.glob(f'*{ext}'))
        if not model_files:
            print(f"❌ 在 {models_dir} 中找不到 {ext} 檔案")
            return {}
        
        loaded_models = {}
        for model_file in model_files:
            model_name = model_file.stem
            if not model_name or model_name.strip() == '':
                model_name = f"model_{model_file.name}"
            loaded_models[model_name] = {
                'model_path': model_file,
                'source': source,
                'loaded': True,
                'model_dir': model_dir
            }
        
        print(f"✅ 載入 {len(loaded_models)} 個 {source.upper()} 模型")
        self.qai_hub_models.update(loaded_models)
        return loaded_models
    
    def upload_models(self) -> bool:
        """
        上傳模型到 QAI Hub
        
        Returns:
            上傳是否成功
        """
        try:
            import qai_hub as hub
            from qai_hub.client import Dataset
            
            uploaded_count = 0
            for model_name, model_info in self.qai_hub_models.items():
                if not model_info.get('loaded'):
                    continue
                
                model_path = model_info['model_path']
                try:
                    # 上傳模型
                    uploaded_model = hub.upload_model(model_path)
                    model_info['qai_hub_model'] = uploaded_model
                    model_info['model_id'] = uploaded_model.model_id
                    uploaded_count += 1
                    print(f"✅ 上傳成功: {model_name} -> Model ID: {uploaded_model.model_id}")
                except Exception as e:
                    print(f"❌ 上傳失敗 {model_name}: {e}")
                    model_info['error'] = str(e)
            
            print(f"📊 總共上傳 {uploaded_count} 個模型")
            return uploaded_count > 0
            
        except Exception as e:
            print(f"❌ 上傳過程發生錯誤: {e}")
            return False
    
    def submit_compilation_jobs(self) -> bool:
        """
        提交編譯任務
        
        Returns:
            提交是否成功
        """
        try:
            import qai_hub as hub
            
            if not self.target_device:
                print("❌ 未設定目標裝置，無法提交編譯任務")
                return False
            
            submitted_count = 0
            for model_name, model_info in self.qai_hub_models.items():
                if not model_info.get('qai_hub_model'):
                    continue
                
                try:
                    # 提交編譯任務 - 不傳遞任何選項參數
                    # 確保 model_name 不是 None 且不是空字符串
                    safe_model_name = str(model_name) if model_name is not None else "unknown_model"
                    if not safe_model_name.strip():
                        safe_model_name = "unknown_model"
                    
                    # 使用最簡單的參數呼叫方式，避免任何可能的參數問題
                    job = hub.submit_compile_job(
                        model=model_info['qai_hub_model'],
                        device=self.target_device
                    )
                    model_info['compile_job'] = job
                    model_info['compile_job_id'] = job.job_id
                    submitted_count += 1
                    print(f"✅ 提交編譯任務: {model_name} -> Job ID: {job.job_id}")
                except Exception as e:
                    print(f"❌ 提交編譯任務失敗 {model_name}: {e}")
                    model_info['error'] = str(e)
            
            print(f"📊 總共提交 {submitted_count} 個編譯任務")
            return submitted_count > 0
            
        except Exception as e:
            print(f"❌ 提交編譯任務過程發生錯誤: {e}")
            return False
    
    def submit_profile_jobs(self, profile_options: Optional[Dict] = None) -> bool:
        """
        提交效能分析任務
        
        Args:
            profile_options: 分析選項 (可選)
            
        Returns:
            提交是否成功
        """
        try:
            import qai_hub as hub
            
            if not self.target_device:
                print("❌ 未設定目標裝置，無法提交分析任務")
                return False
            
            submitted_count = 0
            for model_name, model_info in self.qai_hub_models.items():
                if not model_info.get('qai_hub_model'):
                    continue
                
                try:
                    # 提交分析任務 - 不傳遞 options 參數，讓 QAI Hub 使用預設值
                    # 確保 model_name 不是 None 且不是空字符串
                    safe_model_name = str(model_name) if model_name is not None else "unknown_model"
                    if not safe_model_name.strip():
                        safe_model_name = "unknown_model"
                    
                    job = hub.submit_profile_job(
                        model=model_info['qai_hub_model'],
                        device=self.target_device,
                        name=f"profile_{safe_model_name}"
                    )
                    model_info['profile_job'] = job
                    model_info['profile_job_id'] = job.job_id
                    submitted_count += 1
                    print(f"✅ 提交分析任務: {model_name} -> Job ID: {job.job_id}")
                except Exception as e:
                    print(f"❌ 提交分析任務失敗 {model_name}: {e}")
                    model_info['error'] = str(e)
            
            print(f"📊 總共提交 {submitted_count} 個分析任務")
            return submitted_count > 0
            
        except Exception as e:
            print(f"❌ 提交分析任務過程發生錯誤: {e}")
            return False

    def submit_link_job(self, models: List[Any], job_name: str = "link_pipeline") -> Optional[Any]:
        """
        提交模型串接任務
        
        Args:
            models: 模型物件列表
            job_name: 任務名稱
            
        Returns:
            串接任務物件或 None
        """
        try:
            import qai_hub as hub
            
            if not self.target_device:
                print("❌ 未設定目標裝置，無法提交串接任務")
                return None
            
            if not models:
                print("❌ 沒有提供模型物件，無法提交串接任務")
                return None
            
            print("🔗 提交模型串接任務...")
            print(f"   - 模型數量: {len(models)}")
            
            # 嘗試多種參數組合以兼容不同 SDK 版本
            attempts = [
                ("device", {"device": self.target_device, "name": job_name}),
                ("target_device", {"target_device": self.target_device, "name": job_name}),
                ("no_device", {"name": job_name}),
            ]
            
            errors = []
            link_job = None
            
            for label, kwargs in attempts:
                try:
                    link_job = hub.submit_link_job(models, **kwargs)
                    print(f"✅ 提交串接任務成功 ({label}): {job_name} -> Job ID: {link_job.job_id}")
                    break
                except TypeError as te:
                    errors.append(f"{label}:{te}")
                except Exception as e:
                    errors.append(f"{label}:{e}")
            
            if link_job is None:
                print(f"❌ 所有 submit_link_job 呼叫失敗: {' | '.join(errors)}")
                return None
            
            # 儲存串接任務資訊
            self.qai_hub_models['link_pipeline'] = {
                'link_job': link_job,
                'link_job_id': link_job.job_id,
                'models_count': len(models),
                'job_name': job_name
            }
            
            return link_job
            
        except Exception as e:
            print(f"❌ 提交串接任務失敗: {e}")
            return None
    
    def wait_for_jobs_completion(self, job_type: str = 'compile', 
                               timeout: int = 1800, 
                               poll_interval: int = 10) -> Dict[str, str]:
        """
        等待任務完成
        
        Args:
            job_type: 任務類型 ('compile', 'profile')
            timeout: 最大等待時間（秒）
            poll_interval: 輪詢間隔（秒）
            
        Returns:
            各任務的最終狀態字典
        """
        completed_status = ('COMPLETED', 'SUCCEEDED', 'SUCCESS', 'FINISHED', 
                          'COMPLETED_SUCCESSFULLY', 'RESULTS_READY', 'RESULTS READY', 
                          'results_ready', 'Results Ready')
        
        job_key = f'{job_type}_job'
        status_key = f'{job_type}_status'
        
        all_done = False
        waited = 0
        final_statuses = {}
        
        print(f"\n⏳ 等待所有 {job_type.upper()} Job 完成...")
        
        while not all_done and waited < timeout:
            all_done = True
            status_lines = []
            
            for model_name, model_info in self.qai_hub_models.items():
                job = model_info.get(job_key)
                if not job:
                    continue
                
                # 刷新任務狀態
                try:
                    if hasattr(job, 'refresh'):
                        job.refresh()
                    status = getattr(job, 'status', None) or getattr(job, 'state', None)
                    model_info[status_key] = status
                except Exception as e:
                    status = None
                    print(f"❌ 獲取 {model_name} 狀態失敗: {e}")
                
                job_id = getattr(job, 'job_id', '')
                status_line = f"  {model_name}: {job_id} 狀態: {status}"
                status_lines.append(status_line)
                
                if status is None or str(status).upper() not in [s.upper() for s in completed_status]:
                    all_done = False
            
            # 顯示狀態
            if waited > 0:
                sys.stdout.write(f"\033[{len(status_lines)}A")  # 游標上移
            
            for line in status_lines:
                print(line)
            
            if not all_done:
                print(f"  ...尚有 {job_type.upper()} Job 執行中，{poll_interval} 秒後再查詢...\n")
                time.sleep(poll_interval)
                waited += poll_interval
        
        # 收集最終狀態
        for model_name, model_info in self.qai_hub_models.items():
            if job_key in model_info:
                final_statuses[model_name] = model_info.get(status_key, 'UNKNOWN')
        
        if not all_done:
            print(f"⚠️ 超過最大等待時間，部分 {job_type.upper()} Job 可能尚未完成")
        else:
            print(f"\n✅ {job_type.upper()} Jobs 全部完成！")
        
        return final_statuses
    
    def generate_html_report(self, report_type: str = 'compile') -> str:
        """
        產生 HTML 報告
        
        Args:
            report_type: 報告類型 ('compile', 'profile')
            
        Returns:
            產生的報告檔案路徑
        """
        job_key = f'{report_type}_job'
        status_key = f'{report_type}_status'
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        report_file = f"qai_hub_{report_type}_report_{timestamp.replace(':', '').replace(' ', '_')}.html"
        
        html_content = f'''
        <html>
        <head>
            <meta charset="utf-8">
            <title>QAI Hub {report_type.capitalize()} Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .warning {{ color: orange; }}
            </style>
        </head>
        <body>
            <h1>QAI Hub {report_type.capitalize()} Report</h1>
            <p><b>Timestamp:</b> {timestamp}</p>
            <p><b>Target Device:</b> {self.target_device.name if self.target_device else 'N/A'}</p>
            
            <h2>Models & {report_type.capitalize()} Jobs</h2>
            <table>
                <tr>
                    <th>Model Name</th>
                    <th>Status</th>
                    <th>Job ID</th>
                    <th>Dashboard</th>
                    <th>Error</th>
                </tr>
        '''
        
        for model_name, model_info in self.qai_hub_models.items():
            job = model_info.get(job_key)
            job_id = getattr(job, 'job_id', '') if job else ''
            status = model_info.get(status_key, '')
            error = model_info.get('error', '')
            
            dashboard_link = f'<a href="https://aihub.qualcomm.com/jobs/{job_id}">{job_id}</a>' if job_id else ''
            
            status_class = 'success' if str(status).upper() in ['COMPLETED', 'SUCCEEDED', 'SUCCESS'] else 'error' if error else 'warning'
            
            html_content += f'''
                <tr>
                    <td>{model_name}</td>
                    <td class="{status_class}">{status}</td>
                    <td>{job_id}</td>
                    <td>{dashboard_link}</td>
                    <td>{error}</td>
                </tr>
            '''
        
        html_content += '''
            </table>
            </body>
            </html>
        '''
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📊 HTML 報告已產生: {report_file}")
        return report_file
    
    def check_device_support(self) -> Dict[str, bool]:
        """
        檢查裝置支援的框架格式
        
        Returns:
            支援的框架格式字典
        """
        if not self.target_device:
            return {}
        
        device_attrs = getattr(self.target_device, 'attributes', [])
        
        # 如果設備屬性為空，使用預設支援設定
        if not device_attrs:
            print("⚠️  設備屬性為空，使用預設支援設定")
            # 對於 Snapdragon X Elite CRD，預設支援 ONNX
            support_info = {
                'onnx': True,
                'tflite': False,
                'dlc': False
            }
        else:
            # 正常檢查設備屬性
            support_info = {
                'onnx': any('framework:onnx' in str(a).lower() for a in device_attrs),
                'tflite': any('framework:tflite' in str(a).lower() for a in device_attrs),
                'dlc': any('framework:dlc' in str(a).lower() for a in device_attrs)
            }
        
        print(f"\n📋 裝置支援格式:")
        for framework, supported in support_info.items():
            status = "✅" if supported else "❌"
            print(f"   {status} {framework.upper()}: {'支援' if supported else '不支援'}")
        
        return support_info

# 單例模式實例
_qaihub_client_instance = None

def get_qaihub_client(base_dir: Optional[Path] = None) -> QAIHubClient:
    """
    取得 QAI Hub 客戶端實例（單例模式）
    
    Args:
        base_dir: 基礎目錄路徑
        
    Returns:
        QAIHubClient 實例
    """
    global _qaihub_client_instance
    if _qaihub_client_instance is None:
        _qaihub_client_instance = QAIHubClient(base_dir)
    return _qaihub_client_instance
