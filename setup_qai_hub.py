#!/usr/bin/env python3
"""
QAI Hub 設置工具
在 Snapdragon X Elite 平台設置 QAI Hub 認證
"""

import os
import sys
import configparser
from pathlib import Path
import json
import argparse

def setup_qai_hub_credentials(api_token=None):
    """設置 QAI Hub 認證"""
    print("=== QAI Hub 認證設置工具 ===")
    
    # 獲取 API 令牌
    if not api_token:
        # 檢查環境變量
        api_token = os.environ.get('QAI_HUB_API_TOKEN')
        
        # 如果環境變量中沒有，從配置文件中讀取
        if not api_token:
            config_path = Path.cwd() / "qai_hub_config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        api_token = config.get('api_token')
                        if api_token:
                            print(f">>> 從配置文件獲取到 API 令牌")
                except Exception as e:
                    print(f"!!! 讀取配置文件失敗: {e}")
    
    # 如果仍然沒有 API 令牌，要求用戶輸入
    if not api_token:
        print("!!! 未找到 QAI Hub API 令牌")
        print("請訪問 https://aihub.qualcomm.com/ 獲取訪問權限")
        print("如果您已有訪問權限，請參考 https://app.aihub.qualcomm.com/docs 獲取設置說明")
        api_token = input("請輸入您的 QAI Hub API 令牌: ").strip()
        
        if not api_token:
            print("!!! 未提供 API 令牌，無法繼續設置")
            return False
    
    # 創建 QAI Hub 配置目錄
    config_dir = Path.home() / ".qai_hub"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # 創建配置文件
    config_file = config_dir / "client.ini"
    
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'api_key': api_token
    }
    
    # 寫入配置文件
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f">>> QAI Hub 認證已設置: {config_file}")
    
    # 設置環境變量
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    
    print(">>> QAI Hub 環境變量已設置")
    
    # 創建示例 QAI Hub 配置文件
    example_config = {
        "api_token": api_token,
        "device_preference": "Snapdragon X Elite CRD",
        "fallback_device": "Snapdragon X Plus 8-Core CRD",
        "inference_backend": "QNN",
        "model_optimization": True,
        "arm64_native": True,
        "use_directml_fallback": True
    }
    
    example_config_path = Path.cwd() / "qai_hub_config.json"
    with open(example_config_path, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2)
    
    print(f">>> QAI Hub 配置範例已創建: {example_config_path}")
    
    return True

def test_qai_hub_connection():
    """測試 QAI Hub 連接"""
    print("\n=== 測試 QAI Hub 連接 ===")
    
    try:
        import qai_hub as hub
        
        # 獲取設備列表
        devices = hub.get_devices()
        print(f">>> 成功連接到 QAI Hub!")
        print(f">>> 可用設備數量: {len(devices)}")
        
        if devices:
            print(">>> 可用設備列表:")
            for i, device in enumerate(devices):
                print(f"   {i+1}. {device.name}")
        
        return True
    except Exception as e:
        print(f"!!! QAI Hub 連接失敗: {e}")
        return False

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='QAI Hub 設置工具')
    parser.add_argument('--token', type=str, help='QAI Hub API 令牌')
    parser.add_argument('--test', action='store_true', help='測試 QAI Hub 連接')
    
    args = parser.parse_args()
    
    if args.test:
        # 只進行測試
        test_qai_hub_connection()
    else:
        # 設置認證
        success = setup_qai_hub_credentials(args.token)
        
        if success and input("是否測試 QAI Hub 連接? (y/n): ").lower() == 'y':
            test_qai_hub_connection()

if __name__ == "__main__":
    main()
