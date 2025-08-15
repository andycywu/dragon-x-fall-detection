"""
QAI Hub client.ini 修復工具 - Windows 版本
修復 QAI Hub 認證和連接問題
"""

import os
import sys
import platform
import time
import subprocess
from pathlib import Path
import configparser
import shutil
import traceback

# 定義顏色輸出（Windows控制台可能無法顯示）
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

def fix_client_ini_windows():
    """專門為 Windows 修復 client.ini 文件"""
    print_header("QAI Hub client.ini Windows 修復工具")
    
    # 檢查是否是 Windows 系統
    if platform.system() != "Windows":
        print_warning(f"這個工具是為 Windows 設計的，當前系統是 {platform.system()}")
    
    # 記錄系統信息
    print_info(f"Windows 版本: {platform.win32_ver()[0]}")
    print_info(f"Python 版本: {sys.version.split()[0]}")
    print_info(f"用戶主目錄: {str(Path.home())}")
    
    # 使用 API 令牌
    api_token = 'pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d'
    print_info(f"使用指定的 API 令牌")
    
    # 設置環境變量
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    os.environ['QAI_API_KEY'] = api_token
    print_success("環境變量已設置")
    
    # 1. 創建並檢查 .qai_hub 目錄
    config_dir = Path.home() / ".qai_hub"
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"配置目錄已創建: {config_dir}")
    except Exception as e:
        print_error(f"創建配置目錄失敗: {e}")
        return False
    
    # 2. 備份現有的 client.ini 文件
    config_file = config_dir / "client.ini"
    if config_file.exists():
        try:
            backup_file = config_dir / f"client.ini.bak.{int(time.time())}"
            shutil.copy2(config_file, backup_file)
            print_success(f"已備份現有配置文件到: {backup_file}")
        except Exception as e:
            print_warning(f"備份配置文件失敗: {e}")
    
    # 3. 創建 client.ini 文件 - 嘗試多種格式
    created = False
    
    # 格式 1: 使用 [default]
    try:
        print_info("嘗試創建格式 1: [default]")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("[default]\n")
            f.write(f"api_token = {api_token}\n")
            f.write(f"api_key = {api_token}\n")
            f.write("base_api_url = https://api.qai-hub.qualcomm.com\n")
            f.write("web_url = https://app.aihub.qualcomm.com\n")
        print_success("格式 1 創建成功")
        created = True
    except Exception as e:
        print_error(f"格式 1 創建失敗: {e}")
    
    # 檢查文件是否正確創建
    if created and config_file.exists():
        print_success(f"client.ini 文件已創建: {config_file}")
        
        # 顯示文件內容
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print_info(f"client.ini 內容:\n{colorize(content, Colors.BOLD)}")
        except Exception as e:
            print_warning(f"讀取文件內容失敗: {e}")
    else:
        print_error("client.ini 文件創建失敗")
        return False
    
    # 4. 創建備用格式的配置文件
    try:
        # 備用格式 1: 使用 [DEFAULT]
        alt_file1 = config_dir / "client.ini.uppercase"
        with open(alt_file1, 'w', encoding='utf-8') as f:
            f.write("[DEFAULT]\n")
            f.write(f"api_key = {api_token}\n")
            f.write(f"api_token = {api_token}\n")
            f.write("base_api_url = https://api.qai-hub.qualcomm.com\n")
            f.write("web_url = https://app.aihub.qualcomm.com\n")
        
        # 備用格式 2: 簡化格式
        alt_file2 = config_dir / "client.ini.simple"
        with open(alt_file2, 'w', encoding='utf-8') as f:
            f.write("[default]\n")
            f.write(f"api_key = {api_token}\n")
        
        print_success("備用配置文件已創建")
    except Exception as e:
        print_warning(f"創建備用配置文件失敗: {e}")
    
    # 5. 在 .env 文件中保存 API 令牌
    try:
        env_file = Path.home() / ".env"
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"QAI_HUB_API_TOKEN={api_token}\n")
            f.write(f"QAI_API_KEY={api_token}\n")
        print_success(f"API 令牌已保存到 .env 文件: {env_file}")
    except Exception as e:
        print_warning(f"保存 .env 文件失敗: {e}")
    
    # 在Windows上使用setx永久設置環境變量
    try:
        subprocess.run(['setx', 'QAI_HUB_API_TOKEN', api_token], check=True)
        subprocess.run(['setx', 'QAI_API_KEY', api_token], check=True)
        print_success("已使用 setx 設置永久環境變量")
    except Exception as e:
        print_warning(f"設置永久環境變量失敗: {e}")
    
    return True

