#!/usr/bin/env python3
"""
🔍 QAI Hub 功能狀態檢查器
快速確認 QAI Hub 集成是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def check_banner():
    print("🔍 QAI Hub 功能狀態檢查")
    print("=" * 50)

def check_environment():
    """檢查環境設置"""
    print("\n📊 1. 環境檢查")
    print("-" * 30)
    
    checks = []
    
    # 檢查 .env 文件
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env 文件存在")
        checks.append(True)
    else:
        print("❌ .env 文件不存在")
        checks.append(False)
    
    # 檢查 API Token
    from dotenv import load_dotenv
    load_dotenv()
    
    api_token = os.getenv("QAI_HUB_API_TOKEN")
    if api_token and api_token != "your_api_token_here":
        print(f"✅ API Token 已設置 ({api_token[:10]}...)")
        checks.append(True)
    else:
        print("❌ API Token 未設置或為默認值")
        checks.append(False)
    
    return all(checks)

def check_dependencies():
    """檢查依賴模塊"""
    print("\n📦 2. 依賴檢查")
    print("-" * 30)
    
    dependencies = [
        ("mediapipe", "MediaPipe 姿態檢測"),
        ("cv2", "OpenCV 視頻處理"),
        ("numpy", "數值計算"),
        ("qai_hub", "Qualcomm AI Hub"),
        ("streamlit", "Web 界面"),
    ]
    
    results = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✅ {module:<12} - {description}")
            results.append(True)
        except ImportError:
            print(f"❌ {module:<12} - {description} (未安裝)")
            results.append(False)
    
    return results

def check_config_manager():
    """檢查配置管理器"""
    print("\n⚙️  3. 配置管理器檢查")
    print("-" * 30)
    
    try:
        from config_manager import ConfigManager
        config = ConfigManager()
        
        print("✅ ConfigManager 導入成功")
        
        # 獲取配置
        qai_config = config.get_qai_hub_config()
        detection_config = config.get_detection_config()
        
        print(f"✅ QAI Hub 配置: {len(qai_config)} 項")
        print(f"✅ 檢測配置: {len(detection_config)} 項")
        
        # 顯示關鍵配置
        print(f"   API Token: {'已設置' if qai_config.get('api_token') != 'your_api_token_here' else '未設置'}")
        print(f"   硬件加速: {'啟用' if qai_config.get('enable_acceleration') else '禁用'}")
        print(f"   跌倒閾值: {detection_config.get('fall_threshold')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager 檢查失敗: {e}")
        return False

def check_qai_hub_integration():
    """檢查 QAI Hub 集成"""
    print("\n🚀 4. QAI Hub 集成檢查")
    print("-" * 30)
    
    try:
        # 檢查 qai_hub_integration.py
        integration_file = Path("qai_hub_integration.py")
        if integration_file.exists():
            print("✅ qai_hub_integration.py 存在")
        else:
            print("❌ qai_hub_integration.py 不存在")
            return False
        
        # 嘗試導入
        try:
            from qai_hub_integration import QAIHubManager
            print("✅ QAIHubManager 導入成功")
            
            # 創建實例
            manager = QAIHubManager()
            print("✅ QAIHubManager 實例化成功")
            
            return True
            
        except Exception as e:
            print(f"⚠️  QAIHubManager 導入失敗: {e}")
            print("🔧 這可能是因為 qai_hub 模塊未安裝")
            return False
            
    except Exception as e:
        print(f"❌ QAI Hub 集成檢查失敗: {e}")
        return False

def check_demo_files():
    """檢查演示文件"""
    print("\n🎪 5. 演示文件檢查")
    print("-" * 30)
    
    demo_files = [
        ("hackathon_main.py", "主要檢測程序"),
        ("hackathon_demo.py", "Streamlit Web 演示"),
        ("qai_hub_demo.py", "QAI Hub 功能演示"),
        ("qai_hub_live_demo.py", "實時檢測演示"),
        ("qai_setup_helper.py", "API 配置助手")
    ]
    
    results = []
    
    for filename, description in demo_files:
        file_path = Path(filename)
        if file_path.exists():
            print(f"✅ {filename:<20} - {description}")
            results.append(True)
        else:
            print(f"❌ {filename:<20} - {description}")
            results.append(False)
    
    return results

def test_qai_hub_connection():
    """測試 QAI Hub 實際連接"""
    print("\n🔌 6. QAI Hub 連接測試")
    print("-" * 30)
    
    try:
        import qai_hub
        print("✅ qai_hub 模塊導入成功")
        
        # 嘗試獲取設備信息
        try:
            devices = qai_hub.get_devices()
            print(f"✅ 成功連接 QAI Hub")
            print(f"📱 可用設備: {len(devices)} 個")
            
            if devices:
                print("🔧 設備列表:")
                for i, device in enumerate(devices[:3]):
                    print(f"   {i+1}. {device.name} ({device.os})")
            
            return True, len(devices)
            
        except Exception as e:
            print(f"⚠️  設備獲取失敗: {e}")
            print("🔧 可能的原因:")
            print("   - API Token 無效")
            print("   - 網絡連接問題")
            print("   - QAI Hub 服務異常")
            return False, 0
            
    except ImportError:
        print("❌ qai_hub 模塊未安裝")
        print("💡 安裝命令: pip install qai-hub")
        return False, 0

def generate_report(env_ok, deps, config_ok, qai_ok, demos, connection_ok, device_count):
    """生成檢查報告"""
    print("\n" + "=" * 50)
    print("📋 QAI Hub 功能狀態報告")
    print("=" * 50)
    
    # 計算總體狀態
    dep_score = sum(deps) / len(deps) * 100 if deps else 0
    demo_score = sum(demos) / len(demos) * 100 if demos else 0
    
    print(f"🌡️  整體健康度:")
    print(f"   環境配置: {'✅ 正常' if env_ok else '❌ 異常'}")
    print(f"   依賴模塊: {dep_score:.0f}% ({sum(deps)}/{len(deps)})")
    print(f"   配置管理: {'✅ 正常' if config_ok else '❌ 異常'}")
    print(f"   QAI 集成: {'✅ 正常' if qai_ok else '❌ 異常'}")
    print(f"   演示文件: {demo_score:.0f}% ({sum(demos)}/{len(demos)})")
    print(f"   Hub 連接: {'✅ 已連接' if connection_ok else '❌ 未連接'}")
    
    if connection_ok:
        print(f"   可用設備: {device_count} 個")
    
    print(f"\n🎯 QAI Hub 功能狀態:")
    
    if env_ok and config_ok and dep_score >= 80:
        if connection_ok:
            print("🚀 完全就緒 - 可以展示完整 QAI Hub 功能")
            print("💡 建議運行: python qai_hub_live_demo.py")
        else:
            print("⚡ 基本就緒 - 可以展示 QAI Hub 集成架構")
            print("💡 建議運行: python qai_hub_demo.py")
    else:
        print("🔧 需要配置 - 請解決上述問題")
        print("💡 建議運行: python qai_setup_helper.py")
    
    print(f"\n🏆 黑客松建議:")
    if connection_ok and device_count > 0:
        print("   ✨ 重點展示硬件加速性能")
        print("   ✨ 強調邊緣AI優化能力")
    else:
        print("   ✨ 重點展示技術架構設計")
        print("   ✨ 強調系統工程能力")
    
    print("   ✨ MediaPipe + QAI Hub 創新整合")
    print("   ✨ 完整的產品級解決方案")

def main():
    check_banner()
    
    # 執行所有檢查
    env_ok = check_environment()
    deps = check_dependencies()
    config_ok = check_config_manager()
    qai_ok = check_qai_hub_integration()
    demos = check_demo_files()
    connection_ok, device_count = test_qai_hub_connection()
    
    # 生成報告
    generate_report(env_ok, deps, config_ok, qai_ok, demos, connection_ok, device_count)

if __name__ == "__main__":
    main()
