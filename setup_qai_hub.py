#!/usr/bin/env python3
"""
QAI Hub 設置工具 - 增強版
在 Snapdragon X Elite 平台設置 QAI Hub 認證，並提供全面的診斷和修復功能
"""

import os
import sys
import configparser
import platform
import time
import traceback
import subprocess
from pathlib import Path
import json
import argparse
import shutil

# 在 Windows 啟用 ANSI 顏色支持
if platform.system() == "Windows":
    os.system("")

# 定義顏色輸出
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colorize(text, color):
    """添加顏色到文本"""
    return f"{color}{text}{Colors.END}"

def print_header(text):
    """打印帶有顏色的標題"""
    print(f"\n{colorize('='*70, Colors.BOLD)}")
    print(f"{colorize(f'  {text}', Colors.BOLD)}")
    print(f"{colorize('='*70, Colors.BOLD)}\n")

def print_success(text):
    """打印成功訊息"""
    print(f"{colorize('✅ ', Colors.GREEN)}{text}")

def print_error(text):
    """打印錯誤訊息"""
    print(f"{colorize('❌ ', Colors.RED)}{text}")

def print_warning(text):
    """打印警告訊息"""
    print(f"{colorize('⚠️ ', Colors.YELLOW)}{text}")

def print_info(text):
    """打印信息訊息"""
    print(f"{colorize('ℹ️ ', Colors.BLUE)}{text}")

def get_api_token_from_sources(config_path=None, verbose=True):
    """從多個來源獲取 API 令牌"""
    # 使用固定的新 API 令牌
    api_token = 'pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d'
    if verbose:
        print_info("使用指定的 API 令牌")
    
    # 檢查命令行參數中是否提供了令牌
    if config_path and config_path != api_token:
        if verbose:
            print_warning(f"提供的參數與指定的 API 令牌不同，將使用指定的令牌")
    
    # 檢查環境變量是否有舊令牌
    env_vars = ['QAI_HUB_API_TOKEN', 'QAI_API_KEY', 'QAI_HUB_API_KEY']
    for var in env_vars:
        if var in os.environ and os.environ[var] != api_token:
            if verbose:
                print_warning(f"環境變量 {var} 中的 API 令牌與指定的不同，將使用指定的令牌")
            # 更新環境變量
            os.environ[var] = api_token
    
    return api_token
    return api_token