def check_network_connection():
    """檢查網絡連接"""
    print_header("網絡連接診斷")
    
    # 測試連接 QAI Hub API
    domains = [
        "api.qai-hub.qualcomm.com",
        "qualcomm.com",
        "app.aihub.qualcomm.com"
    ]
    
    all_success = True
    for domain in domains:
        print_info(f"測試連接到 {domain}...")
        try:
            # 使用 ping 測試連接
            result = subprocess.run(['ping', '-n', '1', domain], 
                                   capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print_success(f"可以連接到 {domain}")
            else:
                print_error(f"無法連接到 {domain}")
                all_success = False
        except Exception as e:
            print_error(f"測試連接到 {domain} 時出錯: {e}")
            all_success = False
    
    # 建議
    if not all_success:
        print_warning("網絡連接問題可能影響 QAI Hub 功能")
        print_info("建議檢查:")
        print_info("1. 防火牆設置")
        print_info("2. 網絡連接狀態")
        print_info("3. DNS 設置")
        print_info("4. 代理服務器設置")
    else:
        print_success("網絡連接檢查通過")
    
    return all_success

def test_qai_hub_import():
    """測試 QAI Hub 模塊導入"""
    print_header("QAI Hub 模塊測試")
    
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
        print_warning(f"檢查 protobuf 版本失敗: {e}")
    
    # 嘗試導入 qai_hub
    try:
        import qai_hub
        version = getattr(qai_hub, '__version__', '未知')
        print_success(f"QAI Hub 模塊導入成功，版本: {version}")
        
        # 嘗試基本 API 調用
        print_info("嘗試基本 API 調用...")
        try:
            user = qai_hub.get_user()
            print_success(f"API 調用成功! 用戶 ID: {user.id}")
            return True
        except Exception as e:
            print_error(f"API 調用失敗: {e}")
            
            # 分析錯誤原因
            error_msg = str(e)
            if "Failed to load configuration file" in error_msg:
                print_error("配置文件加載失敗")
                print_info("請確保 ~/.qai_hub/client.ini 文件格式正確")
            elif "Invalid API key" in error_msg:
                print_error("API 密鑰無效")
                print_info("請確認 API 令牌是否正確")
            elif "Connection refused" in error_msg or "Could not connect" in error_msg:
                print_error("連接被拒絕")
                print_info("請檢查網絡連接和防火牆設置")
            
            return False
    except ImportError:
        print_error("QAI Hub 模塊導入失敗")
        print_info("請確保已安裝: pip install qai-hub==0.31.0")
        return False
    except Exception as e:
        print_error(f"測試 QAI Hub 導入時出錯: {e}")
        return False

def main():
    """主函數"""
    print_header("QAI Hub Windows 診斷與修復工具")
    
    # 步驟 1: 修復 client.ini
    success = fix_client_ini_windows()
    
    # 步驟 2: 檢查網絡連接
    network_ok = check_network_connection()
    
    # 步驟 3: 測試 QAI Hub 導入
    qai_hub_ok = test_qai_hub_import()
    
    # 總結
    print_header("診斷摘要")
    if success:
        print_success("client.ini 文件已修復")
    else:
        print_error("client.ini 文件修復失敗")
    
    if network_ok:
        print_success("網絡連接正常")
    else:
        print_error("網絡連接有問題")
    
    if qai_hub_ok:
        print_success("QAI Hub 模塊測試通過")
    else:
        print_error("QAI Hub 模塊測試失敗")
    
    # 後續建議
    print_header("後續步驟")
    if success and network_ok and qai_hub_ok:
        print_success("✨ 所有問題已修復! QAI Hub 配置正常 ✨")
        print_info("建議運行: python check_qai_hub_status.py")
    else:
        print_warning("⚠️ 仍有一些問題需要解決")
        
        if not success:
            print_info("1. 手動編輯 %USERPROFILE%\\.qai_hub\\client.ini 文件")
            print_info("   格式應為:")
            print_info("   [default]")
            print_info("   api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d")
        
        if not network_ok:
            print_info("2. 檢查網絡連接和防火牆設置")
            print_info("   確保可以連接到 api.qai-hub.qualcomm.com")
        
        if not qai_hub_ok:
            print_info("3. 重新安裝 QAI Hub SDK:")
            print_info("   pip install qai-hub==0.31.0")
    
    print_header("故障排除技巧")
    print_info("1. 如果配置文件不正確，嘗試使用備用格式:")
    print_info("   copy %USERPROFILE%\\.qai_hub\\client.ini.uppercase %USERPROFILE%\\.qai_hub\\client.ini")
    print_info("2. 確保設置了環境變量:")
    print_info("   setx QAI_HUB_API_TOKEN pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d")
    print_info("3. 檢查 Python 版本和依賴包:")
    print_info("   pip install protobuf==4.25.3")
    print_info("   pip install qai-hub==0.31.0 qai-hub-models==0.33.1")
    print_info("4. 確認 Windows 安全設置允許應用程序連接網絡")
    print_info("5. 重啟電腦後再試，因為某些環境變量需要重啟後才能生效")
    
    print("\n請按 Enter 鍵退出...")
    input()

if __name__ == "__main__":
    # 在 Windows 上啟用 ANSI 顏色支持
    if platform.system() == "Windows":
        os.system("")
    main()
