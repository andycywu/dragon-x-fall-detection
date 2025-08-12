#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QAI Hub 連接測試 - 簡化版
QAI Hub Connection Test - Simplified Version

此腳本用於測試 QAI Hub 的連接是否正常
This script is used to test if the connection to QAI Hub is working properly
"""

import os
import sys
from pathlib import Path

def check_environment_variables():
    """檢查與 QAI Hub 相關的環境變數"""
    api_token = os.environ.get('QAI_HUB_TOKEN')
    if api_token:
        masked_token = "****" + api_token[-4:] if len(api_token) > 4 else "****"
        print(f"✅ 找到環境變數 QAI_HUB_TOKEN: {masked_token}")
    else:
        print("⚠️ 找不到環境變數 QAI_HUB_TOKEN")
    
    base_url = os.environ.get('QAI_HUB_BASE_URL')
    if base_url:
        print(f"✅ 找到環境變數 QAI_HUB_BASE_URL: {base_url}")
    
    device_group = os.environ.get('QAI_HUB_DEVICE_GROUP')
    if device_group:
        print(f"✅ 找到環境變數 QAI_HUB_DEVICE_GROUP: {device_group}")

def check_config_file():
    """檢查 QAI Hub 配置文件"""
    home_dir = str(Path.home())
    config_path = os.path.join(home_dir, ".qai_hub", "client.ini")
    
    if os.path.exists(config_path):
        print(f"✅ 找到 QAI Hub 配置文件: {config_path}")
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                if 'api_token' in content:
                    print("✅ 配置文件包含 API Token")
                else:
                    print("⚠️ 配置文件不包含 API Token")
        except Exception as e:
            print(f"⚠️ 無法讀取配置文件: {e}")
    else:
        print(f"❌ 找不到 QAI Hub 配置文件: {config_path}")

def test_qai_hub_import():
    """測試 QAI Hub 包是否可以正確導入"""
    try:
        import qai_hub
        print(f"✅ 成功導入 QAI Hub 包 (版本: {qai_hub.__version__})")
        return True
    except ImportError as e:
        print(f"❌ 無法導入 QAI Hub 包: {e}")
        print("提示: 請安裝 QAI Hub 包: pip install qai-hub==0.9.0")
        return False

def test_minimal_connection():
    """嘗試使用最小化代碼連接 QAI Hub"""
    try:
        from qai_hub.client import Client, ClientConfig
        
        print("嘗試連接 QAI Hub...")
        
        # 嘗試從配置文件讀取設置
        home_dir = str(Path.home())
        config_path = os.path.join(home_dir, ".qai_hub", "client.ini")
        
        if not os.path.exists(config_path):
            print(f"❌ 配置文件不存在: {config_path}")
            return False
        
        # 讀取配置文件
        import configparser
        config_parser = configparser.ConfigParser()
        config_parser.read(config_path)
        
        # 檢查必要的配置
        if 'api' not in config_parser:
            print("❌ 配置文件缺少 'api' 部分")
            return False
            
        section = config_parser['api']
        
        # 檢查必要的字段
        required_fields = ['api_token', 'api_url', 'web_url']
        missing_fields = [field for field in required_fields if field not in section]
        
        if missing_fields:
            print(f"❌ 配置文件缺少以下字段: {', '.join(missing_fields)}")
            return False
            
        # 創建 ClientConfig 對象
        config = ClientConfig(
            api_url=section['api_url'],
            web_url=section['web_url'],
            api_token=section['api_token'],
            verbose=True
        )
        
        client = Client(config)
        print("✅ 成功創建 QAI Hub 客戶端")
        
        # 嘗試獲取設備列表
        try:
            print("獲取可用設備...")
            devices = client.get_devices()
            print(f"✅ 成功獲取設備列表 (找到 {len(devices)} 個設備)")
            
            # 列出前三個設備
            if devices:
                print("\n可用設備:")
                for i, device in enumerate(devices[:3], 1):
                    print(f"  {i}. {device.name} (ID: {device.id}, 處理器: {device.processor})")
                if len(devices) > 3:
                    print(f"  ... 以及其他 {len(devices) - 3} 個設備")
            
            return True
        except Exception as e:
            print(f"❌ 獲取設備列表失敗: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 連接 QAI Hub 失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔍 QAI Hub 連接測試 - 簡化版")
    print("=" * 50)
    
    # 檢查環境變數
    print("\n檢查環境變數:")
    check_environment_variables()
    
    # 檢查配置文件
    print("\n檢查配置文件:")
    check_config_file()
    
    # 測試包導入
    print("\n測試 QAI Hub 包導入:")
    if not test_qai_hub_import():
        return
    
    # 測試連接
    print("\n測試 QAI Hub 連接:")
    if test_minimal_connection():
        print("\n✅ QAI Hub 連接測試成功！您可以使用 QAI Hub 功能。")
    else:
        print("\n❌ QAI Hub 連接測試失敗。請檢查您的 API Token 和網絡連接。")
        print("提示: 您可以運行 setup_qai_hub_fixed.py 或 setup_qai_hub_env.sh 來設置 QAI Hub。")

if __name__ == "__main__":
    main()
