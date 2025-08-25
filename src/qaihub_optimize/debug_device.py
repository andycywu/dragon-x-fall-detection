#!/usr/bin/env python3
"""
调试设备属性获取问题
"""
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from modules.qaihub_client import QAIHubClient

def debug_device_attributes():
    """调试设备属性获取"""
    print("🔍 调试设备属性获取...")
    
    # 初始化 QAI Hub 客户端
    base_dir = Path('/Users/andycyw/mvp_fall_detection_starter/src/models')
    client = QAIHubClient(base_dir)
    
    print(f"📱 目标设备: {client.target_device.name if client.target_device else 'None'}")
    
    if client.target_device:
        # 获取设备属性
        device_attrs = getattr(client.target_device, 'attributes', [])
        print(f"📋 设备属性列表: {device_attrs}")
        print(f"📋 设备属性类型: {type(device_attrs)}")
        
        # 详细检查每个属性
        print("\n🔍 详细检查每个属性:")
        for i, attr in enumerate(device_attrs):
            print(f"  [{i}] {attr} (类型: {type(attr)})")
            
            # 尝试检查是否包含框架信息
            if hasattr(attr, '__str__'):
                attr_str = str(attr).lower()
                print(f"     字符串表示: {attr_str}")
                
                # 检查各种框架
                for framework in ['onnx', 'tflite', 'dlc']:
                    if f'framework:{framework}' in attr_str:
                        print(f"     ✅ 检测到 {framework.upper()} 支持")
        
        # 使用改进的检查方法
        print("\n🔧 使用改进的检查方法:")
        support_info = {
            'onnx': False,
            'tflite': False,
            'dlc': False
        }
        
        for attr in device_attrs:
            attr_str = str(attr).lower()
            for framework in support_info.keys():
                if f'framework:{framework}' in attr_str:
                    support_info[framework] = True
                    print(f"✅ 检测到 {framework.upper()} 支持: {attr_str}")
        
        print(f"\n📊 最终支持信息: {support_info}")
        
        # 测试 check_device_support 方法
        print("\n🧪 测试 check_device_support 方法:")
        result = client.check_device_support()
        print(f"方法返回结果: {result}")
        
    else:
        print("❌ 无法获取目标设备")

if __name__ == "__main__":
    debug_device_attributes()
