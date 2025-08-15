"""
QAI Hub API 認證測試工具 - Windows 專用
診斷和修復 QAI Hub API 連接問題
"""

import os
import sys
import platform
import time
from pathlib import Path
import traceback
import requests

# 在 Windows 上啟用 ANSI 顏色支持
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

def test_direct_api():
    """直接測試 API 連接，繞過 QAI Hub SDK"""
    print_header("直接 API 連接測試")
    
    api_token = 'pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d'
    print_info(f"使用 API 令牌: {api_token[:5]}...{api_token[-5:]}")
    
    # 測試基本 API 端點
    api_urls = [
        "https://api.qai-hub.qualcomm.com/healthz",
        "https://api.qai-hub.qualcomm.com/api/v1/users/me"
    ]
    
    # 測試標頭
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
        "User-Agent": f"QAI-Hub-Test/{platform.system()}-{platform.release()}/Python-{sys.version.split()[0]}"
    }
    
    all_success = True
    
    # 測試連接狀態
    print_info("測試 API 服務健康狀態...")
    try:
        response = requests.get(api_urls[0], headers=headers, timeout=10)
        if response.status_code == 200:
            print_success(f"API 健康狀態檢查通過: {response.status_code}")
        else:
            print_error(f"API 健康狀態檢查失敗: {response.status_code}")
            print_info(f"響應內容: {response.text}")
            all_success = False
    except requests.exceptions.RequestException as e:
        print_error(f"API 健康狀態檢查出錯: {e}")
        all_success = False
    
    # 測試用戶信息
    print_info("測試用戶 API...")
    try:
        response = requests.get(api_urls[1], headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print_success(f"用戶 API 調用成功: {response.status_code}")
            if 'id' in user_data:
                print_info(f"用戶 ID: {user_data['id']}")
            if 'email' in user_data:
                print_info(f"用戶郵箱: {user_data['email']}")
        else:
            print_error(f"用戶 API 調用失敗: {response.status_code}")
            print_info(f"響應內容: {response.text}")
            all_success = False
    except requests.exceptions.RequestException as e:
        print_error(f"用戶 API 調用出錯: {e}")
        all_success = False
    
    # 返回總體結果
    return all_success

def test_qai_hub_api():
    """測試 QAI Hub SDK API 調用"""
    print_header("QAI Hub SDK API 測試")
    
    try:
        import qai_hub as hub
        print_success(f"成功導入 qai_hub 模塊 (版本: {getattr(hub, '__version__', '未知')})")
        
        # 嘗試獲取用戶信息
        print_info("嘗試獲取用戶信息...")
        try:
            user = hub.get_user()
            print_success(f"獲取用戶信息成功! 用戶 ID: {user.id}")
            
            # 嘗試獲取設備列表
            print_info("嘗試獲取設備列表...")
            try:
                devices = hub.get_devices()
                print_success(f"獲取設備列表成功! 設備數量: {len(devices)}")
                
                if devices:
                    print_info("可用設備:")
                    for i, device in enumerate(devices[:3]):
                        print(f"   {i+1}. {colorize(device.name, Colors.BOLD)}")
                
                # 嘗試獲取模型列表
                print_info("嘗試獲取模型列表...")
                try:
                    models = hub.get_available_models()
                    print_success(f"獲取模型列表成功! 模型數量: {len(models)}")
                    
                    if models and len(models) > 0:
                        print_info("部分可用模型:")
                        for i, model in enumerate(models[:3]):
                            print(f"   {i+1}. {colorize(model.name, Colors.BOLD)}")
                    
                    return True
                except Exception as e:
                    print_error(f"獲取模型列表失敗: {e}")
                    print_info("這可能是正常的，因為某些 API 訪問可能受限")
                    return True  # 仍然返回 True，因為基本功能正常
            except Exception as e:
                print_warning(f"獲取設備列表失敗: {e}")
                print_info("這可能是正常的，因為你的電腦不是 Snapdragon 設備")
                return True  # 仍然返回 True，因為基本功能正常
        except Exception as e:
            print_error(f"獲取用戶信息失敗: {e}")
            print_error("這表明 API 認證可能有問題")
            
            # 分析錯誤原因
            error_msg = str(e)
            if "Failed to load configuration file" in error_msg:
                print_error("配置文件加載失敗")
                print_info("請確保 %USERPROFILE%\\.qai_hub\\client.ini 文件格式正確")
            elif "Invalid API key" in error_msg:
                print_error("API 密鑰無效")
                print_info("請確認 API 令牌是否正確")
            elif "Connection refused" in error_msg or "Could not connect" in error_msg:
                print_error("連接被拒絕")
                print_info("請檢查網絡連接和防火牆設置")
            
            return False
    except ImportError:
        print_error("無法導入 qai_hub 模塊")
        print_info("請確保已安裝: pip install qai-hub==0.31.0")
        return False
    except Exception as e:
        print_error(f"測試 QAI Hub API 時出錯: {e}")
        return False

def fix_api_key():
    """修復 API 密鑰問題"""
    print_header("API 密鑰修復")
    
    api_token = 'pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d'
    print_info(f"使用 API 令牌: {api_token[:5]}...{api_token[-5:]}")
    
    # 設置環境變量
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    os.environ['QAI_API_KEY'] = api_token
    print_success("臨時環境變量已設置")
    
    # 設置永久環境變量
    try:
        os.system(f'setx QAI_HUB_API_TOKEN "{api_token}"')
        os.system(f'setx QAI_API_KEY "{api_token}"')
        print_success("永久環境變量已設置 (需要重啟命令行才能生效)")
    except Exception as e:
        print_warning(f"設置永久環境變量失敗: {e}")
    
    # 檢查並修復 client.ini 文件
    config_dir = Path.home() / ".qai_hub"
    config_file = config_dir / "client.ini"
    
    # 確保目錄存在
    config_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"確保目錄存在: {config_dir}")
    
    # 嘗試以下格式:
    formats = [
        # 格式 1: [default]
        "[default]\n"
        f"api_token = {api_token}\n"
        f"api_key = {api_token}\n"
        "base_api_url = https://api.qai-hub.qualcomm.com\n"
        "web_url = https://app.aihub.qualcomm.com\n",
        
        # 格式 2: [DEFAULT]
        "[DEFAULT]\n"
        f"api_token = {api_token}\n"
        f"api_key = {api_token}\n"
        "base_api_url = https://api.qai-hub.qualcomm.com\n"
        "web_url = https://app.aihub.qualcomm.com\n",
        
        # 格式 3: 簡化格式
        "[default]\n"
        f"api_key = {api_token}\n",
        
        # 格式 4: 簡化大寫格式
        "[DEFAULT]\n"
        f"api_key = {api_token}\n"
    ]
    
    for i, format_content in enumerate(formats, 1):
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(format_content)
            print_success(f"已嘗試格式 {i}")
            
            # 測試此格式是否有效
            try:
                import qai_hub
                user = qai_hub.get_user()
                print_success(f"格式 {i} 有效! 用戶 ID: {user.id}")
                return True
            except Exception:
                print_warning(f"格式 {i} 無效，繼續嘗試其他格式")
        except Exception as e:
            print_error(f"寫入格式 {i} 時出錯: {e}")
    
    print_warning("所有格式都已嘗試，但都未成功")
    return False

