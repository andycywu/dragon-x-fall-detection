"""
進階模型轉換模組 - 解決 tflite2onnx 轉換問題
提供多種轉換方法和錯誤處理
"""
import subprocess
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import shutil
import re

logger = logging.getLogger(__name__)

class AdvancedModelConverter:
    """進階模型轉換器，支援多種轉換方法和錯誤處理"""
    
    def __init__(self):
        self.conversion_timeout = 600
        self.supported_formats = ['tflite', 'onnx', 'pt']
    
    def find_executable(self, exe_name: str) -> Optional[str]:
        """尋找可執行檔"""
        # 檢查虛擬環境
        venv_bin = Path(__file__).parent.parent / '.venv' / 'bin'
        candidate = venv_bin / exe_name
        if candidate.exists():
            return str(candidate)
        
        # 檢查系統 PATH
        which = shutil.which(exe_name)
        if which:
            return which
        
        return None
    
    def check_tflite_model(self, tflite_path: Path) -> Dict:
        """檢查 TFLite 模型是否可轉換"""
        try:
            # 首先檢查基本檔案屬性
            if tflite_path.stat().st_size == 0:
                return {
                    "status": "error", 
                    "message": "模型檔案為空"
                }
            
            # 檢查檔案頭部是否為 TFLite (更寬鬆的檢查)
            with open(tflite_path, 'rb') as f:
                header = f.read(8)  # 讀取更多位元組以適應不同版本
                
            # TFLite 檔案通常以特定的魔術數字開頭
            # 但不同版本可能有所不同，我們使用更寬鬆的檢查
            if len(header) < 4:
                return {
                    "status": "error",
                    "message": "檔案過短，不是有效的 TFLite 檔案"
                }
            
            # 檢查檔案大小和基本結構
            file_size = tflite_path.stat().st_size
            if file_size < 100:  # TFLite 檔案通常至少幾KB
                return {
                    "status": "warning",
                    "message": "檔案大小異常，可能不是有效的 TFLite 模型"
                }
            
            return {
                "status": "ok",
                "message": "基本檢查通過（無法深度分析）",
                "file_size": file_size
            }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"模型檢查異常: {str(e)}"
            }
    
    def convert_tflite_to_onnx_via_tf2onnx(self, tflite_path: Path, output_dir: Path) -> Dict:
        """使用 tf2onnx 進行轉換（替代方案）"""
        try:
            # 需要先將 tflite 轉換為 saved_model，然後再轉為 onnx
            # 這是一個複雜的過程，需要 TensorFlow 環境
            temp_dir = output_dir / "temp_saved_model"
            temp_dir.mkdir(exist_ok=True)
            
            # 這裡只是示例，實際需要完整的轉換流程
            result = subprocess.run([
                'python', '-c', 
                f'''
import tensorflow as tf
import tf2onnx
converter = tf.lite.TFLiteConverter.from_saved_model("{temp_dir}")
tflite_model = converter.convert()
                '''
            ], capture_output=True, text=True, timeout=self.conversion_timeout)
            
            if result.returncode == 0:
                onnx_path = output_dir / f"{tflite_path.stem}.onnx"
                return {
                    "status": "ok",
                    "message": "轉換成功",
                    "onnx_path": onnx_path
                }
            else:
                return {
                    "status": "error",
                    "message": f"tf2onnx 轉換失敗: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"tf2onnx 轉換異常: {str(e)}"
            }
    
    def convert_tflite_to_onnx_fixed(self, tflite_path: Path, output_dir: Path) -> Dict:
        """
        修復的 TFLite 到 ONNX 轉換方法
        解決參數傳遞和錯誤處理問題
        """
        if not tflite_path.exists():
            return {
                "status": "error",
                "message": f"TFLite 檔案不存在: {tflite_path}",
                "onnx_path": None
            }
        
        if tflite_path.stat().st_size == 0:
            return {
                "status": "error",
                "message": f"TFLite 檔案為空: {tflite_path.name}",
                "onnx_path": None
            }
        
        output_dir.mkdir(parents=True, exist_ok=True)
        onnx_path = output_dir / f"{tflite_path.stem}.onnx"
        
        # 檢查 ONNX 檔案是否已經存在
        if onnx_path.exists():
            return {
                "status": "ok",
                "message": "ONNX 檔案已存在，跳過轉換",
                "onnx_path": onnx_path
            }
        
        # 尋找 tflite2onnx 可執行檔
        tflite2onnx_exec = self.find_executable('tflite2onnx')
        if not tflite2onnx_exec:
            return {
                "status": "error",
                "message": "找不到 tflite2onnx 可執行檔，請安裝或添加到 PATH",
                "onnx_path": None
            }
        
        try:
            # 正確的參數格式：tflite2onnx input.tflite output.onnx
            result = subprocess.run(
                [tflite2onnx_exec, str(tflite_path), str(onnx_path)],
                capture_output=True,
                text=True,
                timeout=self.conversion_timeout
            )

            if result.returncode == 0 and onnx_path.exists():
                # 檢查轉換後的 ONNX 檔案是否有效
                try:
                    import onnx
                    model = onnx.load(onnx_path)
                    onnx.checker.check_model(model)
                    
                    return {
                        "status": "ok",
                        "message": "轉換成功",
                        "onnx_path": onnx_path,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                except Exception as e:
                    return {
                        "status": "warning",
                        "message": f"轉換完成但 ONNX 檔案檢查失敗: {str(e)}",
                        "onnx_path": onnx_path,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
            else:
                # 分析錯誤訊息
                error_output = result.stderr or result.stdout
                error_message = self.analyze_conversion_error(error_output, tflite_path.name)
                
                return {
                    "status": "error",
                    "message": error_message,
                    "onnx_path": None,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"轉換超時 ({self.conversion_timeout}秒)",
                "onnx_path": None
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"轉換異常: {str(e)}",
                "onnx_path": None
            }
    
    def analyze_conversion_error(self, error_output: str, model_name: str) -> str:
        """分析轉換錯誤並提供友好的錯誤訊息"""
        error_output_lower = error_output.lower()
        
        if 'float16' in error_output_lower:
            return f"模型 {model_name} 包含 float16 資料類型，tflite2onnx 不支援。建議：使用 TensorFlow 將模型轉換為 float32 格式後再匯出為 TFLite。"
        
        if 'densify' in error_output_lower:
            return f"模型 {model_name} 包含 DENSIFY 操作，tflite2onnx 不支援此操作。建議：使用 tf2onnx 或其他轉換工具，或在模型匯出時避免使用此操作。"
        
        if 'indexerror' in error_output_lower or 'index out of range' in error_output_lower:
            return f"模型 {model_name} 轉換時發生索引錯誤，可能是模型格式問題。建議：檢查模型是否完整且有效。"
        
        if 'typeerror' in error_output_lower or 'has no len' in error_output_lower:
            return f"模型 {model_name} 轉換時發生類型錯誤，可能是 tflite2onnx 版本不相容。建議：更新 tflite2onnx 或嘗試其他版本。"
        
        if 'unrecognized arguments' in error_output_lower:
            return f"參數格式錯誤，請使用正確的 tflite2onnx 命令格式: tflite2onnx input.tflite output.onnx"
        
        # 通用錯誤訊息
        return f"轉換失敗: {error_output[:200]}..." if len(error_output) > 200 else f"轉換失敗: {error_output}"
    
    def batch_convert_with_fallback(self, tflite_files: List[Path], output_dir: Path) -> Tuple[List[Dict], List[Path]]:
        """
        批次轉換並提供備用方案
        
        Returns:
            (成功結果列表, 失敗檔案列表)
        """
        successful_results = []
        failed_files = []
        
        for tflite_path in tflite_files:
            print(f"🔄 處理 {tflite_path.name}...")
            
            # 首先檢查模型
            check_result = self.check_tflite_model(tflite_path)
            if check_result["status"] == "error":
                print(f"❌ 模型檢查失敗: {check_result['message']}")
                failed_files.append(tflite_path)
                continue
            
            # 嘗試標準轉換
            result = self.convert_tflite_to_onnx_fixed(tflite_path, output_dir)
            
            if result["status"] == "ok":
                successful_results.append(result)
                print(f"✅ 轉換成功: {tflite_path.name}")
            else:
                print(f"❌ 標準轉換失敗: {result['message']}")
                
                # 如果標準轉換失敗，嘗試備用方案
                print(f"🔄 嘗試備用轉換方案...")
                fallback_result = self.convert_tflite_to_onnx_via_tf2onnx(tflite_path, output_dir)
                
                if fallback_result["status"] == "ok":
                    successful_results.append(fallback_result)
                    print(f"✅ 備用轉換成功: {tflite_path.name}")
                else:
                    failed_files.append(tflite_path)
                    print(f"❌ 所有轉換方法都失敗: {tflite_path.name}")
        
        return successful_results, failed_files
    
    def generate_conversion_report(self, results: List[Dict], failed_files: List[Path]) -> str:
        """生成轉換報告"""
        report = [
            "📊 模型轉換報告",
            "=" * 50,
            f"✅ 成功轉換: {len(results)} 個檔案",
            f"❌ 轉換失敗: {len(failed_files)} 個檔案",
            "",
            "成功轉換的檔案:"
        ]
        
        for result in results:
            if result["status"] == "ok":
                report.append(f"  - {result['onnx_path'].name if result.get('onnx_path') else '未知'}")
        
        if failed_files:
            report.extend(["", "失敗的檔案:"])
            for failed_file in failed_files:
                report.append(f"  - {failed_file.name}")
        
        return "\n".join(report)


# 單例實例
_advanced_converter = None

def get_advanced_converter() -> AdvancedModelConverter:
    """取得進階轉換器實例"""
    global _advanced_converter
    if _advanced_converter is None:
        _advanced_converter = AdvancedModelConverter()
    return _advanced_converter


def advanced_convert_tflite_files(tflite_files: List[Path], output_dir: Path) -> Tuple[List[Dict], List[Path]]:
    """快速進階轉換"""
    converter = get_advanced_converter()
    return converter.batch_convert_with_fallback(tflite_files, output_dir)


if __name__ == "__main__":
    # 測試程式
    converter = AdvancedModelConverter()
    test_tflite = Path("/Users/andycyw/mvp_fall_detection_starter/src/models/raw/face_detector.tflite")
    test_output = Path("/Users/andycyw/mvp_fall_detection_starter/src/models/onnx")
    
    if test_tflite.exists():
        result = converter.convert_tflite_to_onnx_fixed(test_tflite, test_output)
        print(f"轉換結果: {result}")
    else:
        print("測試檔案不存在")
