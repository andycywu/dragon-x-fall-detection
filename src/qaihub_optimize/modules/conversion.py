"""
模型轉換模組 - 負責模型格式轉換功能
"""
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import threading
import onnx
from onnx import ModelProto
import torch


def sanitize_onnx_inplace(model: ModelProto) -> dict:
    """
    修正 1) IO 與 value_info 重複、2) initializer 也列在 input 的問題，
    並遞迴處理子圖。
    """
    report = {"removed_value_info": 0, "removed_input_initializers": 0}

    def _remove_vi_dups(graph):
        io_names = {t.name for t in list(graph.input) + list(graph.output)}
        keep = []
        removed = 0
        for vi in graph.value_info:
            if vi.name in io_names:
                removed += 1
            else:
                keep.append(vi)
        del graph.value_info[:]
        graph.value_info.extend(keep)
        return removed

    def _inputs_not_in_initializers(graph):
        init_names = {init.name for init in graph.initializer}
        keep = []
        removed = 0
        for in_tensor in graph.input:
            if in_tensor.name in init_names:
                removed += 1
            else:
                keep.append(in_tensor)
        del graph.input[:]
        graph.input.extend(keep)
        return removed

    def _walk_subgraphs(node):
        subgraphs = []
        for attr in node.attribute:
            if attr.g:
                subgraphs.append(attr.g)
            for g in attr.graphs:
                subgraphs.append(g)
        return subgraphs

    def _sanitize_graph(g):
        report["removed_value_info"] += _remove_vi_dups(g)
        report["removed_input_initializers"] += _inputs_not_in_initializers(g)
        for n in g.node:
            for sg in _walk_subgraphs(n):
                _sanitize_graph(sg)

    _sanitize_graph(model.graph)
    return report


def convert_pt_to_onnx(pt_model_path: str, onnx_output_path: str, input_shape: tuple):
    """
    將 PyTorch (.pt) 模型轉換為 ONNX 格式。

    Args:
        pt_model_path (str): PyTorch 模型的路徑。
        onnx_output_path (str): 輸出的 ONNX 模型路徑。
        input_shape (tuple): 模型的輸入形狀。

    Returns:
        dict: 包含轉換狀態和訊息的字典。
    """
    try:
        # 加載 PyTorch 模型
        model = torch.load(pt_model_path)
        model.eval()

        # 建立虛擬輸入
        dummy_input = torch.randn(*input_shape)

        # 將模型導出為 ONNX
        torch.onnx.export(
            model,
            dummy_input,
            onnx_output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output']
        )

        return {
            "status": "ok",
            "message": f"成功將 {pt_model_path} 轉換為 {onnx_output_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"轉換失敗: {str(e)}"
        }


