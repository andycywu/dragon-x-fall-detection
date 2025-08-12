#!/usr/bin/env python3
"""
🔧 QAI Hub API 令牌設定工具
為 Windows 和 Linux 環境設定 QAI Hub API 令牌
"""

import os
import sys
from pathlib import Path

def setup_qai_hub_token():
    """設定 QAI Hub API 令牌"""
    print("🔧 設定 QAI Hub API 令牌...")
    
    # API 令牌
    api_token = "h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2"
    
    # 創建 .qai_hub 目錄
    home_dir = Path.home()
    qai_config_dir = home_dir / ".qai_hub"
    qai_config_dir.mkdir(exist_ok=True)
    print(f"✅ 創建配置目錄: {qai_config_dir}")
    
    # 創建配置文件
    config_file = qai_config_dir / "client.ini"
    config_content = f"""[default]
api_token = {api_token}
api_url = https://app.aihub.qualcomm.com
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"✅ 配置文件已創建: {config_file}")
    
    # 設置環境變量
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    print("✅ 環境變量已設置")
    
    # 驗證設置
    if config_file.exists():
        print("✅ 驗證成功: API 令牌已設定")
    else:
        print("❌ 驗證失敗: 配置文件創建失敗")
    
    return True

def main():
    """主函數"""
    print("=" * 50)
    print("🔧 QAI Hub API 令牌設定工具")
    print("=" * 50)
    
    # 檢測操作系統
    import platform
    system_name = platform.system()
    print(f"🖥️ 檢測到操作系統: {system_name}")
    
    # 設定 API 令牌
    success = setup_qai_hub_token()
    
    # 顯示結果
    print("\n" + "=" * 50)
    if success:
        print("🎉 QAI Hub API 令牌設定成功！")
    else:
        print("❌ QAI Hub API 令牌設定失敗！")
    print("=" * 50)
    
    print("\n📋 後續步驟:")
    print("1. 運行 unified_ai_detector.py 測試 QAI Hub 集成")
    print("2. 運行 fixed_final_demo.py 測試跌倒檢測功能")
    print("3. 查看 windows_guide.md 獲取更多使用說明")

if __name__ == "__main__":
    main()
