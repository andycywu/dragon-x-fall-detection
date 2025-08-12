#!/usr/bin/env python3
"""
QAI Hub URL 切換工具 - Python 版本
用於測試 QAI Hub 的新舊 API URL 並使用能正常工作的那個
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
    print("           QAI Hub URL 切換工具 - Python 版本")
    print("=" * 60)
    print()

def ensure_config_dir():
    """確保配置目錄存在"""
    home_dir = Path.home()
    config_dir = home_dir / ".qai_hub"
    config_dir.mkdir(exist_ok=True)
    
    print(f"配置目錄: {config_dir}")
    return config_dir

def update_config(config_dir, api_url, web_url, token="pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"):
    """更新配置文件"""
    config_file = config_dir / "client.ini"
    
    config = configparser.ConfigParser()
    config["default"] = {
        "api_token": token,
        "api_key": token,
        "base_api_url": api_url,
        "web_url": web_url
    }
    
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f"已更新配置文件: {config_file}")
    print(f"使用 API URL: {api_url}")
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

def test_api_url(config_dir, url_type):
    """測試 API URL 是否可用"""
    if url_type == "new":
        api_url = "https://api.aihub.qualcomm.com"
        web_url = "https://app.aihub.qualcomm.com"
    else:
        api_url = "https://api.qai-hub.qualcomm.com"
        web_url = "https://app.aihub.qualcomm.com"
    
    print(f"測試 {url_type} API URL: {api_url}")
    update_config(config_dir, api_url, web_url)
    
    # 創建臨時測試文件
    test_file = "test_url.py"
    with open(test_file, 'w') as f:
        f.write("import qai_hub\n")
        f.write("print('QAI Hub URL 測試成功')\n")
    
    # 等待配置生效
    time.sleep(2)
    
    # 運行測試
    try:
        result = subprocess.run([sys.executable, test_file], 
                               capture_output=True, text=True, timeout=10)
        success = result.returncode == 0
    except Exception:
        success = False
    
    # 清理臨時文件
    try:
        os.remove(test_file)
    except:
        pass
    
    return success, api_url

def verify_config(config_dir):
    """驗證配置是否正常工作"""
    print("\n驗證配置:")
    print("-" * 60)
    
    # 創建驗證文件
    verify_file = "verify_config.py"
    with open(verify_file, 'w') as f:
        f.write("import qai_hub as hub\n")
        f.write("print('QAI Hub 版本:', hub.__version__)\n")
        f.write("try:\n")
        f.write("    devices = hub.get_devices()\n")
        f.write("    print('可用設備:', devices)\n")
        f.write("    print('QAI Hub 配置正常工作！')\n")
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
                subprocess.run([sys.executable, "-m", "pip", "install", "-U", "qai-hub", "qai-hub-models"])
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
    
    # 確保 QAI Hub 已安裝
    qai_hub_installed = check_qai_hub_installation()
    if not qai_hub_installed:
        print("請先安裝 QAI Hub 然後再運行此工具。")
        return
    
    # 確保配置目錄存在
    config_dir = ensure_config_dir()
    
    # 詢問用戶選擇
    print("\n選擇要使用的 API URL:")
    print("1. 新 API URL (api.aihub.qualcomm.com) - 適用於較新版本")
    print("2. 舊 API URL (api.qai-hub.qualcomm.com) - 適用於較舊版本")
    print("3. 測試兩者並使用有效的那個 (推薦)")
    
    choice = input("請輸入選項 (1, 2, or 3): ")
    
    if choice == "1":
        api_url = "https://api.aihub.qualcomm.com"
        web_url = "https://app.aihub.qualcomm.com"
        update_config(config_dir, api_url, web_url)
    elif choice == "2":
        api_url = "https://api.qai-hub.qualcomm.com"
        web_url = "https://app.aihub.qualcomm.com"
        update_config(config_dir, api_url, web_url)
    else:
        # 測試兩個 URL
        print("\n測試兩個 API URL...")
        
        # 先測試新 URL
        new_success, new_api_url = test_api_url(config_dir, "new")
        
        if new_success:
            print("新 API URL 可用！")
            working_url = "new"
        else:
            print("新 API URL 不可用，測試舊 URL...")
            
            # 測試舊 URL
            old_success, old_api_url = test_api_url(config_dir, "old")
            
            if old_success:
                print("舊 API URL 可用！")
                working_url = "old"
            else:
                print("兩個 API URL 都不可用。")
                working_url = "none"
        
        # 使用可用的 URL
        if working_url == "new":
            api_url = "https://api.aihub.qualcomm.com"
            web_url = "https://app.aihub.qualcomm.com"
            print("\n使用新 API URL (api.aihub.qualcomm.com)")
            print("這是較新版本 QAI Hub 推薦的 URL。")
            update_config(config_dir, api_url, web_url)
        elif working_url == "old":
            api_url = "https://api.qai-hub.qualcomm.com"
            web_url = "https://app.aihub.qualcomm.com"
            print("\n使用舊 API URL (api.qai-hub.qualcomm.com)")
            print("這個 URL 與較舊版本的 QAI Hub 相容。")
            update_config(config_dir, api_url, web_url)
        else:
            print("\n找不到可用的 API URL。")
            print("請檢查您的網絡連接和 QAI Hub 安裝。")
            
            # 默認使用新 URL
            api_url = "https://api.aihub.qualcomm.com"
            web_url = "https://app.aihub.qualcomm.com"
            print("\n默認使用新 API URL。")
            update_config(config_dir, api_url, web_url)
    
    # 驗證配置
    verify_config(config_dir)
    
    # 結束信息
    print("\n" + "=" * 60)
    print("                      後續步驟")
    print("=" * 60)
    print()
    print("1. 如果測試顯示「QAI Hub 配置正常工作！」，則設定成功！")
    print("2. 如果仍有錯誤，請考慮：")
    print("   - 更新您的 QAI Hub 安裝：")
    print("     pip install -U qai-hub qai-hub-models")
    print("   - 嘗試與您的項目相容的特定版本：")
    print("     pip install qai-hub==0.31.0 qai-hub-models==0.31.0")
    print("   - 查看故障排除指南 (QAI_HUB_TROUBLESHOOTING.md)")
    print()

if __name__ == "__main__":
    main()
