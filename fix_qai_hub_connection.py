#!/usr/bin/env python3
"""
QAI Hub 連接修復工具
修復 QAI Hub 連接配置問題
"""

import os
import sys
import configparser
from pathlib import Path
import getpass

def get_api_token():
    """獲取 QAI Hub API Token"""
    # 首先檢查環境變量
    api_token = os.environ.get('QAI_HUB_TOKEN') or os.environ.get('QAI_HUB_API_TOKEN')
    
    if api_token:
        print("✅ 從環境變量獲取 API Token")
        return api_token
    
    # 使用 .env 文件中指定的 token
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('QAI_HUB_API_TOKEN='):
                        api_token = line.split('=', 1)[1].strip()
                        if api_token:
                            print(f"✅ 從 .env 文件讀取 API Token")
                            return api_token
        except Exception as e:
            print(f"⚠️ 讀取 .env 文件失敗: {e}")
    
    # 其次檢查預定義文件
    token_files = [
        Path.cwd() / "qai_hub_token.txt",
        Path.cwd() / ".qai_hub_token",
        Path.home() / "qai_hub_token.txt",
        Path.home() / ".qai_hub_token"
    ]
    
    for path in token_files:
        if path.exists():
            try:
                token = path.read_text().strip()
                if token:
                    print(f"✅ 從文件讀取 API Token: {path}")
                    return token
            except Exception as e:
                print(f"⚠️ 讀取文件失敗: {e}")
    
    # 最後從用戶輸入獲取
    print("\n獲取 QAI Hub API Token:")
    print("1. 前往 https://aihub.qualcomm.com/")
    print("2. 登錄您的帳戶")
    print("3. 在用戶設置中找到 API Token")
    print("4. 複製 API Token 並粘貼到下方")
    
    api_token = getpass.getpass("請輸入您的 QAI Hub API Token: ").strip()
    
    if not api_token:
        print("❌ 未提供 API Token")
        return None
    
    # 詢問是否保存到文件
    save_response = input("是否將 API Token 保存到本地文件？(y/n): ").lower()
    if save_response == 'y':
        save_path = Path.home() / ".qai_hub_token"
        try:
            save_path.write_text(api_token)
            os.chmod(save_path, 0o600)  # 設置只有用戶可讀寫的權限
            print(f"✅ API Token 已保存到: {save_path}")
        except Exception as e:
            print(f"⚠️ 無法保存 API Token: {e}")
    
    return api_token

def create_config_file(api_token):
    """創建 QAI Hub 配置文件"""
    if not api_token:
        print("❌ 未提供 API Token，無法創建配置文件")
        return False
    
    config_dir = Path.home() / ".qai_hub"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "client.ini"
    
    # 創建配置
    config = configparser.ConfigParser()
    config['api'] = {
        'api_token': api_token,
        'api_url': 'https://app.aihub.qualcomm.com/',
        'web_url': 'https://app.aihub.qualcomm.com/',
        'verbose': 'true'
    }
    
    # 寫入配置文件
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        os.chmod(config_file, 0o600)  # 設置只有用戶可讀寫的權限
        print(f"✅ 已創建 QAI Hub 配置文件: {config_file}")
        return True
    except Exception as e:
        print(f"❌ 創建配置文件失敗: {e}")
        return False

def test_connection():
    """測試 QAI Hub 連接"""
    print("\n測試 QAI Hub 連接...")
    
    try:
        import qai_hub
        
        print(f"✅ QAI Hub 版本: {qai_hub.__version__}")
        
        try:
            devices = qai_hub.get_devices()
            print(f"✅ 成功連接到 QAI Hub! 找到 {len(devices)} 個設備")
            
            if devices:
                print("\n可用設備:")
                for i, device in enumerate(devices[:3], 1):
                    print(f"  {i}. {device.name}")
                if len(devices) > 3:
                    print(f"  ... 以及其他 {len(devices) - 3} 個設備")
            
            return True
        except Exception as e:
            print(f"❌ 獲取設備列表失敗: {e}")
            return False
    except ImportError:
        print("❌ 未安裝 qai-hub 包，請先安裝: pip install qai-hub")
        return False
    except Exception as e:
        print(f"❌ QAI Hub 連接測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🔧 QAI Hub 連接修復工具")
    print("=" * 50)
    
    # 獲取 API Token
    api_token = get_api_token()
    
    if not api_token:
        print("\n❌ 未能獲取有效的 API Token，無法繼續")
        return
    
    # 創建配置文件
    if not create_config_file(api_token):
        print("\n❌ 配置文件創建失敗")
        return
    
    # 測試連接
    if test_connection():
        print("\n✅ QAI Hub 連接測試成功！")
        print("您現在可以使用 QAI Hub 功能。")
    else:
        print("\n❌ QAI Hub 連接測試失敗。")
        print("可能的原因:")
        print("1. API Token 無效或已過期")
        print("2. 網絡連接問題")
        print("3. QAI Hub 服務當前不可用")
        print("\n請確保您的 API Token 有效，並且網絡連接正常。")
        print("您可以訪問 https://aihub.qualcomm.com/ 獲取新的 API Token。")

if __name__ == "__main__":
    main()
