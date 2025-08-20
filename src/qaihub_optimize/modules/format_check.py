"""
格式檢查模組 - 負責模型格式驗證和檢查
"""
import onnx
from pathlib import Path
from typing import List, Tuple, Optional, Dict


class FormatChecker:
    """模型格式檢查器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()
    
    def fix_onnx_value_info(self, onnx_path: Path) -> bool:
        """
        修復 ONNX 模型的 value_info 重複問題
        
        Args:
            onnx_path: ONNX 模型路徑
            
        Returns:
            是否修復成功
        """
        try:
            model = onnx.load(str(onnx_path))
            io_names = set()
            
            # 收集所有 input 和 output 的名稱
            for t in list(model.graph.input) + list(model.graph.output):
                io_names.add(t.name)
            
            # 移除 value_info 中與 input/output 重複的 tensor
            new_value_info = [vi for vi in model.graph.value_info if vi.name not in io_names]
            del model.graph.value_info[:]
            model.graph.value_info.extend(new_value_info)
            
            # 儲存修復後的模型
            onnx.save(model, str(onnx_path))
            return True
            
        except Exception as e:
            print(f"修復 value_info 失敗: {onnx_path.name} | {e}")
            return False
    
    def check_onnx_model(self, onnx_path: Path, full_check: bool = True) -> Optional[str]:
        """
        檢查 ONNX 模型格式
        
        Args:
            onnx_path: ONNX 模型路徑
            full_check: 是否進行完整檢查
            
        Returns:
            錯誤訊息（如果檢查失敗），否則返回 None
        """
        try:
            onnx.checker.check_model(str(onnx_path), full_check=full_check)
            return None
        except onnx.checker.ValidationError as e:
            return str(e)
        except Exception as e:
            return f"檢查異常: {str(e)}"
    
    def batch_fix_onnx_models(self, onnx_files: List[Path]) -> List[Tuple[Path, bool]]:
        """
        批次修復多個 ONNX 模型
        
        Args:
            onnx_files: ONNX 檔案列表
            
        Returns:
            修復結果列表（檔案路徑, 是否成功）
        """
        results = []
        
        for onnx_path in onnx_files:
            success = self.fix_onnx_value_info(onnx_path)
            results.append((onnx_path, success))
            
            if success:
                print(f"[Auto] 修正 value_info: {onnx_path.name}")
            else:
                print(f"[Warning] 修正 value_info 失敗: {onnx_path.name}")
        
        return results
    
    def batch_check_onnx_models(self, onnx_files: List[Path]) -> List[Tuple[Path, Optional[str]]]:
        """
        批次檢查多個 ONNX 模型
        
        Args:
            onnx_files: ONNX 檔案列表
            
        Returns:
            檢查結果列表（檔案路徑, 錯誤訊息）
        """
        results = []
        invalid_models = []
        
        for onnx_path in onnx_files:
            error = self.check_onnx_model(onnx_path)
            results.append((onnx_path, error))
            
            if error:
                invalid_models.append((onnx_path.name, onnx_path, error))
                print(f"❌ ONNX 檢查失敗: {onnx_path.name} - {error}")
            else:
                print(f"✅ ONNX 檢查通過: {onnx_path.name}")
        
        return results, invalid_models
    
    def validate_model_support(self, device_attrs: List[str], model_format: str) -> bool:
        """
        驗證裝置是否支援特定模型格式
        
        Args:
            device_attrs: 裝置屬性列表
            model_format: 模型格式（'onnx', 'tflite', 'dlc'）
            
        Returns:
            是否支援
        """
        framework_key = f'framework:{model_format}'
        return any(framework_key in attr for attr in device_attrs)
    
    def get_device_support_info(self, device_attrs: List[str]) -> Dict[str, bool]:
        """
        取得裝置支援格式資訊
        
        Args:
            device_attrs: 裝置屬性列表
            
        Returns:
            支援格式字典
        """
        return {
            'onnx': self.validate_model_support(device_attrs, 'onnx'),
            'tflite': self.validate_model_support(device_attrs, 'tflite'),
            'dlc': self.validate_model_support(device_attrs, 'dlc')
        }


# 單例實例
format_checker = FormatChecker()


def fix_onnx_value_info(onnx_path: Path) -> bool:
    """
    快速修復 ONNX value_info
    
    Args:
        onnx_path: ONNX 模型路徑
        
    Returns:
        是否成功
    """
    return format_checker.fix_onnx_value_info(onnx_path)


def check_onnx_model(onnx_path: Path) -> Optional[str]:
    """
    快速檢查 ONNX 模型
    
    Args:
        onnx_path: ONNX 模型路徑
        
    Returns:
        錯誤訊息或 None
    """
    return format_checker.check_onnx_model(onnx_path)


def batch_fix_onnx_models(onnx_files: List[Path]) -> List[Tuple[Path, bool]]:
    """
    快速批次修復 ONNX 模型
    
    Args:
        onnx_files: ONNX 檔案列表
        
    Returns:
        修復結果
    """
    return format_checker.batch_fix_onnx_models(onnx_files)


def get_device_support(device_attrs: List[str]) -> Dict[str, bool]:
    """
    快速取得裝置支援資訊
    
    Args:
        device_attrs: 裝置屬性列表
        
    Returns:
        支援格式字典
    """
    return format_checker.get_device_support_info(device_attrs)


if __name__ == "__main__":
    # 測試程式
    test_dir = Path(__file__).parent.parent.parent / 'models' / 'onnx'
    
    if test_dir.exists():
        onnx_files = list(test_dir.glob('*.onnx'))
        if onnx_files:
            print(f"測試檢查 {len(onnx_files)} 個 ONNX 檔案...")
            results, invalid = format_checker.batch_check_onnx_models(onnx_files)
            
            if invalid:
                print(f"\n發現 {len(invalid)} 個無效模型：")
                for name, path, error in invalid:
                    print(f"  - {name}: {error}")
            else:
                print("所有模型檢查通過！")
        else:
            print("測試目錄中沒有 ONNX 檔案")
    else:
        print("測試目錄不存在")