class ModelConverter:
    """模型格式轉換器"""
    
    def __init__(self):
        self.conversion_timeout = 600  # 轉換超時時間（秒）
    
    def convert_tflite_to_onnx(self, tflite_path: Path, output_dir: Path) -> Dict:
        """
        將 TFLite 模型轉換為 ONNX 格式
        
        Args:
            tflite_path: TFLite 模型路徑
            output_dir: 輸出目錄
            
        Returns:
            轉換結果字典
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
        
        try:
            # 使用 tflite2onnx 進行轉換
            result = subprocess.run(
                ['tflite2onnx', str(tflite_path), str(onnx_path)],
                capture_output=True,
                text=True,
                timeout=self.conversion_timeout
            )

            if result.returncode == 0 and onnx_path.exists():
                # 加入 sanitize 步驟
                model = onnx.load(onnx_path)
                sanitize_report = sanitize_onnx_inplace(model)
                onnx.checker.check_model(model, full_check=True)
                onnx.save(model, onnx_path)

                return {
                    "status": "ok",
                    "message": "轉換成功並已清理",
                    "onnx_path": onnx_path,
                    "tflite_path": tflite_path,
                    "sanitize_report": sanitize_report,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "status": "error",
                    "message": f"轉換失敗: {result.stderr}",
                    "onnx_path": None,
                    "tflite_path": tflite_path,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"轉換超時 ({self.conversion_timeout}秒)",
                "onnx_path": None,
                "tflite_path": tflite_path
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"轉換異常: {str(e)}",
                "onnx_path": None,
                "tflite_path": tflite_path
            }
    
    def batch_convert_tflite(self, tflite_files: List[Path], output_dir: Path) -> List[Dict]:
        """
        批次轉換多個 TFLite 檔案
        
        Args:
            tflite_files: TFLite 檔案列表
            output_dir: 輸出目錄
            
        Returns:
            轉換結果列表
        """
        results = []
        failed_conversions = []
        
        print(f"\n🔄 開始批次轉換 {len(tflite_files)} 個 TFLite 檔案...")
        
        for i, tflite_path in enumerate(tflite_files, 1):
            print(f"  [{i}/{len(tflite_files)}] 轉換 {tflite_path.name} ...")
            
            result = self.convert_tflite_to_onnx(tflite_path, output_dir)
            results.append(result)
            
            if result["status"] == "ok":
                print(f"    ✅ 成功: {result['onnx_path'].name}")
            else:
                print(f"    ❌ 失敗: {result['message']}")
                failed_conversions.append(tflite_path.name)
        
        return results, failed_conversions
    
    def ask_for_conversion(self, tflite_count: int, timeout: int = 30) -> bool:
        """
        詢問使用者是否要進行轉換
        
        Args:
            tflite_count: TFLite 檔案數量
            timeout: 詢問超時時間（秒）
            
        Returns:
            是否進行轉換
        """
        print(f"⚠️  偵測到 {tflite_count} 個 TFLite 模型。是否要自動全部轉換為 ONNX？(y/n, {timeout}秒後自動轉換)")
        
        user_response = [None]
        
        def get_user_input():
            try:
                user_response[0] = input().strip().lower()
            except:
                user_response[0] = None
        
        # 啟動輸入執行緒
        input_thread = threading.Thread(target=get_user_input)
        input_thread.daemon = True
        input_thread.start()
        
        # 等待使用者輸入或超時
        input_thread.join(timeout=timeout)
        
        if user_response[0] is None or user_response[0] == '':
            print("⏰ 逾時，自動執行轉換 (y)")
            return True
        
        return user_response[0] == 'y'
    
    def convert_pt_to_onnx(self, pt_model_path: Path, output_dir: Path, input_shape: tuple) -> Dict:
        """
        將 PyTorch (.pt) 模型轉換為 ONNX 格式。

        Args:
            pt_model_path (Path): PyTorch 模型的路徑。
            output_dir (Path): 輸出目錄。
            input_shape (tuple): 模型的輸入形狀。

        Returns:
            dict: 包含轉換狀態和訊息的字典。
        """
        if not pt_model_path.exists():
            return {
                "status": "error",
                "message": f"PyTorch 模型不存在: {pt_model_path}"
            }

        output_dir.mkdir(parents=True, exist_ok=True)
        onnx_path = output_dir / f"{pt_model_path.stem}.onnx"

        return convert_pt_to_onnx(str(pt_model_path), str(onnx_path), input_shape)


# 單例實例
model_converter = ModelConverter()


def convert_tflite_files(tflite_files: List[Path], output_dir: Path) -> List[Dict]:
    """
    快速轉換 TFLite 檔案
    
    Args:
        tflite_files: TFLite 檔案列表
        output_dir: 輸出目錄
        
    Returns:
        轉換結果列表和失敗清單
    """
    return model_converter.batch_convert_tflite(tflite_files, output_dir)


def ask_for_tflite_conversion(tflite_count: int) -> bool:
    """
    快速詢問是否進行 TFLite 轉換
    
    Args:
        tflite_count: TFLite 檔案數量
        
    Returns:
        是否進行轉換
    """
    return model_converter.ask_for_conversion(tflite_count)


if __name__ == "__main__":
    # 測試程式
    test_dir = Path(__file__).parent.parent.parent / 'models' / 'test'
    test_tflite = test_dir / "test.tflite"
    
    if test_tflite.exists():
        result = model_converter.convert_tflite_to_onnx(test_tflite, test_dir)
        print(f"轉換結果: {result}")
    else:
        print("測試檔案不存在，請先建立測試檔案")
