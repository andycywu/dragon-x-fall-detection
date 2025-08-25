"""
模型預處理模組 - 負責模型的自動轉換和移動
根據目標裝置支援情況，自動將 raw 目錄中的模型轉換並移動到 onnx 目錄
"""
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

from .scanner import ModelScanner
from .conversion import ModelConverter
from .advanced_conversion import AdvancedModelConverter, get_advanced_converter
from .qaihub_client import QAIHubClient

# 載入環境變數
load_dotenv()

MODEL_SOURCE_DIR = os.getenv('MODEL_SOURCE_DIR', 'raw')  # 原始模型目錄名稱
ONNX_MODEL_DIR = os.getenv('ONNX_MODEL_DIR', 'onnx')  # ONNX 模型目錄名稱
ENABLE_PREPROCESSING = os.getenv('ENABLE_PREPROCESSING', 'true').lower() == 'true'
AUTO_CONVERT_TFLITE = os.getenv('AUTO_CONVERT_TFLITE', 'true').lower() == 'true'


class ModelPreprocessor:
    """模型預處理器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        初始化模型預處理器
        
        Args:
            base_dir: 基礎目錄路徑
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent / 'models'
        self.base_dir = base_dir
        self.scanner = ModelScanner(base_dir)
        self.converter = ModelConverter()
        self.advanced_converter = get_advanced_converter()
        self.qaihub_client = QAIHubClient(base_dir)
    
    def check_device_support(self) -> Dict[str, bool]:
        """
        檢查裝置支援的格式
        
        Returns:
            支援的框架格式字典
        """
        return self.qaihub_client.check_device_support()
    
    def scan_raw_models(self) -> Dict[str, List[Path]]:
        """
        掃描 raw 目錄中的模型檔案
        
        Returns:
            包含各種格式模型檔案的字典
        """
        return self.scanner.scan_model_directory(MODEL_SOURCE_DIR)
    
    def scan_onnx_models(self) -> Dict[str, List[Path]]:
        """
        掃描 onnx 目錄中的模型檔案
        
        Returns:
            包含各種格式模型檔案的字典
        """
        return self.scanner.scan_model_directory(ONNX_MODEL_DIR)
    
    def move_supported_models(self, models: Dict[str, List[Path]], support_info: Dict[str, bool]) -> Tuple[List[Path], List[Path]]:
        """
        移動裝置支援的模型到 onnx 目錄
        
        Args:
            models: 模型檔案字典
            support_info: 裝置支援資訊
            
        Returns:
            (成功移動的檔案列表, 失敗的檔案列表)
        """
        if not ENABLE_PREPROCESSING:
            return [], []
        
        onnx_dir = self.base_dir / ONNX_MODEL_DIR
        onnx_dir.mkdir(parents=True, exist_ok=True)
        
        moved_files = []
        failed_files = []
        
        # 移動所有支援的 ONNX 檔案
        if support_info.get('onnx', False) and models.get('onnx'):
            for onnx_path in models['onnx']:
                try:
                    dest_path = onnx_dir / onnx_path.name
                    if not dest_path.exists():
                        shutil.move(str(onnx_path), str(dest_path))
                        moved_files.append(dest_path)
                        print(f"✅ 移動 ONNX 檔案: {onnx_path.name} -> {ONNX_MODEL_DIR}/")
                    else:
                        print(f"⏭️ ONNX 檔案已存在，跳過移動: {onnx_path.name}")
                except Exception as e:
                    print(f"❌ 移動 ONNX 檔案失敗 {onnx_path.name}: {e}")
                    failed_files.append(onnx_path)
        
        # 移動所有支援的 DLC 檔案
        if support_info.get('dlc', False) and models.get('dlc'):
            for dlc_path in models['dlc']:
                try:
                    dest_path = onnx_dir / dlc_path.name
                    if not dest_path.exists():
                        shutil.move(str(dlc_path), str(dest_path))
                        moved_files.append(dest_path)
                        print(f"✅ 移動 DLC 檔案: {dlc_path.name} -> {ONNX_MODEL_DIR}/")
                    else:
                        print(f"⏭️ DLC 檔案已存在，跳過移動: {dlc_path.name}")
                except Exception as e:
                    print(f"❌ 移動 DLC 檔案失敗 {dlc_path.name}: {e}")
                    failed_files.append(dlc_path)
        
        return moved_files, failed_files
    
    def convert_and_move_tflite(self, tflite_files: List[Path], support_info: Dict[str, bool]) -> Tuple[List[Path], List[Path]]:
        """
        轉換並移動 TFLite 模型到 onnx 目錄
        
        Args:
            tflite_files: TFLite 檔案列表
            support_info: 裝置支援資訊
            
        Returns:
            (成功轉換的檔案列表, 失敗的檔案列表)
        """
        if not ENABLE_PREPROCESSING or not AUTO_CONVERT_TFLITE:
            return [], []
        
        converted_files = []
        failed_files = []
        onnx_dir = self.base_dir / ONNX_MODEL_DIR
        
        # 如果裝置支援 TFLite，直接移動
        if support_info.get('tflite', False):
            for tflite_path in tflite_files:
                try:
                    dest_path = onnx_dir / tflite_path.name
                    if not dest_path.exists():
                        shutil.move(str(tflite_path), str(dest_path))
                        converted_files.append(dest_path)
                        print(f"✅ 移動 TFLite 檔案: {tflite_path.name} -> {ONNX_MODEL_DIR}/")
                    else:
                        print(f"⏭️ TFLite 檔案已存在，跳過移動: {tflite_path.name}")
                except Exception as e:
                    print(f"❌ 移動 TFLite 檔案失敗 {tflite_path.name}: {e}")
                    failed_files.append(tflite_path)
        else:
            # 如果裝置不支援 TFLite，轉換為 ONNX
            for tflite_path in tflite_files:
                onnx_path = onnx_dir / f"{tflite_path.stem}.onnx"
                
                # 檢查 ONNX 檔案是否已經存在
                if onnx_path.exists():
                    print(f"⏭️ ONNX 檔案已存在，跳過轉換: {tflite_path.name} -> {onnx_path.name}")
                    converted_files.append(onnx_path)
                    continue
                    
                print(f"🔄 轉換 TFLite 到 ONNX: {tflite_path.name}")
                
                # 使用進階轉換器進行轉換
                result = self.advanced_converter.convert_tflite_to_onnx_fixed(tflite_path, onnx_dir)
                
                if result["status"] == "ok":
                    converted_files.append(result["onnx_path"])
                    print(f"✅ 轉換成功: {tflite_path.name} -> {result['onnx_path'].name}")
                elif result["status"] == "warning":
                    converted_files.append(result["onnx_path"])
                    print(f"⚠️  轉換完成但有警告: {tflite_path.name} - {result['message']}")
                else:
                    failed_files.append(tflite_path)
                    print(f"❌ 轉換失敗: {tflite_path.name} - {result['message']}")
        
        return converted_files, failed_files
    
    def preprocess_models(self) -> Dict[str, List[Path]]:
        """
        執行模型預處理流程
        
        Returns:
            預處理結果字典
        """
        if not ENABLE_PREPROCESSING:
            print("ℹ️ 模型預處理已禁用，跳過預處理流程")
            return {}
        
        print("🔧 開始模型預處理流程...")
        
        # 檢查裝置支援
        support_info = self.check_device_support()
        print(f"📋 裝置支援格式:")
        for framework, supported in support_info.items():
            status = "✅" if supported else "❌"
            print(f"   {status} {framework.upper()}: {'支援' if supported else '不支援'}")
        
        # 掃描 raw 目錄
        raw_models = self.scan_raw_models()
        print(f"📁 在 {MODEL_SOURCE_DIR} 目錄中找到 {sum(len(files) for files in raw_models.values())} 個模型檔案")
        
        # 移動支援的模型
        moved_files, move_failed = self.move_supported_models(raw_models, support_info)
        
        # 轉換和移動 TFLite 模型
        converted_files, convert_failed = self.convert_and_move_tflite(raw_models.get('tflite', []), support_info)
        
        # 掃描處理後的 onnx 目錄
        processed_models = self.scan_onnx_models()
        
        # 統計結果
        total_processed = len(moved_files) + len(converted_files)
        total_failed = len(move_failed) + len(convert_failed)
        
        print(f"\n📊 預處理完成:")
        print(f"   ✅ 成功處理: {total_processed} 個檔案")
        print(f"   ❌ 處理失敗: {total_failed} 個檔案")
        print(f"   📁 現在 {ONNX_MODEL_DIR} 目錄中有 {sum(len(files) for files in processed_models.values())} 個模型檔案")
        
        return {
            'moved_files': moved_files,
            'converted_files': converted_files,
            'move_failed': move_failed,
            'convert_failed': convert_failed,
            'processed_models': processed_models,
            'device_support': support_info
        }
    
    def get_ready_models(self) -> Dict[str, List[Path]]:
        """
        取得準備好的模型（位於 onnx 目錄中）
        
        Returns:
            準備好的模型字典
        """
        return self.scan_onnx_models()


# 單例實例
_model_preprocessor = None

def get_model_preprocessor(base_dir: Optional[Path] = None) -> ModelPreprocessor:
    """
    取得模型預處理器實例（單例模式）
    
    Args:
        base_dir: 基礎目錄路徑
        
    Returns:
        ModelPreprocessor 實例
    """
    global _model_preprocessor
    if _model_preprocessor is None:
        _model_preprocessor = ModelPreprocessor(base_dir)
    return _model_preprocessor


def preprocess_models() -> Dict[str, List[Path]]:
    """
    快速執行模型預處理
    
    Returns:
        預處理結果字典
    """
    preprocessor = get_model_preprocessor()
    return preprocessor.preprocess_models()


def get_ready_models() -> Dict[str, List[Path]]:
    """
    快速取得準備好的模型
    
    Returns:
        準備好的模型字典
    """
    preprocessor = get_model_preprocessor()
    return preprocessor.get_ready_models()


if __name__ == "__main__":
    # 測試程式
    result = preprocess_models()
    print(f"\n預處理結果: {len(result.get('moved_files', []))} 移動, {len(result.get('converted_files', []))} 轉換")
    
    ready_models = get_ready_models()
    print(f"準備好的模型: {sum(len(files) for files in ready_models.values())} 個檔案")
