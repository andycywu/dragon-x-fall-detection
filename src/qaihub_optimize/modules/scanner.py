"""
模型掃描模組 - 負責掃描和檢測模型檔案
"""
from pathlib import Path
from typing import List, Dict, Tuple


class ModelScanner:
    """模型檔案掃描器"""
    
    def __init__(self, base_dir: Path = None):
        """
        初始化掃描器
        
        Args:
            base_dir: 基礎目錄路徑，預設為專案的 models 目錄
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent / 'models'
        self.base_dir = base_dir
    
    def scan_org_directory(self) -> Dict[str, List[Path]]:
        """
        掃描 org 目錄中的模型檔案
        
        Returns:
            包含各種格式模型檔案的字典
        """
        org_dir = self.base_dir / 'org'
        if not org_dir.exists():
            raise FileNotFoundError(f"找不到 org 目錄: {org_dir}")
        
        all_files = list(org_dir.glob('*'))
        
        # 分類模型檔案
        model_files = {
            'tflite': [f for f in all_files if f.suffix.lower() == '.tflite'],
            'onnx': [f for f in all_files if f.suffix.lower() == '.onnx'],
            'dlc': [f for f in all_files if f.suffix.lower() == '.dlc'],
            'other': [f for f in all_files if f.suffix.lower() not in ['.tflite', '.onnx', '.dlc']]
        }
        
        return model_files
    
    def scan_model_directory(self, model_dir: str) -> Dict[str, List[Path]]:
        """
        掃描指定模型目錄
        
        Args:
            model_dir: 模型目錄名稱
            
        Returns:
            包含各種格式模型檔案的字典
        """
        target_dir = self.base_dir / model_dir
        if not target_dir.exists():
            raise FileNotFoundError(f"找不到目錄: {target_dir}")
        
        all_files = list(target_dir.glob('*'))
        
        # 分類模型檔案
        model_files = {
            'tflite': [f for f in all_files if f.suffix.lower() == '.tflite'],
            'onnx': [f for f in all_files if f.suffix.lower() == '.onnx'],
            'dlc': [f for f in all_files if f.suffix.lower() == '.dlc'],
            'other': [f for f in all_files if f.suffix.lower() not in ['.tflite', '.onnx', '.dlc']]
        }
        
        return model_files
    
    def get_model_counts(self, model_files: Dict[str, List[Path]]) -> Dict[str, int]:
        """
        取得模型檔案數量統計
        
        Args:
            model_files: 模型檔案字典
            
        Returns:
            各種格式模型數量的字典
        """
        return {
            'tflite': len(model_files['tflite']),
            'onnx': len(model_files['onnx']),
            'dlc': len(model_files['dlc']),
            'other': len(model_files['other']),
            'total': sum(len(files) for files in model_files.values())
        }
    
    def print_scan_results(self, model_files: Dict[str, List[Path]]):
        """
        列印掃描結果
        
        Args:
            model_files: 模型檔案字典
        """
        counts = self.get_model_counts(model_files)
        
        print(f"\n[模型掃描] 偵測到 {counts['total']} 個檔案：")
        print(f"  - TFLite: {counts['tflite']} 個")
        print(f"  - ONNX: {counts['onnx']} 個")
        print(f"  - DLC: {counts['dlc']} 個")
        print(f"  - 其他: {counts['other']} 個")
        
        if counts['tflite'] > 0:
            print("\nTFLite 檔案：")
            for f in model_files['tflite']:
                print(f"  - {f.name}")
        
        if counts['onnx'] > 0:
            print("\nONNX 檔案：")
            for f in model_files['onnx']:
                print(f"  - {f.name}")
        
        if counts['dlc'] > 0:
            print("\nDLC 檔案：")
            for f in model_files['dlc']:
                print(f"  - {f.name}")


# 單例實例
model_scanner = ModelScanner()


def scan_models() -> Dict[str, List[Path]]:
    """
    快速掃描 org 目錄中的模型檔案
    
    Returns:
        包含各種格式模型檔案的字典
    """
    return model_scanner.scan_org_directory()


if __name__ == "__main__":
    # 測試程式
    try:
        files = scan_models()
        model_scanner.print_scan_results(files)
    except FileNotFoundError as e:
        print(f"錯誤: {e}")