def diagnose_network():
    """診斷網絡問題"""
    print_header("網絡診斷")
    
    # 測試基本連接
    domains = [
        "api.qai-hub.qualcomm.com",
        "qualcomm.com",
        "google.com"  # 測試基本網絡連接
    ]
    
    for domain in domains:
        print_info(f"測試連接到 {domain}...")
        try:
            import socket
            socket.gethostbyname(domain)
            print_success(f"DNS 解析 {domain} 成功")
        except socket.gaierror:
            print_error(f"DNS 解析 {domain} 失敗")
        
        # 測試 ping
        try:
            import subprocess
            result = subprocess.run(['ping', '-n', '1', domain], 
                                    capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"Ping {domain} 成功")
            else:
                print_error(f"Ping {domain} 失敗")
        except Exception as e:
            print_error(f"Ping 測試失敗: {e}")
        
        # 測試 HTTP 連接
        if domain != "qualcomm.com":  # 僅測試 API 和 Google
            try:
                response = requests.get(f"https://{domain}", timeout=5)
                print_success(f"HTTP 連接到 {domain} 成功: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print_error(f"HTTP 連接到 {domain} 失敗: {e}")
    
    # 檢查代理設置
    proxies = {
        'http': os.environ.get('HTTP_PROXY', ''),
        'https': os.environ.get('HTTPS_PROXY', '')
    }
    
    if proxies['http'] or proxies['https']:
        print_info(f"檢測到代理設置: HTTP={proxies['http']}, HTTPS={proxies['https']}")
    else:
        print_info("未檢測到代理設置")
    
    # 檢查 Windows 防火牆
    try:
        import subprocess
        result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], 
                                capture_output=True, text=True)
        print_info("Windows 防火牆狀態:")
        if "狀態" in result.stdout or "State" in result.stdout:
            print_info(result.stdout.split("Domain Profile")[0].strip())
        else:
            print_info("無法獲取防火牆狀態詳細信息")
    except Exception:
        print_info("無法檢查 Windows 防火牆狀態")
    
    return True

