#!/usr/bin/env python3
"""
QAI Hub client.ini 修復工具 - 加強版
確保 client.ini 文件格式正確並提供詳細診斷
"""

import os
import sys
import platform
import time
from pathlib import Path
import configparser
import shutil
import subprocess

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

def fix_client_ini():
    """修復 client.ini 文件格式 - 多種方法嘗試確保成功"""
    print_header("QAI Hub client.ini 修復工具")
    
    # 獲取 API 令牌 - 嘗試多個來源
    api_token = None
    
    # 使用新的固定 API 令牌
    api_token = 'pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d'
    print_info(f"使用指定的 API 令牌: {api_token}")
    
    # 檢查環境變量中是否有舊的令牌
    env_vars = ['QAI_HUB_API_TOKEN', 'QAI_API_KEY', 'QAI_HUB_API_KEY']
    for var in env_vars:
        if var in os.environ:
            old_token = os.environ[var]
            if old_token != api_token:
                print_warning(f"環境變量 {var} 中的 API 令牌已過時，將被更新")
            else:
                print_success(f"環境變量 {var} 中的 API 令牌已正確設置")
    
    # 同時設置所有可能的環境變量
    for var in env_vars:
        os.environ[var] = api_token
    print_info("已設置所有相關環境變量")
    
    # 記錄診斷信息
    print_info(f"操作系統: {platform.system()} {platform.release()}")
    print_info(f"Python 版本: {sys.version.split()[0]}")
    user_home = str(Path.home())
    print_info(f"用戶主目錄: {user_home}")
    
    # 創建配置目錄 - 嘗試多種方法
    config_dir = Path.home() / ".qai_hub"
    config_dir_str = str(config_dir)
    
    # 方法 1: 使用 pathlib
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"已確保 .qai_hub 目錄存在 (方法 1): {config_dir}")
    except Exception as e:
        print_error(f"使用 pathlib 創建目錄失敗: {e}")
        
        # 方法 2: 使用 os.makedirs
        try:
            os.makedirs(config_dir_str, exist_ok=True)
            print_success(f"已確保 .qai_hub 目錄存在 (方法 2)")
        except Exception as e:
            print_error(f"使用 os.makedirs 創建目錄失敗: {e}")
            
            # 方法 3: 使用系統命令
            try:
                if platform.system() == "Windows":
                    os.system(f'mkdir "{config_dir_str}" 2> nul')
                else:
                    os.system(f'mkdir -p "{config_dir_str}" 2>/dev/null')
                print_success(f"已嘗試使用系統命令創建目錄 (方法 3)")
            except Exception as e:
                print_error(f"使用系統命令創建目錄失敗: {e}")
    
    # 創建 client.ini 文件 - 嘗試多種方法
    client_ini = config_dir / "client.ini"
    client_ini_str = str(client_ini)
    
    # 備份舊文件（如果存在）
    if os.path.exists(client_ini_str):
        try:
            backup_path = f"{client_ini_str}.bak"
            shutil.copy2(client_ini_str, backup_path)
            print_info(f"已備份舊 client.ini 到 {backup_path}")
        except Exception as e:
            print_warning(f"備份 client.ini 失敗: {e}")
    
    # 方法 1: 使用 configparser
    created = False
    try:
        config = configparser.ConfigParser()
        # 使用兩種可能的格式：DEFAULT 和 default
        config['DEFAULT'] = {'api_key': api_token}
        # 也創建 default 區段並設置 api_token 和 api_key
        config['default'] = {
            'api_token': api_token,
            'api_key': api_token,
            'organization': '',
            'base_api_url': 'https://api.aihub.qualcomm.com',
            'web_url': 'https://app.aihub.qualcomm.com',
            'profile': 'default',
            'device_group': 'default',
            'model_path': 'models'
        }
        
        with open(client_ini_str, 'w') as f:
            config.write(f)
        print_success(f"已使用 configparser 創建 client.ini (方法 1)")
        created = True
    except Exception as e:
        print_error(f"使用 configparser 創建 client.ini 失敗: {e}")
        
        # 方法 2: 直接寫入
        if not created:
            try:
                with open(client_ini_str, 'w') as f:
                    f.write("[DEFAULT]\n")
                    f.write(f"api_key = {api_token}\n")
                    f.write("\n[default]\n")
                    f.write(f"api_token = {api_token}\n")
                    f.write(f"api_key = {api_token}\n")
                    f.write("organization = \n")
                    f.write("base_api_url = https://api.aihub.qualcomm.com\n")
                    f.write("web_url = https://app.aihub.qualcomm.com\n")
                    f.write("profile = default\n")
                    f.write("device_group = default\n")
                    f.write("model_path = models\n")
                print_success(f"已直接寫入 client.ini (方法 2)")
                created = True
            except Exception as e:
                print_error(f"直接寫入 client.ini 失敗: {e}")
                
                # 方法 3: 使用 Path 對象
                if not created:
                    try:
                        content = f"""[DEFAULT]
api_key = {api_token}

[default]
api_token = {api_token}
api_key = {api_token}
organization = 
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
profile = default
device_group = default
model_path = models
"""
                        Path(client_ini_str).write_text(content)
                        print_success(f"已使用 Path 對象寫入 client.ini (方法 3)")
                        created = True
                    except Exception as e:
                        print_error(f"使用 Path 對象寫入 client.ini 失敗: {e}")
                        
                        # 方法 4: 使用系統命令
                        if not created:
                            try:
                                if platform.system() == "Windows":
                                    cmd = f'echo [DEFAULT] > "{client_ini_str}" && echo api_key = {api_token} >> "{client_ini_str}" && echo. >> "{client_ini_str}" && echo [default] >> "{client_ini_str}" && echo api_token = {api_token} >> "{client_ini_str}" && echo api_key = {api_token} >> "{client_ini_str}" && echo organization = >> "{client_ini_str}" && echo base_api_url = https://api.aihub.qualcomm.com >> "{client_ini_str}" && echo web_url = https://app.aihub.qualcomm.com >> "{client_ini_str}" && echo profile = default >> "{client_ini_str}" && echo device_group = default >> "{client_ini_str}" && echo model_path = models >> "{client_ini_str}"'
                                    os.system(cmd)
                                else:
                                    cmd = f'''echo -e "[DEFAULT]\\napi_key = {api_token}\\n\\n[default]\\napi_token = {api_token}\\napi_key = {api_token}\\norganization = \\nbase_api_url = https://api.aihub.qualcomm.com\\nweb_url = https://app.aihub.qualcomm.com\\nprofile = default\\ndevice_group = default\\nmodel_path = models" > "{client_ini_str}"'''
                                    os.system(cmd)
                                print_success(f"已使用系統命令創建 client.ini (方法 4)")
                                created = True
                            except Exception as e:
                                print_error(f"使用系統命令創建 client.ini 失敗: {e}")
    
    # 檢查文件是否正確創建
    verified = False
    if os.path.exists(client_ini_str):
        print_success(f"client.ini 文件存在")
        try:
            with open(client_ini_str, 'r') as f:
                content = f.read()
                if "[DEFAULT]" in content and "api_key" in content:
                    print_success("client.ini 格式正確")
                    verified = True
                else:
                    print_warning("client.ini 格式不正確")
                
                print_info(f"client.ini 內容:\n{colorize(content, Colors.BOLD)}")
        except Exception as e:
            print_error(f"讀取 client.ini 失敗: {e}")
    else:
        print_error(f"client.ini 文件不存在")
    
    # 最終確認
    if verified:
        print_success("client.ini 文件已成功創建並驗證!")
    else:
        print_warning("client.ini 文件可能創建失敗或格式不正確")
    
    return created

