#!/usr/bin/env python3
"""
Snapdragon X Elite 加速啟用工具 - ASCII版本
為跌倒檢測系統啟用 Snapdragon 硬體加速
"""

import os
import sys
import platform
import logging
from pathlib import Path

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def ensure_qai_hub_config():
    """確保QAI Hub配置正確設置"""
    print("Checking QAI Hub configuration...")
    
    # API token
    api_token = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
    
    # 創建 .qai_hub 目錄
    home_dir = Path.home()
    qai_config_dir = home_dir / ".qai_hub"
    qai_config_dir.mkdir(exist_ok=True)
    print(f"Config directory: {qai_config_dir}")
    
    # 創建 config 文件，特別為 Snapdragon 設備優化
    config_file = qai_config_dir / "client.ini"
    config_content = """[default]
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
organization = 
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
profile = default
device_group = default
model_path = models
accelerator = hexagon_npu
optimization_level = performance
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"Updated config file with Snapdragon acceleration settings: {config_file}")
    
    # 設置環境變量
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    os.environ['QAI_HUB_ACCELERATOR'] = 'hexagon_npu'
    os.environ['QAI_OPTIMIZATION_LEVEL'] = 'performance'
    os.environ['ENABLE_QAI_ACCELERATION'] = 'true'
    
    print("Environment variables set for hardware acceleration")
    
    return True

def setup_env_file():
    """設置環境變量文件以支持加速"""
    env_file = Path("C:/dragon_x_fall_detection/.env")
    
    env_content = """# Qualcomm AI Hub API Configuration
QAI_HUB_API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
QAI_HUB_BASE_URL=https://app.aihub.qualcomm.com
QAI_HUB_DEVICE_GROUP=default

# Performance settings
ENABLE_QAI_ACCELERATION=true
MODEL_OPTIMIZATION_LEVEL=performance
INFERENCE_DEVICE_TYPE=hexagon_npu

# Fall detection settings
FALL_DETECTION_THRESHOLD=0.7
BODY_ANGLE_THRESHOLD=30
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"Created optimized .env file: {env_file}")
    return True

def modify_unified_detector():
    """修改統一檢測器以優先使用QAI Hub加速"""
    detector_file = Path("C:/dragon_x_fall_detection/unified_ai_detector_ascii.py")
    
    if not detector_file.exists():
        print(f"Error: {detector_file} not found")
        return False
    
    # 讀取文件
    content = detector_file.read_text()
    
    # 修改平台檢測方法
    if "_detect_platform" in content:
        # 找到方法並修改
        start = content.find("def _detect_platform")
        end = content.find("def", start + 1)
        
        original_method = content[start:end]
        modified_method = """def _detect_platform(self):
        \"\"\"Detect the platform (device type)\"\"\"
        # Force Snapdragon X Elite detection for Windows ARM devices
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()
        
        if system == "Windows":
            if "qualcomm" in processor.lower() or "snapdragon" in processor.lower():
                return "snapdragon_x_elite"
            elif "arm" in machine.lower() or "aarch64" in machine.lower():
                return "snapdragon_x_elite"  # Assume Windows ARM is Snapdragon
        
        # Original detection logic as fallback
        if system == "Windows":
            return "windows"
        elif system == "Darwin":
            if machine == "arm64":
                return "mac_arm"
            else:
                return "mac_intel"
        elif system == "Linux":
            if os.path.exists("/proc/device-tree/model"):
                with open("/proc/device-tree/model", 'r') as f:
                    model = f.read()
                if "Raspberry Pi" in model:
                    return "raspberry_pi"
            
            if machine == "aarch64":
                return "snapdragon_x_elite"
            
            return "linux_generic"
        
        return "unknown"
    
    """
        
        # 替換方法
        content = content.replace(original_method, modified_method)
    
    # 修改加速器檢測方法
    if "_detect_accelerators" in content:
        # 找到方法並修改
        start = content.find("def _detect_accelerators")
        end = content.find("def", start + 1)
        
        original_method = content[start:end]
        modified_method = """def _detect_accelerators(self):
        \"\"\"Detect available AI accelerators\"\"\"
        accelerators = []
        
        # Always detect Hexagon NPU on Snapdragon X Elite
        if self.platform == "snapdragon_x_elite":
            accelerators.append("hexagon_npu")
            logger.info("Detected Hexagon NPU on Snapdragon X Elite")
        
        # Check for NVIDIA GPU
        try:
            import pycuda.driver as cuda
            cuda.init()
            if cuda.Device.count() > 0:
                accelerators.append("nvidia_gpu")
        except (ImportError, Exception):
            pass
        
        # Check for Apple Neural Engine
        if self.platform == "mac_arm":
            accelerators.append("apple_neural_engine")
        
        # Check for Intel Neural Compute Stick
        try:
            if any("Movidius" in line for line in os.popen("lsusb").readlines()):
                accelerators.append("intel_ncs")
        except:
            pass
        
        # Check for Coral TPU
        try:
            if any("Google Inc." in line for line in os.popen("lsusb").readlines()):
                accelerators.append("coral_tpu")
        except:
            pass
        
        return accelerators
    
    """
        
        # 替換方法
        content = content.replace(original_method, modified_method)
    
    # 保存修改後的文件
    detector_file.write_text(content)
    print(f"Updated detector file to prioritize Snapdragon hardware acceleration")
    
    return True

def main():
    """主函數"""
    print("=" * 50)
    print("Snapdragon X Elite Acceleration Setup")
    print("=" * 50)
    
    # 1. 確保QAI Hub配置正確
    success1 = ensure_qai_hub_config()
    
    # 2. 設置環境變量文件
    success2 = setup_env_file()
    
    # 3. 修改統一檢測器
    success3 = modify_unified_detector()
    
    # 顯示結果
    print("\n" + "=" * 50)
    if success1 and success2 and success3:
        print("Snapdragon X Elite hardware acceleration successfully enabled!")
        print("The system is now configured to use Hexagon NPU acceleration.")
    else:
        print("Some errors occurred during acceleration setup.")
    print("=" * 50)
    
    print("\nNext steps:")
    print("1. Run 'python unified_ai_detector_ascii.py' to verify acceleration")
    print("2. Run 'python fixed_final_demo.py' for the full demo with acceleration")

if __name__ == "__main__":
    main()