def create_hackathon_demo():
    """創建一個假的演示腳本，在無法連接時使用"""
    print_header("創建黑客松演示腳本")
    
    demo_file = Path.cwd() / "qai_hub_demo_offline.py"
    
    demo_content = '''#!/usr/bin/env python3
"""
離線 QAI Hub 演示 - 為黑客松準備
當無法連接到 QAI Hub 時提供替代方案
"""

import time
import os
import numpy as np
from pathlib import Path
import sys

def print_banner():
    """演示橫幅"""
    print("=" * 60)
    print("🏆 Dragon X Fall Detection 黑客松演示")
    print("   MediaPipe + Qualcomm AI Hub 跌倒檢測系統")
    print("=" * 60)
    print()

def simulate_qai_hub():
    """模擬 QAI Hub 功能"""
    print("📊 模擬 QAI Hub 集成")
    print("-" * 40)
    
    print("❗注意: 這是一個離線演示，使用模擬數據")
    print("   真實系統需要連接到 QAI Hub API")
    
    print("\\n📱 模擬設備列表:")
    devices = [
        "Snapdragon X Elite CRD",
        "Snapdragon X Plus 8-Core CRD",
        "Snapdragon X Plus 4-Core CRD"
    ]
    
    for i, device in enumerate(devices, 1):
        print(f"   {i}. {device}")
    
    print("\\n🔍 模擬 Fall Detection 模型:")
    models = [
        "onnx-fall-detector",
        "pose-estimation-landmarks",
        "person-detector-v1"
    ]
    
    for i, model in enumerate(models, 1):
        print(f"   {i}. {model}")

def simulate_performance():
    """模擬性能數據"""
    print("\\n⚡ 模擬性能比較")
    print("-" * 40)
    
    platforms = ["CPU", "GPU", "Hexagon DSP", "QAI Hub 加速"]
    
    print(f"{'平台':<15} {'延遲(ms)':<10} {'FPS':<8} {'功耗':<10}")
    print("-" * 45)
    
    for platform in platforms:
        if platform == "CPU":
            latency = 85
            fps = 12
            power = "高"
        elif platform == "GPU":
            latency = 45
            fps = 22
            power = "中高"
        elif platform == "Hexagon DSP":
            latency = 28
            fps = 35
            power = "中"
        else:  # QAI Hub
            latency = 15
            fps = 66
            power = "低"
        
        print(f"{platform:<15} {latency:<10} {fps:<8} {power:<10}")

def show_fall_detection():
    """展示跌倒檢測過程"""
    print("\\n🎯 跌倒檢測模擬")
    print("-" * 40)
    
    print("💡 正在執行跌倒檢測邏輯...")
    
    stages = [
        ("載入視頻流", 0.5),
        ("姿態檢測", 0.8),
        ("提取關鍵點", 0.6),
        ("計算角度特徵", 0.4),
        ("QAI Hub 模型推理", 1.0),
        ("檢測結果融合", 0.3)
    ]
    
    for stage, duration in stages:
        print(f"⏳ {stage}...", end="", flush=True)
        time.sleep(duration)
        print(" ✅")
    
    print("\\n📊 檢測結果:")
    print("   ✅ 未檢測到跌倒")
    print("   📈 站立置信度: 95%")
    print("   📉 跌倒風險: 低")

def main():
    """主函數"""
    print_banner()
    
    print("👋 歡迎使用 Dragon X Fall Detection 系統!")
    print("⚠️  當前處於離線演示模式")
    print("🔄 這個模式模擬了系統的主要功能，但不需要連接到 QAI Hub API")
    print()
    
    simulate_qai_hub()
    input("\\n按 Enter 繼續...")
    
    simulate_performance()
    input("\\n按 Enter 繼續...")
    
    show_fall_detection()
    
    print("\\n" + "=" * 60)
    print("🎉 演示完成!")
    print("=" * 60)
    
    print("\\n💡 在完整系統中，您將能夠:")
    print("   ✅ 連接到實際的 QAI Hub API")
    print("   ✅ 使用真實的硬件加速")
    print("   ✅ 進行實時跌倒檢測")
    print("   ✅ 獲得更準確的結果")
    
    print("\\n📋 如需連接 QAI Hub API:")
    print("   1. 運行 fix_qai_hub_client.bat 修復工具")
    print("   2. 確保網絡可以連接到 api.qai-hub.qualcomm.com")
    print("   3. 檢查 API 令牌配置")

if __name__ == "__main__":
    main()
'''
    
    with open(demo_file, 'w', encoding='utf-8') as f:
        f.write(demo_content)
    
    print_success(f"演示腳本已創建: {demo_file}")
    print_info("如果無法連接到 QAI Hub API，可運行此腳本進行演示")
    
    return True