def test_qai_hub():
    """測試 QAI Hub 連接 - 更全面的診斷"""
    print_header("測試 QAI Hub 連接")
    
    # 檢查是否安裝了 qai_hub 包
    try:
        import importlib
        qai_hub_spec = importlib.util.find_spec("qai_hub")
        if qai_hub_spec is None:
            print_error("未安裝 qai_hub 包")
            print_info("請安裝 qai_hub: pip install qai-hub")
            return False
        else:
            print_success("已安裝 qai_hub 包")
    except Exception as e:
        print_error(f"檢查 qai_hub 安裝時出錯: {e}")
    
    # 檢查 protobuf 版本
    try:
        import pkg_resources
        protobuf_version = pkg_resources.get_distribution("protobuf").version
        print_info(f"protobuf 版本: {protobuf_version}")
        
        if protobuf_version == "4.25.3":
            print_success("protobuf 版本正確 (4.25.3)")
        else:
            print_warning(f"protobuf 版本 ({protobuf_version}) 可能不兼容")
            print_info("建議安裝 4.25.3 版本: pip install protobuf==4.25.3")
    except Exception as e:
        print_warning(f"無法確定 protobuf 版本: {e}")
    
    # 嘗試導入 qai_hub
    try:
        import qai_hub as hub
        print_success(f"成功導入 qai_hub 模塊 (版本: {getattr(hub, '__version__', '未知')})")
        
        # 嘗試連接到 QAI Hub
        print_info("正在連接到 QAI Hub API...")
        try:
            # 嘗試獲取設備列表
            devices = hub.get_devices()
            print_success(f"成功連接到 QAI Hub!")
            print_success(f"可用設備數量: {len(devices)}")
            
            if devices:
                print_info("可用設備列表:")
                for i, device in enumerate(devices):
                    print(f"   {i+1}. {colorize(device.name, Colors.BOLD)}")
            
            # 嘗試獲取模型列表
            try:
                models = hub.get_available_models()
                print_success(f"可用模型數量: {len(models)}")
                if models and len(models) > 0:
                    print_info("前 5 個可用模型:")
                    for i, model in enumerate(models[:5]):
                        print(f"   {i+1}. {colorize(model.name, Colors.BOLD)}")
            except Exception as e:
                print_warning(f"獲取模型列表失敗: {e}")
            
            return True
        except Exception as e:
            print_error(f"獲取設備失敗: {e}")
            
            # 嘗試一個更簡單的 API 調用
            try:
                print_info("嘗試一個更簡單的 API 調用...")
                user = hub.get_user()
                print_success(f"成功調用 API! 用戶 ID: {user.id}")
                return True
            except Exception as e2:
                print_error(f"簡單 API 調用也失敗: {e2}")
                return False
            
    except ImportError:
        print_error("無法導入 qai_hub 模塊。請確保已安裝: pip install qai-hub")
        return False
    except Exception as e:
        print_error(f"導入 qai_hub 時出錯: {e}")
        return False

