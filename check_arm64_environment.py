#!/usr/bin/env python3
"""
ARM64 環境檢測工具
檢測並顯示當前環境的 ARM64 相關信息
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path

def check_arm64_environment():
    """檢測 ARM64 環境"""
    # 系統信息
    system_name = platform.system()
    machine = platform.machine()
    processor = platform.processor()
    python_version = platform.python_version()
    python_implementation = platform.python_implementation()
    
    # 判斷是否為 ARM64
    is_arm64 = ('aarch64' in machine.lower() or 'arm64' in machine.lower())
    
    # 打印基本信息
    print("=== ARM64 環境檢測 ===")
    print(f"系統: {system_name}")
    print(f"架構: {machine}")
    print(f"處理器: {processor}")
    print(f"Python版本: {python_version}")
    print(f"Python實現: {python_implementation}")
    print(f"是否ARM64: {'✓' if is_arm64 else '✗'}")
    
    # 檢查Python是否為ARM64原生版本
    if is_arm64:
        # 在不同系統上檢查Python是否為ARM64原生
        if system_name.lower() == 'darwin':  # macOS
            print(f"Python路徑: {sys.executable}")
            result = subprocess.run(['file', sys.executable], capture_output=True, text=True)
            if 'arm64' in result.stdout.lower():
                print("Python版本: ✓ 原生ARM64")
            else:
                print("Python版本: ✗ 非原生ARM64 (可能通過Rosetta運行)")
        elif system_name.lower() == 'windows':  # Windows
            print(f"Python路徑: {sys.executable}")
            # Windows沒有file命令，使用其他方法
            if 'arm64' in sys.executable.lower() or 'aarch64' in sys.executable.lower():
                print("Python版本: ✓ 可能是原生ARM64")
            else:
                # 使用環境變量判斷
                if 'PROCESSOR_ARCHITECTURE' in os.environ and 'ARM64' in os.environ['PROCESSOR_ARCHITECTURE']:
                    print("Python版本: ✓ 可能是原生ARM64")
                else:
                    print("Python版本: ⚠ 無法確定是否為原生ARM64")
        else:  # Linux
            print(f"Python路徑: {sys.executable}")
            result = subprocess.run(['file', sys.executable], capture_output=True, text=True)
            if 'aarch64' in result.stdout.lower() or 'arm64' in result.stdout.lower():
                print("Python版本: ✓ 原生ARM64")
            else:
                print("Python版本: ✗ 非原生ARM64")
    
    # 檢查關鍵包是否為ARM64版本
    print("\n=== 關鍵套件檢測 ===")
    packages_to_check = ['numpy', 'opencv-python', 'mediapipe', 'torch', 'onnxruntime']
    
    for package in packages_to_check:
        try:
            # 使用pip顯示包信息
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # 提取版本信息
                version_line = [line for line in result.stdout.split('\n') if line.startswith('Version:')]
                if version_line:
                    version = version_line[0].split('Version:')[1].strip()
                    print(f"{package}: ✓ 已安裝 (版本: {version})")
                    
                    # 對於某些包，額外檢查是否為ARM64版本
                    if package == 'torch':
                        try:
                            import torch
                            if hasattr(torch, '_C'):
                                # 如果有_C屬性，可能是原生版本
                                print(f"  - {'✓' if torch.version.cuda is None else '⚠'} CPU版本")
                            else:
                                print(f"  - ⚠ 可能非原生")
                        except ImportError:
                            pass
                    
                    elif package == 'onnxruntime':
                        try:
                            import onnxruntime as ort
                            providers = ort.get_available_providers()
                            print(f"  - 可用提供商: {', '.join(providers)}")
                            
                            # 檢查是否有ARM64專有提供商
                            arm_providers = [p for p in providers if 'ARM' in p or 'Qnn' in p or 'DirectML' in p]
                            if arm_providers:
                                print(f"  - ✓ 發現ARM64優化提供商: {', '.join(arm_providers)}")
                            else:
                                print(f"  - ⚠ 未發現ARM64專用提供商")
                        except ImportError:
                            pass
                else:
                    print(f"{package}: ✓ 已安裝 (無法獲取版本信息)")
            else:
                print(f"{package}: ✗ 未安裝")
        except Exception as e:
            print(f"{package}: ⚠ 檢測錯誤 ({str(e)})")
    
    # 檢測硬件加速器
    print("\n=== 硬件加速器檢測 ===")
    
    # 檢測CUDA/ROCm
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA: ✓ 可用 (設備數: {torch.cuda.device_count()})")
            for i in range(torch.cuda.device_count()):
                print(f"  - 設備 {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("CUDA: ✗ 不可用")
    except ImportError:
        print("CUDA: ⚠ 無法檢測 (PyTorch未安裝)")
    
    # 檢測Apple Neural Engine (Mac only)
    if system_name.lower() == 'darwin' and is_arm64:
        try:
            # 檢查coremltools是否可用
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'coremltools'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Apple Neural Engine: ✓ 可能可用 (已安裝coremltools)")
            else:
                print("Apple Neural Engine: ⚠ 可能可用 (未安裝coremltools)")
        except:
            print("Apple Neural Engine: ⚠ 檢測失敗")
    
    # 檢測DirectML (Windows only)
    if system_name.lower() == 'windows':
        try:
            # 檢查onnxruntime-directml是否可用
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'onnxruntime-directml'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("DirectML: ✓ 可能可用 (已安裝onnxruntime-directml)")
            else:
                print("DirectML: ✗ 可能不可用 (未安裝onnxruntime-directml)")
        except:
            print("DirectML: ⚠ 檢測失敗")
    
    # 檢測QNN (Qualcomm Neural Network)
    try:
        # 檢查onnxruntime-qnn是否可用
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'onnxruntime-qnn'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Qualcomm QNN: ✓ 可能可用 (已安裝onnxruntime-qnn)")
        else:
            print("Qualcomm QNN: ✗ 可能不可用 (未安裝onnxruntime-qnn)")
    except:
        print("Qualcomm QNN: ⚠ 檢測失敗")
    
    # 環境變數檢測
    print("\n=== 環境變數檢測 ===")
    env_vars_to_check = [
        'ONNXRUNTIME_PROVIDER_PRIORITY',
        'ORT_LOGGING_LEVEL',
        'QAI_PREFER_NATIVE_MODELS',
        'PYTORCH_ENABLE_ARM64_NATIVE',
        'QAI_HUB_API_TOKEN'
    ]
    
    for var in env_vars_to_check:
        if var in os.environ:
            # 對於API令牌，不顯示完整值
            if 'TOKEN' in var or 'KEY' in var:
                value = "****" + os.environ[var][-4:] if len(os.environ[var]) > 4 else "****"
            else:
                value = os.environ[var]
            print(f"{var}: ✓ 已設置 ({value})")
        else:
            print(f"{var}: ✗ 未設置")
    
    # 生成報告
    report = {
        "system": {
            "name": system_name,
            "machine": machine,
            "processor": processor,
            "is_arm64": is_arm64
        },
        "python": {
            "version": python_version,
            "implementation": python_implementation,
            "path": sys.executable
        },
        "packages": {},
        "accelerators": {},
        "environment_variables": {}
    }
    
    # 將報告保存為JSON
    report_path = Path(__file__).parent / "arm64_environment_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== 環境報告已生成: {report_path} ===")
    
    return is_arm64

if __name__ == "__main__":
    is_arm64 = check_arm64_environment()
    
    if is_arm64:
        print("\n>>> 檢測到ARM64環境！")
        print("建議: 使用專為ARM64優化的套件獲得最佳性能")
    else:
        print("\n>>> 未檢測到ARM64環境")
        print("注意: 在非ARM64環境中，某些優化可能不適用")