def setup_qai_hub_credentials(api_token=None, force=False, verbose=True):
    """設置 QAI Hub 認證 - 增強版"""
    if verbose:
        print_header("QAI Hub 認證設置工具")
    
    # 獲取 API 令牌
    api_token = get_api_token_from_sources(api_token, verbose)
    
    # 檢查令牌格式
    if not api_token or len(api_token) < 10:
        print_error("API 令牌格式不正確或為空")
        print_info("正確的 API 令牌應為長字符串，例如: pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d")
        if not force:
            print_info("請訪問 https://aihub.qualcomm.com/ 獲取訪問權限")
            print_info("如果您已有訪問權限，請參考 https://app.aihub.qualcomm.com/docs 獲取設置說明")
            user_token = input("請輸入您的 QAI Hub API 令牌（或按 Enter 使用默認值）: ").strip()
            if user_token:
                api_token = user_token
    
    # 記錄系統信息
    if verbose:
        print_info(f"操作系統: {platform.system()} {platform.release()}")
        print_info(f"Python 版本: {sys.version.split()[0]}")
        print_info(f"用戶主目錄: {str(Path.home())}")
    
    # 創建 QAI Hub 配置目錄 - 多種嘗試方式
    config_dir = Path.home() / ".qai_hub"
    config_dir_str = str(config_dir)
    
    try:
        # 方法 1: 使用 pathlib
        config_dir.mkdir(parents=True, exist_ok=True)
        if verbose:
            print_success(f"QAI Hub 配置目錄已確保存在: {config_dir}")
    except Exception as e:
        print_error(f"創建配置目錄失敗: {e}")
        try:
            # 方法 2: 使用 os.makedirs
            os.makedirs(config_dir_str, exist_ok=True)
            if verbose:
                print_success("使用 os.makedirs 成功創建配置目錄")
        except Exception as e2:
            print_error(f"使用 os.makedirs 創建目錄也失敗: {e2}")
            return False
    
    # 備份現有文件
    config_file = config_dir / "client.ini"
    if config_file.exists() and not force:
        try:
            backup_file = config_dir / f"client.ini.bak.{int(time.time())}"
            shutil.copy2(config_file, backup_file)
            if verbose:
                print_success(f"已備份現有配置文件到: {backup_file}")
        except Exception as e:
            if verbose:
                print_warning(f"備份配置文件失敗: {e}")
    
    # 創建配置文件 - 多種嘗試方式
    success = False
    
    # 方法 1: 使用 configparser
    try:
        config = configparser.ConfigParser()
        config['default'] = {
            'api_token': api_token,
            'api_key': api_token,
            'base_api_url': 'https://api.qai-hub.qualcomm.com',
            'web_url': 'https://app.aihub.qualcomm.com'
        }
        
        with open(config_file, 'w') as f:
            config.write(f)
        
        if verbose:
            print_success(f"使用 configparser 成功創建配置文件: {config_file}")
        success = True
    except Exception as e:
        print_error(f"使用 configparser 創建配置文件失敗: {e}")
        
        # 方法 2: 直接寫入文件
        try:
            with open(config_file, 'w') as f:
                f.write("[default]\n")
                f.write(f"api_token = {api_token}\n")
                f.write(f"api_key = {api_token}\n")
                f.write("base_api_url = https://api.qai-hub.qualcomm.com\n")
                f.write("web_url = https://app.aihub.qualcomm.com\n")
            
            if verbose:
                print_success("使用直接寫入方式成功創建配置文件")
            success = True
        except Exception as e2:
            print_error(f"直接寫入配置文件也失敗: {e2}")
            return False
    
    # 設置環境變量
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    os.environ['QAI_API_KEY'] = api_token
    
    if verbose:
        print_success("QAI Hub 環境變量已設置")
    
    # 創建示例 QAI Hub 配置文件
    example_config = {
        "api_token": 'pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d',
        "device_preference": "Snapdragon X Elite CRD",
        "fallback_device": "Snapdragon X Plus 8-Core CRD",
        "inference_backend": "QNN",
        "model_optimization": True,
        "arm64_native": True,
        "use_directml_fallback": True
    }
    
    example_config_path = Path.cwd() / "qai_hub_config.json"
    try:
        with open(example_config_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2)
        
        if verbose:
            print_success(f"QAI Hub 配置範例已創建: {example_config_path}")
    except Exception as e:
        if verbose:
            print_warning(f"創建配置範例失敗: {e}")
    
    # 創建 .env 文件
    env_path = Path.home() / ".env"
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f"QAI_HUB_API_TOKEN={api_token}\n")
            f.write(f"QAI_API_KEY={api_token}\n")
        
        if verbose:
            print_success(f"環境變量設置已儲存至 .env 文件: {env_path}")
    except Exception as e:
        if verbose:
            print_warning(f"創建 .env 文件失敗: {e}")
    
    # 檢查配置文件
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if verbose:
                    print_info(f"配置文件內容:\n{colorize(content, Colors.BOLD)}")
                
                # 驗證格式
                if "[DEFAULT]" in content and "api_key" in content:
                    if verbose:
                        print_success("配置文件格式正確")
                else:
                    print_warning("配置文件格式可能不正確，請確保包含 [DEFAULT] 和 api_key 字段")
        except Exception as e:
            if verbose:
                print_warning(f"讀取配置文件失敗: {e}")
    
    return success

def check_qai_hub_installation():
    """檢查 QAI Hub SDK 安裝狀態"""
    print_info("檢查 QAI Hub SDK 安裝...")
    
    try:
        import importlib
        qai_hub_spec = importlib.util.find_spec("qai_hub")
        if qai_hub_spec is None:
            print_error("未安裝 QAI Hub SDK")
            print_info("請安裝 QAI Hub SDK: pip install qai-hub")
            return False
        else:
            import qai_hub
            print_success(f"QAI Hub SDK 已安裝，版本: {getattr(qai_hub, '__version__', '未知')}")
            return True
    except ImportError:
        print_error("未安裝 QAI Hub SDK")
        print_info("請安裝 QAI Hub SDK: pip install qai-hub")
        return False
    except Exception as e:
        print_error(f"檢查 QAI Hub SDK 安裝時出錯: {e}")
        return False

def check_protobuf_version():
    """檢查 protobuf 版本"""
    print_info("檢查 protobuf 版本...")
    
    try:
        import pkg_resources
        protobuf_version = pkg_resources.get_distribution("protobuf").version
        print_info(f"protobuf 版本: {protobuf_version}")
        
        if protobuf_version == "4.25.3":
            print_success("protobuf 版本正確 (4.25.3)")
            return True
        else:
            print_warning(f"protobuf 版本 ({protobuf_version}) 可能不兼容")
            print_info("建議安裝 4.25.3 版本: pip install protobuf==4.25.3")
            return False
    except Exception as e:
        print_warning(f"無法確定 protobuf 版本: {e}")
        return False