def check_network():
    """檢查網絡連接"""
    print_info("檢查網絡連接...")
    
    # 測試連接 QAI Hub API 端點
    test_urls = [
        "api.qai-hub.qualcomm.com",
        "qualcomm.com"
    ]
    
    all_ok = True
    for url in test_urls:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["ping", "-n", "1", url], 
                                       capture_output=True, text=True, timeout=5)
            else:
                result = subprocess.run(["ping", "-c", "1", url], 
                                       capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print_success(f"可以連接到 {url}")
            else:
                print_error(f"無法連接到 {url}")
                all_ok = False
        except Exception as e:
            print_warning(f"測試連接 {url} 時出錯: {e}")
            all_ok = False
    
    return all_ok

def diagnose_system():
    """全面診斷系統狀態"""
    print_header("系統診斷")
    
    # 基本系統信息
    print_info(f"操作系統: {platform.system()} {platform.release()}")
    print_info(f"架構: {platform.machine()}")
    print_info(f"Python 版本: {sys.version.split()[0]}")
    
    # 檢查是否是 ARM64 架構
    is_arm64 = platform.machine().lower() in ['arm64', 'aarch64']
    if is_arm64:
        print_info("檢測到 ARM64 架構")
    
    # 檢查 QAI 相關環境變量
    env_vars = ['QAI_HUB_API_TOKEN', 'QAI_API_KEY', 'PYTHONPATH', 'PATH']
    for var in env_vars:
        if var in os.environ:
            value = os.environ[var]
            # 如果是 API 密鑰，隱藏部分內容
            if 'API' in var:
                masked_value = value[:5] + '*' * (len(value) - 10) + value[-5:] if len(value) > 10 else '***'
                print_info(f"環境變量 {var}: {masked_value}")
            else:
                print_info(f"環境變量 {var}: 已設置")
        else:
            print_warning(f"環境變量 {var}: 未設置")
    
    # 返回診斷結果
    return True

def main():
    """主函數"""
    print_header("QAI Hub 診斷與修復工具")
    
    # 步驟 1: 診斷系統
    diagnose_system()
    
    # 步驟 2: 檢查網絡
    check_network()
    
    # 步驟 3: 修復 client.ini
    client_ini_fixed = fix_client_ini()
    
    # 步驟 4: 測試 QAI Hub 連接
    connection_ok = test_qai_hub()
    
    # 總結
    print_header("診斷摘要")
    if client_ini_fixed and connection_ok:
        print_success("✨ 所有問題已修復! QAI Hub 配置正常 ✨")
    elif client_ini_fixed:
        print_warning("⚠️ client.ini 已修復，但 QAI Hub 連接測試失敗")
    else:
        print_error("❌ 修復失敗")
    
    # 故障排除建議
    print_header("故障排除建議")
    print_info("1. 確保 client.ini 文件格式正確:")
    print(colorize("   [DEFAULT]", Colors.BOLD))
    print(colorize("   api_key = your_api_key_here", Colors.BOLD))
    print_info("2. 確保 protobuf 版本兼容: pip install protobuf==4.25.3")
    print_info("3. 重新安裝 qai-hub: pip install -U qai-hub")
    print_info("4. 檢查環境變量: echo %QAI_HUB_API_TOKEN%")
    print_info("5. 檢查網絡連接")
    print_info("6. 嘗試重啟電腦後再試一次")
    print_info("7. 檢查防火牆設置，確保允許 Python 連接網絡")

if __name__ == "__main__":
    main()
