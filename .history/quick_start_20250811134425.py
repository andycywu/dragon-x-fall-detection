#!/usr/bin/env python3
"""
🚀 快速啟動腳本
一鍵設置和測試跨平台AI檢測系統
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def print_banner():
    """顯示啟動橫幅"""
    print("🚀 跨平台AI檢測系統 - 快速啟動")
    print("=" * 50)
    print("📅 啟動時間:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

def check_environment():
    """檢查環境設置"""
    print("🔍 檢查開發環境...")
    
    # 檢查Python版本
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    else:
        print(f"❌ Python版本過低: {python_version.major}.{python_version.minor}")
        return False
    
    # 檢查關鍵文件
    required_files = [
        "unified_ai_detector.py",
        "cross_platform_ai_detector.py", 
        "cross_platform_config.json"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ 發現文件: {file}")
        else:
            print(f"❌ 缺少文件: {file}")
            return False
    
    # 檢查QAI Hub API Token
    api_token = os.getenv('QAI_HUB_API_TOKEN')
    if api_token:
        print(f"✅ QAI Hub API Token: {api_token[:10]}...")
    else:
        print("⚠️ QAI Hub API Token未設置")
        print("💡 可以運行: export QAI_HUB_API_TOKEN='your_token'")
    
    return True

def install_dependencies():
    """安裝依賴項"""
    print("\n📦 檢查和安裝依賴項...")
    
    required_packages = [
        "opencv-python",
        "numpy",
        "mediapipe", 
        "onnxruntime"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} 已安裝")
        except ImportError:
            missing_packages.append(package)
            print(f"⚠️ {package} 未安裝")
    
    if missing_packages:
        print(f"\n🔧 安裝缺失的包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ 依賴項安裝完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 依賴項安裝失敗: {e}")
            return False
    
    return True

def run_platform_analysis():
    """運行平台分析"""
    print("\n🌐 運行平台分析...")
    try:
        result = subprocess.run([
            sys.executable, "cross_platform_ai_detector.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 平台分析完成")
            print("📄 查看詳細報告: cross_platform_analysis.json")
        else:
            print("❌ 平台分析失敗")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ 平台分析超時")
        return False
    except Exception as e:
        print(f"❌ 平台分析異常: {e}")
        return False
    
    return True

def run_ai_detector_test():
    """運行AI檢測器測試"""
    print("\n🧠 運行AI檢測器測試...")
    try:
        result = subprocess.run([
            sys.executable, "unified_ai_detector.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ AI檢測器測試完成")
            # 提取風險分數
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if '風險分數:' in line:
                    print(f"📊 {line.strip()}")
                elif '警報:' in line:
                    print(f"⚠️ {line.strip()}")
        else:
            print("❌ AI檢測器測試失敗")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ AI檢測器測試超時")
        return False
    except Exception as e:
        print(f"❌ AI檢測器測試異常: {e}")
        return False
    
    return True

def generate_setup_report():
    """生成設置報告"""
    print("\n📋 生成設置報告...")
    
    # 讀取平台分析結果
    platform_info = {}
    if os.path.exists("cross_platform_analysis.json"):
        try:
            with open("cross_platform_analysis.json", 'r') as f:
                platform_info = json.load(f)
        except Exception as e:
            print(f"⚠️ 讀取平台分析失敗: {e}")
    
    # 創建設置報告
    report = {
        "setup_timestamp": datetime.now().isoformat(),
        "environment_check": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
            "qai_hub_configured": bool(os.getenv('QAI_HUB_API_TOKEN')),
            "platform_analysis": platform_info
        },
        "next_steps": [
            "🍎 在Mac上完善核心功能開發",
            "☁️ 配置QAI Hub進行雲端測試",
            "🐉 準備Snapdragon X Elite部署包",
            "📊 建立性能基準和測試套件"
        ],
        "quick_commands": {
            "run_platform_analysis": "python cross_platform_ai_detector.py",
            "run_ai_detector": "python unified_ai_detector.py",
            "set_qai_hub_token": "export QAI_HUB_API_TOKEN='your_token'",
            "view_config": "cat cross_platform_config.json"
        }
    }
    
    report_path = "setup_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 設置報告已保存: {report_path}")
    return report

def show_next_steps(report):
    """顯示下一步建議"""
    print("\n🎯 下一步建議:")
    for step in report["next_steps"]:
        print(f"   {step}")
    
    print("\n💻 快速命令:")
    for desc, cmd in report["quick_commands"].items():
        print(f"   {desc}: {cmd}")
    
    # QAI Hub設置建議
    if not os.getenv('QAI_HUB_API_TOKEN'):
        print("\n🔑 啟用QAI Hub雲端功能:")
        print("   export QAI_HUB_API_TOKEN='h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2'")
        print("   python real_qai_hub_onnx_detector.py")

def main():
    """主函數"""
    print_banner()
    
    success_count = 0
    total_steps = 4
    
    # 步驟1: 檢查環境
    if check_environment():
        success_count += 1
    
    # 步驟2: 安裝依賴項
    if install_dependencies():
        success_count += 1
    
    # 步驟3: 運行平台分析
    if run_platform_analysis():
        success_count += 1
    
    # 步驟4: 運行AI檢測器測試
    if run_ai_detector_test():
        success_count += 1
    
    # 生成報告
    report = generate_setup_report()
    
    # 顯示結果
    print(f"\n🎊 設置完成! ({success_count}/{total_steps} 步驟成功)")
    
    if success_count == total_steps:
        print("✅ 系統完全就緒！")
        print("🚀 你現在可以:")
        print("   • 在Mac上進行AI檢測開發")
        print("   • 使用Apple Neural Engine加速")
        print("   • 準備Snapdragon X Elite部署")
    elif success_count >= 2:
        print("⚠️ 系統基本可用，有一些非關鍵問題")
        print("💡 查看設置報告了解詳情")
    else:
        print("❌ 系統設置遇到問題")
        print("🔧 請解決關鍵問題後重新運行")
    
    show_next_steps(report)
    
    print(f"\n📋 完整指南: MAC_TO_SNAPDRAGON_MIGRATION_GUIDE.md")
    print("🏁 設置完成!")

if __name__ == "__main__":
    main()
