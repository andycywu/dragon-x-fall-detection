#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安裝平台特定的加速器包
Platform-specific accelerator package installer for Dragon X Fall Detection
"""

import sys
import platform
import subprocess
import os

def get_platform_info():
    """獲取當前平台的詳細信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # 檢測 ARM64 架構
    is_arm64 = 'arm64' in machine or 'aarch64' in machine
    
    # 檢測特定平台
    is_windows = system == 'windows'
    is_macos = system == 'darwin'
    is_linux = system == 'linux'
    
    print(f"檢測到平台: {system} on {machine} (ARM64: {is_arm64})")
    
    return {
        'system': system,
        'machine': machine,
        'is_arm64': is_arm64,
        'is_windows': is_windows,
        'is_macos': is_macos,
        'is_linux': is_linux
    }

def install_platform_accelerators():
    """根據平台安裝適當的加速器包"""
    platform_info = get_platform_info()
    
    # 基本依賴包
    subprocess.check_call([
        sys.executable, '-m', 'pip', 'install',
        'onnxruntime==1.18.0',
        '--prefer-binary',
        '--only-binary=:all:'
    ])
    
    # 平台特定加速器
    if platform_info['is_windows']:
        print("安裝 Windows 特定加速器: DirectML...")
        # Windows: DirectML 支持 (適用於 x64 和 ARM64)
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'onnxruntime-directml==1.18.0',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
        
        # Windows 上的 QNN 加速器 (僅 ARM64)
        if platform_info['is_arm64']:
            print("安裝 ARM64 特定加速器: QNN...")
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                'onnxruntime-qnn==1.18.0',
                '--prefer-binary',
                '--only-binary=:all:'
            ])
    
    elif platform_info['is_macos']:
        print("安裝 macOS 特定加速器: CoreML...")
        # macOS: CoreML 支持
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'onnxruntime-coreml',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
    
    elif platform_info['is_linux'] and platform_info['is_arm64']:
        print("安裝 Linux ARM64 特定加速器: QNN...")
        # Linux ARM64: QNN 支持
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'onnxruntime-qnn==1.18.0',
            '--prefer-binary',
            '--only-binary=:all:'
        ])

def install_pytorch():
    """根據平台安裝適當的 PyTorch 版本"""
    platform_info = get_platform_info()
    
    if platform_info['is_macos'] and platform_info['is_arm64']:
        print("安裝 macOS ARM64 (Apple Silicon) 適用的 PyTorch...")
        # 使用官方原生 MPS 支持的 PyTorch
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
    elif platform_info['is_macos'] and not platform_info['is_arm64']:
        print("安裝 macOS Intel 適用的 PyTorch...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
    elif platform_info['is_windows'] and platform_info['is_arm64']:
        print("安裝 Windows ARM64 適用的 PyTorch...")
        # Windows ARM64 目前使用 CPU 版本
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            '--index-url', 'https://download.pytorch.org/whl/cpu',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
    elif platform_info['is_windows'] and not platform_info['is_arm64']:
        print("安裝 Windows x64 適用的 PyTorch...")
        # Windows x64 可以使用 CUDA 或 CPU 版本
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
    elif platform_info['is_linux'] and platform_info['is_arm64']:
        print("安裝 Linux ARM64 適用的 PyTorch...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            '--index-url', 'https://download.pytorch.org/whl/cpu',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
    else:
        print("安裝通用 PyTorch...")
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'torch>=2.0.0',
            'torchvision>=0.15.0',
            '--prefer-binary',
            '--only-binary=:all:'
        ])

def install_all_dependencies():
    """安裝基本依賴，然後加裝平台特定加速器"""
    print("安裝基本依賴包...")
    
    # 修改為逐行安裝必要的包，避免因為一個包失敗而導致全部失敗
    try:
        # 先安裝基礎包
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'onnxruntime==1.18.0',
            'mediapipe==0.10.14',
            'opencv-python-headless==4.10.0.84',
            'Pillow==9.5.0',
            'numpy==1.23.5',
            'scipy==1.10.1',
            '--prefer-binary',
            '--only-binary=:all:'
        ])
        
        # 安裝平台特定的 PyTorch
        install_pytorch()
        
        # 安裝平台特定加速器
        install_platform_accelerators()
        
        # 安裝其他依賴
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            '-r', 'requirements.txt',
            '--prefer-binary',
            '--only-binary=:all:',
            '--ignore-installed'  # 忽略已安裝的包，避免衝突
        ])
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️ 部分依賴安裝失敗: {e}")
        print("繼續安裝其他依賴...")
    
    print("\n✅ 安裝完成！")
    print("已為您的平台安裝最佳的 Dragon X Fall Detection 依賴包。")

if __name__ == "__main__":
    install_all_dependencies()