def check_network(domain="api.qai-hub.qualcomm.com"):
    """檢查網絡連接"""
    print_info(f"檢查與 {domain} 的網絡連接...")
    
    try:
        if platform.system() == "Windows":
            ping_cmd = ["ping", "-n", "1", domain]
        else:
            ping_cmd = ["ping", "-c", "1", domain]
        
        result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print_success(f"可以連接到 {domain}")
            return True
        else:
            print_error(f"無法連接到 {domain}")
            print_info("請檢查您的網絡連接和防火牆設置")
            return False
    except Exception as e:
        print_error(f"執行網絡檢查時出錯: {e}")
        return False

def test_qai_hub_connection(verbose=True):
    """測試 QAI Hub 連接 - 增強版"""
    if verbose:
        print_header("測試 QAI Hub 連接")
    
    # 檢查 QAI Hub SDK 安裝
    sdk_installed = check_qai_hub_installation()
    if not sdk_installed:
        return False
    
    # 檢查 protobuf 版本
    check_protobuf_version()
    
    # 檢查網絡連接
    check_network("api.qai-hub.qualcomm.com")
    
    # 嘗試連接 QAI Hub
    try:
        if verbose:
            print_info("嘗試連接到 QAI Hub API...")
        
        import qai_hub as hub
        
        # 捕獲詳細錯誤信息
        try:
            # 獲取設備列表
            devices = hub.get_devices()
            if verbose:
                print_success(f"成功連接到 QAI Hub!")
                print_success(f"可用設備數量: {len(devices)}")
                
                if devices:
                    print_info("可用設備列表:")
                    for i, device in enumerate(devices):
                        print(f"   {i+1}. {colorize(device.name, Colors.BOLD)}")
            
            # 嘗試獲取模型列表
            try:
                models = hub.get_available_models()
                if verbose:
                    print_success(f"可用模型數量: {len(models)}")
                    if models and len(models) > 0:
                        print_info("可用模型示例:")
                        for i, model in enumerate(models[:3]):  # 只顯示前3個
                            print(f"   {i+1}. {colorize(model.name, Colors.BOLD)}")
            except Exception as e:
                if verbose:
                    print_warning(f"獲取模型列表失敗: {e}")
            
            return True
        except Exception as e:
            error_msg = str(e)
            if verbose:
                print_error(f"連接 QAI Hub 失敗: {error_msg}")
                
                # 特定錯誤的處理建議
                if "Failed to load configuration file" in error_msg:
                    print_error("配置文件加載失敗")
                    print_info("解決方案:")
                    print_info("1. 確認 ~/.qai_hub/client.ini 文件存在")
                    print_info("2. 確認文件格式正確 (必須包含 [DEFAULT] 和 api_key)")
                    print_info("3. 執行 fix_qai_hub_client.bat 修復配置")
                elif "Invalid API key" in error_msg or "API key validation failed" in error_msg:
                    print_error("API 密鑰無效或驗證失敗")
                    print_info("解決方案:")
                    print_info("1. 獲取有效的 API 密鑰")
                    print_info("2. 在 ~/.qai_hub/client.ini 中設置正確的 API 密鑰")
                elif "Connection refused" in error_msg or "Could not connect" in error_msg:
                    print_error("連接被拒絕")
                    print_info("解決方案:")
                    print_info("1. 檢查網絡連接")
                    print_info("2. 檢查防火牆設置")
                    print_info("3. 確認 QAI Hub 服務是否可用")
                
                # 顯示錯誤詳情和調用堆棧
                if verbose:
                    print_info("錯誤詳情:")
                    traceback.print_exc()
            
            # 嘗試更簡單的 API 調用
            try:
                if verbose:
                    print_info("嘗試更簡單的 API 調用...")
                user = hub.get_user()
                if verbose:
                    print_success(f"API 調用成功! 用戶 ID: {user.id}")
                return True
            except Exception as e2:
                if verbose:
                    print_error(f"API 調用失敗: {e2}")
                return False
    except ImportError:
        if verbose:
            print_error("導入 qai_hub 模塊失敗")
            print_info("請確保已安裝: pip install qai-hub")
        return False
    except Exception as e:
        if verbose:
            print_error(f"測試連接時出現未預期的錯誤: {e}")
            traceback.print_exc()
        return False

