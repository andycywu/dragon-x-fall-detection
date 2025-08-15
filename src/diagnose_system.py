#!/usr/bin/env python3
"""
Dragon X Fall Detection 系統診斷工具
用於診斷常見問題並提供修復建議
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
import shutil

def check_python_environment():
    """檢查 Python 環境"""
    print("=== Python 環境檢查 ===")
    print(f"Python 版本: {platform.python_version()}")
    print(f"Python 路徑: {sys.executable}")
    
    # 檢查虛擬環境
    venv_path = Path.cwd() / ".venv"
    if venv_path.exists():
        print("虛擬環境: 已找到 (.venv)")
        
        # 檢查虛擬環境是否被激活
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("虛擬環境狀態: 已激活")
        else:
            print("虛擬環境狀態: 未激活 (建議激活)")
    else:
        print("虛擬環境: 未找到 (建議創建)")
    
    # 檢查重要套件版本
    packages = {
        "numpy": "數值計算",
        "opencv-python-headless": "計算機視覺 (Headless)",
        "opencv-python": "計算機視覺",
        "onnxruntime": "ONNX 運行時",
        "onnxruntime-directml": "ONNX DirectML 加速",
        "onnxruntime-qnn": "ONNX QNN 加速",
        "mediapipe": "MediaPipe",
        "qai-hub": "QAI Hub SDK",
        "qai-hub-models": "QAI Hub 模型",
        "protobuf": "Protocol Buffers",
        "ctranslate2": "CTranslate2",
        "faster-whisper": "Faster Whisper"
    }
    
    print("\n已安裝套件版本:")
    for pkg, desc in packages.items():
        try:
            version = subprocess.check_output([sys.executable, '-m', 'pip', 'show', pkg]).decode().split('\n')[1].split(': ')[1]
            print(f"✅ {pkg}: {version} ({desc})")
        except:
            print(f"❌ {pkg}: 未安裝 ({desc})")
    
    return True

def check_system_architecture():
    """檢查系統架構"""
    print("\n=== 系統架構檢查 ===")
    
    system = platform.system()
    print(f"操作系統: {system}")
    
    machine = platform.machine()
    print(f"硬件架構: {machine}")
    
    is_arm64 = "arm64" in machine.lower() or "aarch64" in machine.lower()
    if is_arm64:
        print("✅ 檢測到 ARM64 架構")
        print("建議: 啟用 QNN / DirectML 加速")
    else:
        print("❓ 未檢測到 ARM64 架構")
        print("建議: 使用標準 CPU / DirectML 配置")
    
    # 在 Windows 上檢查是否是 Snapdragon
    if system == "Windows":
        try:
            cpu_info = subprocess.check_output("wmic cpu get name", shell=True).decode()
            if "qualcomm" in cpu_info.lower():
                print("✅ 檢測到 Qualcomm Snapdragon 處理器")
            else:
                print("❓ 未檢測到 Qualcomm Snapdragon 處理器")
        except:
            print("❓ 無法檢測處理器型號")
    
    return True

def check_qai_hub_config():
    """檢查 QAI Hub 配置"""
    print("\n=== QAI Hub 配置檢查 ===")
    
    # 檢查環境變量
    api_token = os.environ.get('QAI_HUB_API_TOKEN')
    if api_token:
        print("✅ QAI_HUB_API_TOKEN 環境變量: 已設置")
    else:
        print("❌ QAI_HUB_API_TOKEN 環境變量: 未設置")
    
    # 檢查 .qai_hub 目錄
    qai_hub_dir = Path.home() / ".qai_hub"
    if qai_hub_dir.exists():
        print(f"✅ QAI Hub 配置目錄: 已找到 ({qai_hub_dir})")
        
        # 檢查 client.ini 文件
        client_ini = qai_hub_dir / "client.ini"
        if client_ini.exists():
            print("✅ client.ini 文件: 已找到")
            
            # 檢查 client.ini 內容
            try:
                with open(client_ini, 'r') as f:
                    content = f.read()
                    if "api_key" in content:
                        print("✅ client.ini 內容: 包含 API 密鑰")
                    else:
                        print("❌ client.ini 內容: 缺少 API 密鑰")
            except:
                print("❌ client.ini 讀取失敗")
        else:
            print("❌ client.ini 文件: 未找到")
    else:
        print(f"❌ QAI Hub 配置目錄: 未找到 ({qai_hub_dir})")
    
    # 檢查項目配置文件
    config_path = Path.cwd() / "qai_hub_config.json"
    if config_path.exists():
        print(f"✅ 項目配置文件: 已找到 ({config_path})")
        
        # 檢查配置文件內容
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "api_token" in config:
                    print("✅ 配置文件內容: 包含 API 令牌")
                else:
                    print("❌ 配置文件內容: 缺少 API 令牌")
        except:
            print("❌ 配置文件讀取失敗")
    else:
        print(f"❌ 項目配置文件: 未找到 ({config_path})")
    
    # 檢查 .env 文件
    env_path = Path.home() / ".env"
    if env_path.exists():
        print(f"✅ .env 文件: 已找到 ({env_path})")
        
        # 檢查 .env 內容
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "QAI_HUB_API_TOKEN" in content:
                    print("✅ .env 內容: 包含 QAI_HUB_API_TOKEN")
                else:
                    print("❌ .env 內容: 缺少 QAI_HUB_API_TOKEN")
        except:
            print("❌ .env 讀取失敗")
    else:
        print(f"❌ .env 文件: 未找到 ({env_path})")
    
    # 測試 QAI Hub 連接
    print("\n嘗試連接 QAI Hub...")
    try:
        subprocess.check_call([sys.executable, 'setup_qai_hub.py', '--test'], stderr=subprocess.STDOUT)
        print("✅ QAI Hub 連接測試: 成功")
    except:
        print("❌ QAI Hub 連接測試: 失敗")
        print("建議: 運行 fix_dependencies.bat 修復相依性問題")
    
    return True

def check_dependencies_compatibility():
    """檢查相依性兼容性"""
    print("\n=== 相依性兼容性檢查 ===")
    
    # 檢查 protobuf 版本與 mediapipe 的兼容性
    try:
        import pkg_resources
        protobuf_version = pkg_resources.get_distribution("protobuf").version
        print(f"Protobuf 版本: {protobuf_version}")
        
        # MediaPipe 需要 protobuf >= 3.20.0, < 5.0.0
        protobuf_ver = pkg_resources.parse_version(protobuf_version)
        min_ver = pkg_resources.parse_version("3.20.0")
        max_ver = pkg_resources.parse_version("5.0.0")
        
        if min_ver <= protobuf_ver < max_ver:
            print("✅ Protobuf 版本與 MediaPipe 兼容")
        else:
            print("❌ Protobuf 版本與 MediaPipe 不兼容 (需要 3.20.0 - 4.25.3)")
            print("建議: 安裝兼容版本 - pip install protobuf==4.25.3")
    except:
        print("❌ 無法檢查 Protobuf 版本")
    
    # 測試 MediaPipe 導入
    try:
        import mediapipe
        print(f"✅ MediaPipe 導入成功 (版本: {mediapipe.__version__})")
    except Exception as e:
        print(f"❌ MediaPipe 導入失敗: {e}")
        print("建議: 重新安裝 MediaPipe - pip install mediapipe==0.10.14")
    
    # 測試 QAI Hub 導入
    try:
        import qai_hub
        print(f"✅ QAI Hub 導入成功")
    except Exception as e:
        print(f"❌ QAI Hub 導入失敗: {e}")
        print("建議: 重新安裝 QAI Hub - pip install qai-hub==0.31.0 qai-hub-models==0.33.1")
    
    return True

def provide_recommendations():
    """提供修復建議"""
    print("\n=== 修復建議 ===")
    print("1. 運行 fix_dependencies.bat 修復相依性問題")
    print("2. 確保設置了正確的 QAI Hub API 令牌")
    print("3. 如果使用虛擬環境，確保已激活虛擬環境")
    print("4. 在運行系統前，確保先運行 install_packages.bat")
    print("5. 檢查 .qai_hub/client.ini 文件是否正確設置")
    print("6. 手動測試 QAI Hub 連接: python setup_qai_hub.py --test")
    
    return True

def main():
    """主函數"""
    print("=== Dragon X Fall Detection 系統診斷工具 ===")
    print("===========================================")
    
    check_python_environment()
    check_system_architecture()
    check_qai_hub_config()
    check_dependencies_compatibility()
    provide_recommendations()
    
    print("\n診斷完成！請根據建議修復問題。")

if __name__ == "__main__":
    main()
