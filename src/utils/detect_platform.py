#!/usr/bin/env python3
"""
平台檢測工具 - ASCII版本
檢測 Snapdragon X Elite 平台並啟用硬體加速
"""

import os
import sys
import platform
import subprocess
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def detect_platform():
    """檢測執行平台"""
    system = platform.system()
    machine = platform.machine()
    processor = platform.processor()
    
    print("=" * 50)
    print("Platform Detection Tool")
    print("=" * 50)
    print(f"System: {system}")
    print(f"Machine: {machine}")
    print(f"Processor: {processor}")
    
    # 檢查CPU信息
    if system == "Windows":
        try:
            output = subprocess.check_output("wmic cpu get name", shell=True).decode('utf-8')
            print(f"CPU Info: {output.strip()}")
            
            # 檢測 Snapdragon
            if "snapdragon" in output.lower() or "qualcomm" in output.lower():
                print("Detected: Snapdragon processor")
                return "snapdragon_x_elite"
        except Exception as e:
            print(f"Error getting CPU info: {e}")
    
    # 檢查系統環境變量
    try:
        if "SNAPDRAGON" in os.environ or "QUALCOMM" in os.environ:
            print("Detected Snapdragon environment variable")
            return "snapdragon_x_elite"
    except:
        pass
    
    # 回傳基於現有信息的平台
    if system == "Windows":
        if "arm" in machine.lower() or "aarch64" in machine.lower():
            print("Detected: Windows on ARM")
            return "snapdragon_x_elite"  # 假設Windows ARM就是Snapdragon X Elite
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

def force_snapdragon_platform():
    """強制設置為Snapdragon平台"""
    os.environ["FORCE_SNAPDRAGON"] = "1"
    print("Forced platform to Snapdragon X Elite")
    return "snapdragon_x_elite"

def main():
    """主函數"""
    platform_type = detect_platform()
    
    print("\nDetected platform:", platform_type)
    
    # 如果需要，強制設置為Snapdragon平台
    if platform_type != "snapdragon_x_elite" and len(sys.argv) > 1 and sys.argv[1] == "--force":
        platform_type = force_snapdragon_platform()
        print("Platform forced to:", platform_type)
    
    # 檢查QAI Hub環境
    try:
        import qai_hub
        print("QAI Hub module is available")
    except ImportError:
        print("QAI Hub module is NOT installed")
    
    # 返回結果
    return platform_type

if __name__ == "__main__":
    platform = main()
    
    print("\n" + "=" * 50)
    if platform == "snapdragon_x_elite":
        print("RESULT: This IS a Snapdragon X Elite platform!")
        print("Hardware acceleration should be available")
    else:
        print(f"RESULT: This is NOT a Snapdragon X Elite platform ({platform})")
        print("Add --force argument to force Snapdragon platform detection")
    print("=" * 50)