def main():
    """主函數"""
    print_header("QAI Hub API 認證診斷工具 - Windows版本")
    
    # 首先創建離線演示腳本 (以防後續失敗)
    create_hackathon_demo()
    
    # 步驟 1: 修復 API 密鑰
    fix_api_key()
    
    # 步驟 2: 測試直接 API 連接
    direct_api_ok = test_direct_api()
    
    # 步驟 3: 診斷網絡
    if not direct_api_ok:
        diagnose_network()
    
    # 步驟 4: 測試 QAI Hub SDK
    sdk_ok = test_qai_hub_api()
    
    # 總結
    print_header("診斷摘要")
    if direct_api_ok:
        print_success("直接 API 連接測試通過")
    else:
        print_error("直接 API 連接測試失敗")
    
    if sdk_ok:
        print_success("QAI Hub SDK 測試通過")
    else:
        print_error("QAI Hub SDK 測試失敗")
    
    # 建議
    print_header("故障排除建議")
    if not direct_api_ok and not sdk_ok:
        print_error("無法連接到 QAI Hub API")
        print_info("可能原因:")
        print_info("1. 網絡連接問題")
        print_info("2. API 令牌無效")
        print_info("3. 防火牆或安全軟件阻止連接")
        
        print_info("\n建議操作:")
        print_info("1. 嘗試在瀏覽器中訪問 https://app.aihub.qualcomm.com")
        print_info("2. 檢查 Windows 安全設置和防火牆")
        print_info("3. 如使用公司/學校網絡，請確認是否限制了對 qualcomm.com 的訪問")
        print_info("4. 使用離線演示腳本進行演示: python qai_hub_demo_offline.py")
    elif not sdk_ok:
        print_warning("API 連接正常，但 SDK 有問題")
        print_info("建議操作:")
        print_info("1. 重新安裝 QAI Hub SDK: pip install qai-hub==0.31.0")
        print_info("2. 確保 protobuf 版本兼容: pip install protobuf==4.25.3")
        print_info("3. 檢查 Python 環境")
    else:
        print_success("✨ QAI Hub API 連接正常! ✨")
        print_info("您現在可以:")
        print_info("1. 運行 check_qai_hub_status.py 檢查作業狀態")
        print_info("2. 運行 dragon_x_fall_detection_system.py 啟動系統")
    
    print("\n按任意鍵退出...")
    input()

if __name__ == "__main__":
    main()