def diagnose_system():
    """診斷系統配置"""
    print_header("系統診斷")
    
    # 基本系統信息
    print_info(f"操作系統: {platform.system()} {platform.release()}")
    print_info(f"Python 版本: {sys.version.split()[0]}")
    print_info(f"系統架構: {platform.machine()}")
    
    # 檢查 ARM64 架構
    is_arm64 = platform.machine().lower() in ['arm64', 'aarch64']
    if is_arm64:
        print_success("檢測到 ARM64 架構，適合 Snapdragon 優化")
    else:
        print_info(f"當前架構: {platform.machine()}")
    
    # 檢查 Python 環境
    print_info("檢查 Python 環境...")
    try:
        # 檢查 pip
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"pip 已安裝: {result.stdout.strip()}")
        else:
            print_error("pip 未安裝或不可用")
    except Exception as e:
        print_error(f"檢查 pip 時出錯: {e}")
    
    # 檢查相關模塊
    modules_to_check = ['numpy', 'cv2', 'qai_hub', 'onnxruntime', 'protobuf', 'mediapipe']
    for module in modules_to_check:
        try:
            import importlib
            module_spec = importlib.util.find_spec(module)
            if module_spec is not None:
                try:
                    mod = importlib.import_module(module)
                    version = getattr(mod, '__version__', 'unknown')
                    print_success(f"{module} 已安裝，版本: {version}")
                except Exception:
                    print_success(f"{module} 已安裝")
            else:
                print_info(f"{module} 未安裝")
        except Exception:
            print_info(f"{module} 導入失敗")
    
    # 檢查環境變量
    env_vars = ['QAI_HUB_API_TOKEN', 'QAI_API_KEY', 'PYTHONPATH', 'PATH']
    for var in env_vars:
        if var in os.environ:
            if 'API' in var or 'TOKEN' in var:
                # 隱藏 API 密鑰
                value = os.environ[var]
                masked_value = value[:5] + '*' * (len(value) - 10) + value[-5:] if len(value) > 10 else '***'
                print_success(f"環境變量 {var} 已設置: {masked_value}")
            else:
                print_success(f"環境變量 {var} 已設置")
        else:
            print_info(f"環境變量 {var} 未設置")
    
    # 檢查配置文件
    config_file = Path.home() / ".qai_hub" / "client.ini"
    if config_file.exists():
        print_success(f"QAI Hub 配置文件存在: {config_file}")
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                if "[DEFAULT]" in content and "api_key" in content:
                    print_success("配置文件格式正確")
                else:
                    print_warning("配置文件格式可能不正確")
        except Exception as e:
            print_warning(f"讀取配置文件失敗: {e}")
    else:
        print_error(f"QAI Hub 配置文件不存在: {config_file}")
    
    # 檢查網絡連接
    check_network("qualcomm.com")
    check_network("api.qai-hub.qualcomm.com")
    
    return True

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='QAI Hub 設置與診斷工具')
    parser.add_argument('--token', type=str, help='QAI Hub API 令牌')
    parser.add_argument('--test', action='store_true', help='測試 QAI Hub 連接')
    parser.add_argument('--force', action='store_true', help='強制重新設置所有配置')
    parser.add_argument('--diagnose', action='store_true', help='診斷系統配置')
    parser.add_argument('--quiet', action='store_true', help='安靜模式，減少輸出')
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    print_header("QAI Hub 設置與診斷工具")
    
    if args.diagnose:
        # 系統診斷
        diagnose_system()
    
    if args.test:
        # 只進行測試
        test_qai_hub_connection(verbose)
    else:
        # 設置認證
        success = setup_qai_hub_credentials(args.token, args.force, verbose)
        
        if success:
            if args.force or input("是否測試 QAI Hub 連接? (y/n): ").lower() == 'y':
                test_qai_hub_connection(verbose)
        
    print_header("設置摘要")
    config_file = Path.home() / ".qai_hub" / "client.ini"
    if config_file.exists():
        print_success("QAI Hub 配置文件已創建")
        print_info(f"配置文件路徑: {config_file}")
        print_info("您現在應該可以使用 QAI Hub SDK 了")
    else:
        print_error("QAI Hub 配置文件未成功創建")
        print_info("請嘗試以下操作:")
        print_info("1. 運行 fix_qai_hub_client.bat")
        print_info("2. 手動創建配置文件")
        print_info("3. 檢查用戶目錄權限")
    
    # 建議
    print_header("後續步驟")
    print_info("1. 運行 dragon_x_fall_detection_system.py 啟動系統")
    print_info("2. 如遇問題，請運行 fix_dependencies.bat 修復依賴")
    print_info("3. 確保安裝了正確版本的 protobuf: pip install protobuf==4.25.3")
    print_info("4. 在 ARM64 設備上，啟用 Snapdragon 加速: python enable_snapdragon_acceleration.py")

if __name__ == "__main__":
    main()
