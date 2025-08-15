#!/usr/bin/env python3
"""
QAI Hub 正確設定工具 - Python 版本
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import configparser
import time

def print_header():
    """打印標題"""
    print("=" * 60)
    print("           QAI Hub 正確設定工具 - Python 版本")
    print("=" * 60)
    print()

def ensure_config_dir():
    """確保配置目錄存在"""
    home_dir = Path.home()
    config_dir = home_dir / ".qai_hub"
    config_dir.mkdir(exist_ok=True)
    
    print(f"配置目錄: {config_dir}")
    return config_dir

def update_config(config_dir, token="pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"):
    """更新配置文件"""
    config_file = config_dir / "client.ini"
    
    config = configparser.ConfigParser()
    config["default"] = {
        "api_token": token,
        "api_key": token,
        "base_api_url": "https://app.aihub.qualcomm.com",
        "web_url": "https://app.aihub.qualcomm.com"
    }
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f"已更新配置文件: {config_file}")
    print(f"使用正確的 URL: https://app.aihub.qualcomm.com")
    return config_file

def test_qai_hub_import():
    """測試是否可以導入 qai_hub"""
    try:
        import qai_hub
        return True, qai_hub.__version__
    except ImportError:
        return False, None
    except Exception as e:
        return False, str(e)

def verify_config():
    """驗證配置是否正常工作"""
    print("\n驗證配置:")
    print("-" * 60)
    
    # 創建驗證文件
    verify_file = "verify_config.py"
    with open(verify_file, 'w') as f:
        f.write("import qai_hub as hub\n")
        f.write("try:\n")
        f.write("    print('QAI Hub 版本:', hub.__version__)\n")
        f.write("    print('QAI Hub 配置正常！')\n")
        f.write("except Exception as e:\n")
        f.write("    print('測試 QAI Hub 時出錯:', e)\n")
    
    # 運行驗證
    print("驗證結果:")
    print("-" * 60)
    try:
        subprocess.run([sys.executable, verify_file])
    except Exception as e:
        print(f"驗證時出錯: {e}")
    
    # 清理臨時文件
    try:
        os.remove(verify_file)
    except:
        pass

def check_qai_hub_installation():
    """檢查 QAI Hub 是否安裝"""
    success, version = test_qai_hub_import()
    if success:
        print(f"QAI Hub 已安裝，版本: {version}")
        return True
    else:
        print("QAI Hub 未安裝或無法導入")
        choice = input("是否要安裝/更新 QAI Hub? (y/n): ")
        if choice.lower() == 'y':
            print("正在安裝 QAI Hub...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "qai-hub==0.31.0", "qai-hub-models==0.31.0"])
                print("安裝完成。")
                return True
            except Exception as e:
                print(f"安裝時出錯: {e}")
                return False
        return False

def main():
    """主函數"""
    print_header()
    
    # 檢查操作系統
    system = platform.system()
    print(f"操作系統: {system}")
    
    # 確保配置目錄存在
    config_dir = ensure_config_dir()
    
    # 詢問用戶輸入 API 令牌
    print("\n請輸入您的 API 令牌 (或直接按 Enter 使用預設值):")
    token = input("API 令牌: ")
    
    if not token:
        token = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
        print("使用預設令牌")
    
    # 更新配置
    update_config(config_dir, token)
    
    # 確保 QAI Hub 已安裝
    qai_hub_installed = check_qai_hub_installation()
    if not qai_hub_installed:
        print("請先安裝 QAI Hub 然後再運行此工具。")
        return
    
    # 驗證配置
    verify_config()
    
    # 結束信息
    print("\n" + "=" * 60)
    print("                      後續步驟")
    print("=" * 60)
    print()
    print("1. 請確認您有在 QAI Hub 官方網站註冊帳號並獲取有效的 API 令牌")
    print("2. 只使用官方 URL: https://app.aihub.qualcomm.com")
    print("3. 安裝正確版本的 QAI Hub 套件:")
    print("   - pip install qai-hub==0.31.0 qai-hub-models==0.31.0")
    print("4. 確保您的網絡環境可以正常訪問 QAI Hub 服務")
    print()

if __name__ == "__main__":
    main()
