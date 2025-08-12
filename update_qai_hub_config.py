#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QAI Hub 配置更新工具

此工具用於更新 QAI Hub 配置，特別是將 API URL 從舊格式 (api.qai-hub.qualcomm.com)
更新為新格式 (api.aihub.qualcomm.com)，並幫助設置正確的 API token。

用法:
    python update_qai_hub_config.py [--token YOUR_API_TOKEN]
"""

import os
import sys
import argparse
import platform
import subprocess
from pathlib import Path

def get_config_dir():
    """獲取 QAI Hub 配置目錄"""
    home = Path.home()
    return home / ".qai-hub"

def backup_existing_config(config_file):
    """備份現有配置文件"""
    if not config_file.exists():
        return False
    
    backup_file = config_file.with_name(f"{config_file.name}.backup")
    try:
        with open(config_file, 'r') as src:
            with open(backup_file, 'w') as dst:
                dst.write(src.read())
        print(f"已將舊配置備份到 {backup_file}")
        return True
    except Exception as e:
        print(f"備份配置時出錯: {e}")
        return False

def update_config_file(token=None):
    """更新配置文件"""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "client.ini"
    backup_existing_config(config_file)
    
    # 如果沒有提供 token，嘗試從現有配置獲取
    if token is None and config_file.exists():
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith("api_token ="):
                        token = line.split("=")[1].strip()
                        break
                    if line.startswith("api_key ="):
                        token = line.split("=")[1].strip()
                        break
        except Exception:
            pass
    
    # 如果仍然沒有 token，使用默認值
    if token is None:
        token = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
        print("注意: 使用默認 API token。建議從 QAI Hub 網站獲取您自己的 API token。")
    
    # 創建新的配置文件
    config_content = f"""[default]
api_token = {token}
api_key = {token}
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"已更新配置文件: {config_file}")
    print("新 API URL: https://api.aihub.qualcomm.com")
    
    return True

def run_qai_hub_configure(token):
    """運行 qai-hub configure 命令"""
    if token is None:
        print("跳過 qai-hub configure 命令 (未提供 token)")
        return False
    
    try:
        print(f"執行: qai-hub configure --api_token {token[:5]}...(省略)")
        subprocess.check_call([sys.executable, "-m", "qai_hub.cli.configure", "--api_token", token])
        print("已成功配置 QAI Hub")
        return True
    except subprocess.CalledProcessError as e:
        print(f"配置 QAI Hub 時出錯: {e}")
        return False
    except FileNotFoundError:
        print("警告: 未找到 qai-hub 命令，可能需要安裝 QAI Hub SDK")
        print("建議運行: pip install -U qai-hub qai-hub-models")
        return False

def check_sdk_installation():
    """檢查 QAI Hub SDK 安裝"""
    try:
        import qai_hub
        version = getattr(qai_hub, "__version__", "未知")
        print(f"已安裝 QAI Hub SDK 版本: {version}")
        return True
    except ImportError:
        print("警告: 未安裝 QAI Hub SDK")
        print("建議運行: pip install -U qai-hub qai-hub-models")
        return False

def check_windows_arm():
    """檢查是否在 Windows ARM 環境中運行"""
    if platform.system() == "Windows":
        if platform.machine().lower() in ["arm64", "aarch64"]:
            print("\n注意: 檢測到 Windows on ARM 環境 (如 Snapdragon X)")
            print("QAI Hub 客戶端暫不支援原生 ARM Python，請使用 x64 版 Python 3.10")
            
            # 檢測 Python 環境
            is_arm_python = platform.architecture()[0] == "64bit" and platform.machine().lower() in ["arm64", "aarch64"]
            if is_arm_python:
                print("警告: 您正在使用 ARM 版 Python，可能無法正常使用 QAI Hub")
                print("建議安裝 x64 版 Python 3.10")
            return True
    return False

def check_windows_long_path():
    """檢查 Windows 長路徑支援"""
    if platform.system() != "Windows":
        return False
    
    try:
        # 檢查長路徑是否已啟用
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
            if value == 1:
                print("Windows 長路徑支援已啟用")
                return True
            else:
                print("\n警告: Windows 長路徑支援未啟用")
                print("安裝某些 Python 套件時可能會遇到路徑過長錯誤")
                print("解決方法:")
                print("1. 以管理員身份開啟 PowerShell，執行:")
                print("   Set-ItemProperty -Path \"HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem\" -Name \"LongPathsEnabled\" -Value 1 -Type DWord")
                print("2. 重新啟動電腦")
                print("3. 或者使用短路徑的虛擬環境，例如:")
                print("   python -m venv C:\\qai_env")
                return False
    except Exception:
        print("無法檢查 Windows 長路徑支援狀態")
        return False

def verify_configuration():
    """驗證配置是否成功"""
    try:
        print("\n驗證配置...")
        import qai_hub as hub
        devices = hub.get_devices()
        print(f"可用設備: {devices}")
        print("配置驗證成功!")
        return True
    except ImportError:
        print("無法驗證配置: QAI Hub SDK 未安裝")
        return False
    except Exception as e:
        print(f"配置驗證失敗: {e}")
        return False

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="QAI Hub 配置更新工具")
    parser.add_argument("--token", help="您的 QAI Hub API token")
    args = parser.parse_args()
    
    print("\n========== QAI Hub 配置更新工具 ==========\n")
    
    # 檢查 Windows ARM 環境
    check_windows_arm()
    
    # 檢查 Windows 長路徑支援
    if platform.system() == "Windows":
        check_windows_long_path()
    
    # 檢查 SDK 安裝
    check_sdk_installation()
    
    # 更新配置文件
    update_config_file(args.token)
    
    # 使用 qai-hub configure 命令
    run_qai_hub_configure(args.token)
    
    # 驗證配置
    verify_configuration()
    
    print("\n配置更新完成!")
    print("""
下一步:
1. 如果尚未安裝 QAI Hub SDK，請運行:
   pip install -U qai-hub qai-hub-models

2. 驗證配置:
   import qai_hub as hub
   print(hub.get_devices())
""")

if __name__ == "__main__":
    main()
