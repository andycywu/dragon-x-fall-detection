#!/usr/bin/env python3
"""
QAI Hub 連接測試工具
測試 QAI Hub 連接並顯示可用設備
"""

import os
import sys
import json
from pathlib import Path

def test_qai_hub_connection():
    """測試 QAI Hub 連接"""
    print("=== QAI Hub 連接測試 ===")
    
    # 顯示配置路徑
    config_path = Path.home() / ".qai_hub" / "client.ini"
    print(f"配置文件路徑: {config_path}")
    print(f"配置文件存在: {'是' if config_path.exists() else '否'}")
    
    # 檢查環境變量
    api_token = os.environ.get('QAI_HUB_API_TOKEN')
    print(f"環境變量設置: {'是' if api_token else '否'}")
    
    # 嘗試導入 QAI Hub
    try:
        import qai_hub as hub
        print("QAI Hub 模塊導入成功")
        
        # 顯示版本
        print(f"QAI Hub 版本: {hub.__version__}")
        
        # 嘗試獲取設備列表
        try:
            print("\n獲取設備列表...")
            devices = hub.get_devices()
            print(f"成功獲取設備列表")
            print(f"可用設備數量: {len(devices)}")
            
            if devices:
                print("\n可用設備:")
                for i, device in enumerate(devices):
                    print(f"{i+1}. {device.name}")
                    print(f"   - 類型: {device.device_type}")
                    print(f"   - ID: {device.id}")
            else:
                print("沒有可用設備")
                
            # 獲取模型列表
            try:
                print("\n獲取模型列表...")
                models = hub.get_models()
                print(f"可用模型數量: {len(models)}")
                
                if models and len(models) > 0:
                    print("\n可用模型範例 (最多顯示 5 個):")
                    for i, model in enumerate(models[:5]):
                        print(f"{i+1}. {model.name}")
                        print(f"   - ID: {model.id}")
                        print(f"   - 描述: {model.description[:50]}..." if model.description and len(model.description) > 50 else f"   - 描述: {model.description}")
            except Exception as e:
                print(f"獲取模型列表失敗: {e}")
            
            print("\n=== QAI Hub 連接測試成功 ===")
            return True
            
        except Exception as e:
            print(f"獲取設備列表失敗: {e}")
            print("\n以下是故障排除步驟:")
            print("1. 確認您的 API 令牌是否有效")
            print("2. 檢查網絡連接")
            print("3. 嘗試重新設置 API 令牌: python setup_qai_hub.py")
            return False
            
    except ImportError:
        print("QAI Hub 模塊導入失敗")
        print("請安裝 QAI Hub: pip install qai-hub")
        return False
    except Exception as e:
        print(f"QAI Hub 初始化失敗: {e}")
        return False

if __name__ == "__main__":
    success = test_qai_hub_connection()
    
    if not success:
        print("\n=== QAI Hub 連接測試失敗 ===")
        sys.exit(1)
    else:
        sys.exit(0)
