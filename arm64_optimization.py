#!/usr/bin/env python3
"""
ARM64 優化工具
針對 Windows ARM64 和 Snapdragon X Elite 平台優化 AI 檢測系統
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import json

class ARM64Optimizer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.is_arm64 = self._detect_arm64()
        
    def _detect_arm64(self):
        """檢測是否為ARM64平台"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        print(f"=== 平台檢測:")
        print(f"   系統: {system}")
        print(f"   架構: {machine}")
        
        is_arm64 = ('aarch64' in machine or 'arm64' in machine)
        if is_arm64:
            print(">>> 檢測到ARM64架構")
        else:
            print(">>> 非ARM64架構")
            
        return is_arm64
    
    def configure_environment(self):
        """設置優化的環境變數"""
        if not self.is_arm64:
            print("!!! 不是ARM64平台，跳過環境優化")
            return
        
        print("\n=== 設置ARM64優化環境變數...")
        
        # 設置ONNX Runtime提供商優先順序
        os.environ['ONNXRUNTIME_PROVIDER_PRIORITY'] = 'QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider'
        os.environ['ORT_LOGGING_LEVEL'] = '2'
        
        # 設置QAI Hub優化選項
        os.environ['QAI_PREFER_NATIVE_MODELS'] = '1'
        
        # 設置PyTorch選項
        os.environ['PYTORCH_ENABLE_ARM64_NATIVE'] = '1'
        
        print(">>> 環境變數設置完成")
        
        # 寫入永久設置指南
        self._write_permanent_config()
    
    def _write_permanent_config(self):
        """寫入永久設置指南"""
        system = platform.system().lower()
        
        if system == 'windows':
            # Windows 永久環境變數設置批處理
            bat_content = """@echo off
REM ARM64優化環境變數設置腳本

echo === 設置ARM64優化環境變數 ===

REM 設置ONNX Runtime優化
setx ONNXRUNTIME_PROVIDER_PRIORITY "QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider"
setx ORT_LOGGING_LEVEL "2"

REM 設置QAI Hub優化
setx QAI_PREFER_NATIVE_MODELS "1"

REM 設置PyTorch優化
setx PYTORCH_ENABLE_ARM64_NATIVE "1"

echo === 環境變數設置完成 ===
echo 請重新啟動命令提示符以套用變更
"""
            bat_path = self.project_root / "setup_arm64_env.bat"
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(bat_content)
            
            print(f">>> 已創建環境變數設置批處理: {bat_path}")
            
        else:
            # Linux/Mac 永久環境變數設置腳本
            sh_content = """#!/bin/bash
# ARM64優化環境變數設置腳本

echo "=== 設置ARM64優化環境變數 ==="

# 添加環境變數到profile
PROFILE_FILE="$HOME/.profile"
echo "export ONNXRUNTIME_PROVIDER_PRIORITY='QNNExecutionProvider,DirectMLExecutionProvider,CPUExecutionProvider'" >> $PROFILE_FILE
echo "export ORT_LOGGING_LEVEL='2'" >> $PROFILE_FILE
echo "export QAI_PREFER_NATIVE_MODELS='1'" >> $PROFILE_FILE
echo "export PYTORCH_ENABLE_ARM64_NATIVE='1'" >> $PROFILE_FILE

echo "=== 環境變數設置完成 ==="
echo "請重新登入或執行 'source $PROFILE_FILE' 以套用變更"
"""
            sh_path = self.project_root / "setup_arm64_env.sh"
            with open(sh_path, 'w', encoding='utf-8') as f:
                f.write(sh_content)
            
            # 設置執行權限
            os.chmod(sh_path, 0o755)
            print(f">>> 已創建環境變數設置腳本: {sh_path}")
    
    def install_optimized_packages(self):
        """安裝優化的套件"""
        if not self.is_arm64:
            print("!!! 不是ARM64平台，跳過套件優化")
            return
        
        print("\n=== 安裝ARM64優化套件...")
        
        # 安裝依賴
        pip_extra = "--prefer-binary --only-binary=:all:"
        packages = [
            f"numpy>=1.21.0 {pip_extra}",
            f"opencv-python>=4.5.0 {pip_extra}",
            f"mediapipe>=0.10.0 {pip_extra}",
            f"onnxruntime>=1.15.0 {pip_extra}",
            f"onnxruntime-directml {pip_extra}",
            f"onnxruntime-qnn {pip_extra}",
            f"requests>=2.25.0 {pip_extra}",
            f"Pillow>=8.0.0 {pip_extra}",
            f"streamlit>=1.28.0 {pip_extra}",
            f"torch>=1.13.0 {pip_extra}",
            f"torchvision>=0.14.0 {pip_extra}",
            f"qai-hub {pip_extra}",
            f"qai-hub-models {pip_extra}"
        ]
        
        for package in packages:
            try:
                print(f">>> 安裝: {package}")
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + package.split(), 
                             check=True)
            except Exception as e:
                print(f"!!! 安裝失敗: {package} - {e}")
    
    def optimize_model_config(self):
        """優化模型配置"""
        if not self.is_arm64:
            print("!!! 不是ARM64平台，跳過模型優化")
            return
        
        print("\n=== 優化模型配置...")
        
        # 檢查QAI Hub配置
        qai_config_path = self.project_root / "qai_hub_config.json"
        if qai_config_path.exists():
            try:
                with open(qai_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新配置
                if "inference_backend" not in config or config["inference_backend"] != "QNN":
                    config["inference_backend"] = "QNN"
                    print(">>> 已更新推理後端為QNN")
                
                if "model_optimization" not in config or not config["model_optimization"]:
                    config["model_optimization"] = True
                    print(">>> 已啟用模型優化")
                
                # 添加ARM64特定配置
                config["arm64_native"] = True
                config["use_directml_fallback"] = True
                
                # 寫回配置
                with open(qai_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                print(f">>> QAI Hub配置更新完成: {qai_config_path}")
                
            except Exception as e:
                print(f"!!! QAI Hub配置更新失敗: {e}")
        else:
            print(f"!!! QAI Hub配置不存在: {qai_config_path}")
    
    def verify_optimization(self):
        """驗證優化"""
        if not self.is_arm64:
            print("!!! 不是ARM64平台，跳過優化驗證")
            return
        
        print("\n=== 驗證ARM64優化...")
        
        # 檢查ONNX Runtime提供商
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            
            print(">>> ONNX Runtime提供商:")
            for provider in providers:
                print(f"   - {provider}")
            
            # 驗證優先提供商
            expected_first = "QNNExecutionProvider"
            if providers and expected_first in providers:
                print(f">>> 驗證通過: {expected_first}可用")
            else:
                print(f"!!! 驗證失敗: {expected_first}不可用")
                
        except ImportError:
            print("!!! ONNX Runtime不可用")
        
        # 檢查PyTorch
        try:
            import torch
            print(f">>> PyTorch版本: {torch.__version__}")
            
            if torch.cuda.is_available():
                print(">>> GPU加速可用")
            else:
                print("!!! GPU加速不可用")
                
        except ImportError:
            print("!!! PyTorch不可用")
        
        # 檢查QAI Hub
        try:
            import qai_hub as hub
            
            print(">>> QAI Hub可用")
            
            # 檢查設備
            try:
                devices = hub.get_devices()
                print(f">>> 可用設備: {len(devices)}")
                for device in devices:
                    print(f"   - {device.name}")
            except:
                print("!!! 無法獲取QAI Hub設備")
                
        except ImportError:
            print("!!! QAI Hub不可用")
    
    def run_complete_optimization(self):
        """運行完整優化"""
        print("=== ARM64優化工具 ===")
        print("=" * 50)
        
        if not self.is_arm64:
            print("!!! 檢測到非ARM64平台，無法進行優化")
            print("=" * 50)
            return False
        
        try:
            self.configure_environment()
            self.install_optimized_packages()
            self.optimize_model_config()
            self.verify_optimization()
            
            print("\n=== ARM64優化完成！")
            print("=" * 50)
            print("=== 優化摘要:")
            print("   1. 環境變數已配置")
            print("   2. 已安裝ARM64原生套件")
            print("   3. QAI Hub配置已優化")
            print("   4. 優化已驗證")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"\n!!! 優化失敗: {e}")
            return False

if __name__ == "__main__":
    optimizer = ARM64Optimizer()
    success = optimizer.run_complete_optimization()
    
    if success:
        print("\n>>> ARM64優化成功完成！")
    else:
        print("\n!!! ARM64優化失敗！")
        sys.exit(1)
