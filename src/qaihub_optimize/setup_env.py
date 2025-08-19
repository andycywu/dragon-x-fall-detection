#!/usr/bin/env python3
"""
🚀 快速環境檢查和啟動腳本
檢查虛擬環境狀態並提供啟動指導
"""

import os
import sys
import subprocess
from pathlib import Path

def check_virtual_environment():
    """檢查虛擬環境狀態"""
    print("🔍 檢查虛擬環境狀態...")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv_mediapipe"
    
    # 檢查虛擬環境是否存在
    if venv_path.exists():
        print(f"✅ MediaPipe 虛擬環境存在: {venv_path}")
        
        # 檢查 Python 版本
        python_exe = venv_path / "bin" / "python"
        if python_exe.exists():
            try:
                result = subprocess.run([str(python_exe), "--version"], 
                                      capture_output=True, text=True)
                print(f"✅ Python 版本: {result.stdout.strip()}")
            except Exception as e:
                print(f"⚠️  無法獲取 Python 版本: {e}")
        
        # 檢查當前是否在虛擬環境中
        current_venv = os.environ.get('VIRTUAL_ENV', '')
        if str(venv_path) in current_venv:
            print("✅ 當前已在 MediaPipe 虛擬環境中")
        else:
            print("⚠️  當前未在 MediaPipe 虛擬環境中")
            print(f"💡 啟動命令: source {venv_path}/bin/activate")
    else:
        print(f"❌ MediaPipe 虛擬環境不存在: {venv_path}")
        print("💡 創建命令: python3.11 -m venv .venv_mediapipe")
    
    # 檢查舊的 .venv 目錄
    old_venv = project_root / ".venv"
    if old_venv.exists():
        print(f"⚠️  發現舊的虛擬環境: {old_venv}")
        print("💡 建議刪除: rm -rf .venv")
    else:
        print("✅ 舊的 .venv 目錄已清理")

def check_key_packages():
    """檢查關鍵包是否安裝"""
    print("\n📦 檢查關鍵包安裝狀態...")
    print("-" * 30)
    
    key_packages = [
        "mediapipe",
        "opencv-python", 
        "qai_hub",
        "streamlit",
        "numpy"
    ]
    
    for package in key_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未安裝)")

def show_quick_commands():
    """顯示快速命令"""
    print("\n🚀 快速命令指南")
    print("=" * 50)
    
    print("📁 進入項目目錄:")
    print("   cd /Users/andycyw/mvp_fall_detection_starter/src")
    
    print("\n⚡ 啟動虛擬環境:")
    print("   source qaihub_optimize/.venv/bin/activate")
    
    print("\n🔧 安裝依賴 (如需要):")
    print("   pip install -r requirements_qaihub.txt")
    
    print("\n🎪 運行演示:")
    print("   python qai_hub_demo.py")
    print("   python qai_hub_live_demo.py")
    print("   streamlit run hackathon_demo.py")
    
    print("\n📊 檢查配置:")
    print("   python config_manager.py")
    print("   python qai_hub_status_check.py")

def create_terminal_shortcut():
    """創建終端快捷方式"""
    print("\n📱 創建終端快捷方式...")
    
    # 創建啟動腳本
    shortcut_content = '''#!/bin/bash
# MediaPipe 項目快速啟動腳本

echo "🚀 啟動 MediaPipe 跌倒檢測項目..."
cd /Users/andycyw/mvp_fall_detection_starter

if [[ -d ".venv_mediapipe" ]]; then
    source .venv_mediapipe/bin/activate
    echo "✅ MediaPipe 環境已啟動"
    echo "📦 Python: $(python --version)"
    echo "📍 環境: $VIRTUAL_ENV"
    echo ""
    echo "🎯 可用命令:"
    echo "  python qai_hub_demo.py           # QAI Hub 演示"
    echo "  streamlit run hackathon_demo.py  # Web 界面"
    echo "  python config_manager.py         # 檢查配置"
    echo ""
else
    echo "❌ MediaPipe 環境不存在"
    echo "💡 請先創建: python3.11 -m venv .venv_mediapipe"
fi

# 保持終端開啟
exec $SHELL
'''
    
    shortcut_path = Path.home() / "Desktop" / "start_mediapipe_project.sh"
    
    try:
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        
        # 添加執行權限
        os.chmod(shortcut_path, 0o755)
        
        print(f"✅ 桌面快捷方式已創建: {shortcut_path}")
        print("💡 雙擊即可啟動項目環境")
        
    except Exception as e:
        print(f"⚠️  創建桌面快捷方式失敗: {e}")

def main():
    """主函數"""
    print("🏆 MediaPipe 跌倒檢測項目環境檢查")
    print("=" * 60)

    # 已不再需要 MediaPipe 虛擬環境，相關檢查與提示已移除
    print("✅ MediaPipe 虛擬環境檢查已移除")

    # 顯示關鍵包安裝狀態
    check_key_packages()

    # 顯示快速命令指南
    show_quick_commands()

    # 創建桌面快捷方式
    create_terminal_shortcut()

    print("\n" + "=" * 60)
    print("🎉 環境檢查完成！")
    print("💡 現在可以開始你的黑客松項目演示了！")

if __name__ == "__main__":
    main()
