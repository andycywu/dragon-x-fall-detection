#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon X Fall Detection 開發環境設置工具
Dragon X Fall Detection Development Environment Setup Tool

此工具幫助設置完整的開發環境，包括:
1. 安裝平台優化的依賴包
2. 設置 QAI Hub 配置
3. 測試環境配置

This tool helps set up the complete development environment, including:
1. Installing platform-optimized dependencies
2. Setting up QAI Hub configuration
3. Testing the environment configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import importlib.util

def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    print(f"Python 版本: {sys.version}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 版本過低，建議使用 Python 3.8 或更高版本。")
        return False
    
    return True

def check_virtual_env():
    """檢查是否在虛擬環境中運行"""
    is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if is_venv:
        print(f"✅ 使用中的虛擬環境: {sys.prefix}")
    else:
        print("⚠️ 未檢測到虛擬環境。建議在虛擬環境中安裝依賴。")
        
        # 提供創建虛擬環境的指導
        print("\n創建虛擬環境的步驟:")
        print("1. 使用以下命令創建虛擬環境:")
        print("   python -m venv .venv_dragon_x")
        print("2. 啟動虛擬環境:")
        if platform.system() == "Windows":
            print("   .venv_dragon_x\\Scripts\\activate")
        else:
            print("   source .venv_dragon_x/bin/activate")
        print("3. 再次運行此腳本")
        
        response = input("\n是否繼續安裝? (y/n): ").lower()
        if response != 'y':
            return False
    
    return True

def run_pip_install(package, prefer_binary=True):
    """運行 pip install 命令"""
    cmd = [sys.executable, "-m", "pip", "install"]
    
    if prefer_binary:
        cmd.extend(["--prefer-binary", "--only-binary=:all:"])
    
    cmd.append(package)
    
    print(f"安裝: {package}")
    try:
        subprocess.check_call(cmd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ 安裝 {package} 失敗: {e}")
        return False

def ensure_package_installed(package_name, import_name=None):
    """確保包已安裝，如果未安裝則安裝它"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    
    if spec is None:
        print(f"安裝必要的包: {package_name}")
        return run_pip_install(package_name)
    
    return True

def install_dependencies():
    """安裝所有依賴包"""
    print("\n📦 安裝依賴包...")
    
    # 確保必要的工具包已安裝
    essential_packages = {
        "pip": "pip",
        "setuptools": "setuptools",
        "wheel": "wheel",
        "tabulate": "tabulate"
    }
    
    for package, import_name in essential_packages.items():
        if not ensure_package_installed(package, import_name):
            print(f"❌ 無法安裝必要的包: {package}")
            return False
    
    # 執行平台特定的安裝腳本
    print("\n運行平台特定的依賴安裝...")
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_platform_accelerators.py")
        subprocess.check_call([sys.executable, script_path])
    except subprocess.CalledProcessError as e:
        print(f"❌ 平台特定依賴安裝失敗: {e}")
        return False
    
    return True

def setup_qai_hub():
    """設置 QAI Hub"""
    print("\n🔧 設置 QAI Hub...")
    
    # 檢查 QAI Hub 包是否已安裝
    if not ensure_package_installed("qai-hub"):
        print("❌ 無法安裝 QAI Hub 客戶端。")
        return False
    
    # 運行 QAI Hub 設置助手
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qai_hub_setup_assistant.py")
        if os.path.exists(script_path):
            subprocess.check_call([sys.executable, script_path])
        else:
            print(f"⚠️ 找不到 QAI Hub 設置助手: {script_path}")
            print("請手動設置 QAI Hub 配置。")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ QAI Hub 設置失敗: {e}")
        return False
    
    return True

def test_environment():
    """測試環境配置"""
    print("\n🧪 測試環境配置...")
    
    # 測試 ONNX Runtime
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        print(f"ONNX Runtime 版本: {ort.__version__}")
        print(f"可用提供者: {providers}")
        
        accelerated = any(p for p in providers if p != 'CPUExecutionProvider')
        if accelerated:
            print("✅ 已啟用硬體加速")
        else:
            print("⚠️ 僅使用 CPU 執行 (未啟用硬體加速)")
    except ImportError:
        print("❌ ONNX Runtime 未安裝或無法導入")
    
    # 測試 PyTorch
    try:
        import torch
        print(f"\nPyTorch 版本: {torch.__version__}")
        
        if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps'):
            print(f"MPS (Apple Metal) 可用: {torch.backends.mps.is_available()}")
        
        print(f"CUDA 可用: {torch.cuda.is_available()}")
    except ImportError:
        print("❌ PyTorch 未安裝或無法導入")
    
    # 測試 OpenCV
    try:
        import cv2
        print(f"\nOpenCV 版本: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV 未安裝或無法導入")
    
    # 測試 MediaPipe
    try:
        import mediapipe as mp
        print(f"\nMediaPipe 版本: {mp.__version__}")
    except ImportError:
        print("❌ MediaPipe 未安裝或無法導入")
    
    # 測試 QAI Hub
    try:
        import qai_hub
        print(f"\nQAI Hub 版本: {qai_hub.__version__}")
        
        # 檢查配置文件
        home_dir = str(Path.home())
        config_path = os.path.join(home_dir, ".qai_hub", "client.ini")
        
        if os.path.exists(config_path):
            print(f"✅ QAI Hub 配置文件存在: {config_path}")
        else:
            print(f"❌ QAI Hub 配置文件不存在: {config_path}")
    except ImportError:
        print("❌ QAI Hub 未安裝或無法導入")
    
    print("\n環境測試完成！")

def main():
    """主函數"""
    print("🐉 Dragon X Fall Detection 開發環境設置工具")
    print("=" * 60)
    
    # 檢查 Python 版本
    if not check_python_version():
        return
    
    # 檢查虛擬環境
    if not check_virtual_env():
        return
    
    # 安裝依賴
    if not install_dependencies():
        print("❌ 依賴安裝失敗。")
        return
    
    # 設置 QAI Hub
    if not setup_qai_hub():
        print("⚠️ QAI Hub 設置不完整。")
    
    # 測試環境
    test_environment()
    
    print("\n✅ 開發環境設置完成！")
    print("您現在可以開始使用 Dragon X Fall Detection 系統。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n設置已取消。")
    except Exception as e:
        print(f"\n❌ 設置過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
