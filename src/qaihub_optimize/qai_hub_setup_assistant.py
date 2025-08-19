#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QAI Hub 設置助手
QAI Hub Setup Assistant

此工具幫助設置 QAI Hub 連接所需的配置文件和憑證。
This tool helps set up the configuration files and credentials needed for QAI Hub connections.
"""

import os
import sys
import platform
from pathlib import Path
import configparser
import getpass

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

def check_existing_config(config_path):
    """檢查是否已存在配置文件"""
    if os.path.exists(config_path):
        print(f"ℹ️ 發現現有 QAI Hub 配置文件: {config_path}")
        
        # 嘗試讀取現有配置
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            if 'default' in config and 'api_token' in config['default']:
                masked_token = "****" + config['default']['api_token'][-4:] if len(config['default']['api_token']) > 4 else "****"
                print(f"ℹ️ 現有 API Token: {masked_token}")
                
                # 詢問是否覆蓋
                response = input("是否要覆蓋現有配置？(y/n): ").lower()
                return response == 'y'
        except Exception as e:
            print(f"⚠️ 無法讀取現有配置: {e}")
            return True
    
    return True

def get_api_token():
    """獲取 QAI Hub API Token"""
    # 首先檢查環境變量
    api_token = os.environ.get('QAI_HUB_TOKEN')
    
    if api_token:
        print("ℹ️ 從環境變量中獲取 API Token")
        return api_token
    
    # 其次檢查預定義文件
    token_file_paths = [
        os.path.join(os.getcwd(), "qai_hub_token.txt"),
        os.path.join(os.getcwd(), ".qai_hub_token"),
        os.path.join(get_home_directory(), "qai_hub_token.txt"),
        os.path.join(get_home_directory(), ".qai_hub_token")
    ]
    
    for path in token_file_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    api_token = f.read().strip()
                    if api_token:
                        print(f"ℹ️ 從文件讀取 API Token: {path}")
                        return api_token
            except:
                pass
    
    # 最後，從用戶輸入獲取
    print("\n獲取 QAI Hub API Token:")
    print("1. 前往 https://aihub.qualcomm.com/")
    print("2. 登錄您的賬戶")
    print("3. 在用戶設置中找到 API Token")
    print("4. 複製 API Token 並粘貼到下方")
    
    api_token = getpass.getpass("請輸入您的 QAI Hub API Token: ").strip()
    
    if not api_token:
        print("❌ 未提供 API Token")
        return None
    
    # 詢問是否保存到文件
    save_response = input("是否將 API Token 保存到本地文件？(y/n): ").lower()
    if save_response == 'y':
        save_path = os.path.join(get_home_directory(), ".qai_hub_token")
        try:
            with open(save_path, 'w') as f:
                f.write(api_token)
            os.chmod(save_path, 0o600)  # 設置只有用戶可讀寫的權限
            print(f"✅ API Token 已保存到: {save_path}")
        except Exception as e:
            print(f"⚠️ 無法保存 API Token: {e}")
    
    return api_token

def create_client_config(config_dir, api_token):
    """創建 QAI Hub 客戶端配置文件"""
    if not api_token:
        print("❌ 未提供 API Token，無法創建配置文件")
        return False
    
    config_path = os.path.join(config_dir, "client.ini")
    
    # 檢查是否覆蓋現有配置
    if not check_existing_config(config_path):
        print("ℹ️ 保留現有配置文件")
        return True
    
    # 創建新配置
    config = configparser.ConfigParser()
    config['api'] = {
        'api_token': api_token,
        'api_url': 'https://app.aihub.qualcomm.com/',
        'web_url': 'https://app.aihub.qualcomm.com/',
        'verbose': 'true'
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

def test_qai_hub_connection():
    """測試 QAI Hub 連接"""
    try:
        from qai_hub.client import Client, ClientConfig
        
        print("\n測試 QAI Hub 連接...")
        
        # 從配置文件讀取 API Token
        config_path = os.path.join(get_home_directory(), ".qai_hub", "client.ini")
        if not os.path.exists(config_path):
            print(f"❌ 配置文件不存在: {config_path}")
            return False
        
        try:
            config_parser = configparser.ConfigParser()
            config_parser.read(config_path)
            
            if 'api' not in config_parser or 'api_token' not in config_parser['api']:
                print(f"❌ 配置文件缺少必要字段")
                return False
                
            api_token = config_parser['api']['api_token']
            api_url = config_parser['api']['api_url']
            web_url = config_parser['api']['web_url']
        except Exception as e:
            print(f"❌ 無法讀取配置文件: {e}")
            return False
        
        # 直接創建配置對象
        config = ClientConfig(
            api_url=api_url,
            web_url=web_url,
            api_token=api_token,
            verbose=True
        )
        
        client = Client(config)
        
        # 獲取可用設備
        devices = client.get_devices()
        print(f"✅ 成功連接 QAI Hub! 發現 {len(devices)} 個可用設備。")
        
        # 獲取預訓練模型
        models = client.get_models(limit=5)
        print(f"✅ 可訪問 {len(models)} 個預訓練模型。")
        
        return True
    except ImportError:
        print("❌ 未安裝 qai-hub 包，請先安裝: pip install qai-hub")
        return False
    except Exception as e:
        print(f"❌ QAI Hub 連接測試失敗: {e}")
        print("請檢查您的 API Token 是否正確，以及網絡連接是否正常。")
        return False

def main():
    """主函數"""
    print("🚀 QAI Hub 設置助手")
    print("=" * 50)
    
    # 獲取 QAI Hub 配置目錄
    config_dir = create_qai_hub_config_directory()
    
    # 獲取 API Token
    api_token = get_api_token()
    
    # 創建配置文件
    if create_client_config(config_dir, api_token):
        # 測試連接
        if test_qai_hub_connection():
            print("\n✅ QAI Hub 設置完成！您現在可以使用 QAI Hub 功能。")
        else:
            print("\n⚠️ QAI Hub 設置可能不完整。請檢查配置和網絡連接。")
    else:
        print("\n❌ QAI Hub 設置失敗。")

if __name__ == "__main__":
    main()
