#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QAI Hub 簡易配置工具 - 修復版
Simple QAI Hub Configuration Tool - Fixed Version

直接使用 .env 文件中的 API Token 建立 QAI Hub 配置
Uses the API Token from .env file directly to create QAI Hub config
"""

import os
import sys
import configparser
from pathlib import Path
import re

def get_home_directory():
    """獲取用戶主目錄路徑"""
    return str(Path.home())

def create_qai_hub_config_directory():
    """創建 QAI Hub 配置目錄"""
    home_dir = get_home_directory()
    qai_hub_dir = os.path.join(home_dir, ".qai_hub")
    
    if not os.path.exists(qai_hub_dir):
        os.makedirs(qai_hub_dir)
        print(f"✅ 已創建 QAI Hub 配置目錄: {qai_hub_dir}")
    else:
        print(f"ℹ️ QAI Hub 配置目錄已存在: {qai_hub_dir}")
    
    return qai_hub_dir

def read_api_token_from_env_file():
    """從 .env 文件讀取 API Token"""
    try:
        env_path = os.path.join(os.getcwd(), ".env")
        if not os.path.exists(env_path):
            print(f"❌ 找不到 .env 文件: {env_path}")
            return None
        
        with open(env_path, 'r') as f:
            content = f.read()
            
        # 使用正則表達式查找 API Token
        match = re.search(r'QAI_HUB_API_TOKEN\s*=\s*([^\s#]+)', content)
        if match:
            token = match.group(1)
            print(f"✅ 從 .env 文件讀取了 API Token")
            return token
        else:
            print("❌ 在 .env 文件中找不到 QAI_HUB_API_TOKEN")
            return None
    except Exception as e:
        print(f"❌ 讀取 .env 文件時出錯: {e}")
        return None

def create_client_config(config_dir, api_token):
    """創建 QAI Hub 客戶端配置文件"""
    if not api_token:
        print("❌ 未提供 API Token，無法創建配置文件")
        return False
    
    config_path = os.path.join(config_dir, "client.ini")
    
    # 創建新配置
    config = configparser.ConfigParser()
    config['default'] = {
        'api_token': api_token,
        'api_url': 'https://api.qualcomm.com/v1/',
        'compiler_url': 'https://api.qualcomm.com/v1/compiler/',
        'devices_url': 'https://api.qualcomm.com/v1/devices/',
        'models_url': 'https://api.qualcomm.com/v1/models/'
    }
    
    try:
        with open(config_path, 'w') as f:
            config.write(f)
        
        # 設置合適的文件權限
        os.chmod(config_path, 0o600)  # 設置只有用戶可讀寫的權限
        
        print(f"✅ 已創建 QAI Hub 配置文件: {config_path}")
        return True
    except Exception as e:
        print(f"❌ 創建配置文件時出錯: {e}")
        return False

def main():
    """主函數"""
    print("🚀 QAI Hub 簡易配置工具 - 修復版")
    print("=" * 50)
    
    # 獲取 QAI Hub 配置目錄
    config_dir = create_qai_hub_config_directory()
    
    # 從 .env 文件獲取 API Token
    api_token = read_api_token_from_env_file()
    
    if not api_token:
        print("❌ 無法獲取 API Token，QAI Hub 設置失敗")
        return
    
    # 創建配置文件
    if create_client_config(config_dir, api_token):
        print("\n✅ QAI Hub 設置完成！")
        print("您現在可以使用 QAI Hub 功能了。")
    else:
        print("\n❌ QAI Hub 設置失敗。")

if __name__ == "__main__":
    main()
