#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 ONNX Runtime 加速器和平台優化
Check ONNX Runtime accelerators and platform optimizations
"""

import sys
import platform
import os

def get_platform_info():
    """獲取當前平台的詳細信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    python_version = sys.version
    
    # 檢測 ARM64 架構
    is_arm64 = 'arm64' in machine or 'aarch64' in machine
    
    print(f"系統: {system}")
    print(f"架構: {machine}")
    print(f"Python: {python_version}")
    print(f"ARM64: {'是' if is_arm64 else '否'}")
    
    return system, machine, is_arm64

def check_onnx_providers():
    """檢查 ONNX Runtime 可用的執行提供者"""
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        
        print("\nONNX Runtime 信息:")
        print(f"版本: {ort.__version__}")
        print("可用提供者:")
        
        # 分析提供者
        for i, provider in enumerate(providers, 1):
            if 'CoreML' in provider:
                note = "✅ Apple Silicon 最佳加速器"
            elif 'DML' in provider:
                note = "✅ Windows 最佳加速器"
            elif 'QNN' in provider:
                note = "✅ Snapdragon/ARM64 最佳加速器"
            elif 'CUDA' in provider:
                note = "✅ NVIDIA GPU 最佳加速器"
            elif 'CPU' in provider:
                note = "⚠️ 通用提供者 (無硬體加速)"
            else:
                note = ""
                
            print(f"  {i}. {provider} {note}")
            
        return providers
    except ImportError:
        print("❌ 未安裝 ONNX Runtime")
        return []

def check_torch_info():
    """檢查 PyTorch 信息"""
    try:
        import torch
        
        print("\nPyTorch 信息:")
        print(f"版本: {torch.__version__}")
        print(f"CUDA 可用: {torch.cuda.is_available()}")
        
        if hasattr(torch, 'backends') and hasattr(torch.backends, 'mps'):
            print(f"MPS (Apple Metal) 可用: {torch.backends.mps.is_available()}")
        
    except ImportError:
        print("❌ 未安裝 PyTorch")

def check_mediapipe_info():
    """檢查 MediaPipe 信息"""
    try:
        import mediapipe as mp
        
        print("\nMediaPipe 信息:")
        print(f"版本: {mp.__version__}")
        
    except ImportError:
        print("❌ 未安裝 MediaPipe")

def check_opencv_info():
    """檢查 OpenCV 信息"""
    try:
        import cv2
        
        print("\nOpenCV 信息:")
        print(f"版本: {cv2.__version__}")
        
    except ImportError:
        print("❌ 未安裝 OpenCV")

def main():
    """主函數"""
    print("🐉 Dragon X Fall Detection 平台優化檢查")
    print("=" * 50)
    
    system, machine, is_arm64 = get_platform_info()
    
    # 檢查 ONNX Runtime
    providers = check_onnx_providers()
    
    # 檢查 PyTorch
    check_torch_info()
    
    # 檢查 MediaPipe
    check_mediapipe_info()
    
    # 檢查 OpenCV
    check_opencv_info()
    
    # 輸出優化建議
    print("\n優化建議:")
    
    if is_arm64:
        print("✅ 檢測到 ARM64 架構")
        
        if system == 'darwin':  # macOS
            if any('CoreML' in p for p in providers):
                print("✅ 已啟用 CoreML 加速器 - 適合 Apple Silicon")
            else:
                print("⚠️ 建議安裝 onnxruntime-coreml 以獲得最佳性能")
                
        elif system == 'windows':
            if any('QNN' in p for p in providers):
                print("✅ 已啟用 QNN 加速器 - 適合 Snapdragon")
            else:
                print("⚠️ 建議安裝 onnxruntime-qnn 以獲得最佳性能")
    
    else:  # x64 架構
        if system == 'windows':
            if any('DML' in p for p in providers):
                print("✅ 已啟用 DirectML 加速器")
            else:
                print("⚠️ 建議安裝 onnxruntime-directml 以獲得更好性能")
    
    print("\n更多詳細資訊請參閱 PLATFORM_OPTIMIZATION_GUIDE.md")

if __name__ == "__main__":
    main()
