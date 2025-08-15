#!/usr/bin/env python3
"""
QAI Hub API 配置助手
幫助用戶設置 Qualcomm AI Hub API Token
"""

import os
import re
from pathlib import Path
from config_manager import ConfigManager

class QAIHubConfigHelper:
    """QAI Hub配置助手"""
    
    def __init__(self):
        """初始化配置助手"""
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        
    def display_welcome(self):
        """顯示歡迎信息"""
        print("🏆 Qualcomm AI Hub API 配置助手")
        print("=" * 50)
        print("此工具將幫助您配置 QAI Hub API Token")
        print("用於黑客松跌倒檢測系統的硬件加速功能")
        print()
        
    def check_current_config(self):
        """檢查當前配置"""
        config = ConfigManager()
        
        print("📊 當前配置狀態:")
        print("-" * 30)
        
        token = config.get_qai_hub_token()
        if token and token != "your_api_token_here":
            print(f"✅ API Token: 已配置 ({token[:10]}...)")
            return True
        else:
            print("❌ API Token: 未配置")
            return False
            
    def validate_token_format(self, token: str) -> bool:
        """驗證Token格式"""
        # QAI Hub Token 通常以 qai_hub_ 開頭
        if not token.strip():
            return False
            
        # 基本長度檢查
        if len(token.strip()) < 20:
            return False
            
        # 檢查是否是默認值
        if token.strip() == "your_api_token_here":
            return False
            
        return True
        
    def set_api_token(self):
        """設置API Token"""
        print("\n🔧 設置 QAI Hub API Token")
        print("-" * 30)
        print("請按照以下步驟獲取 API Token:")
        print("1. 訪問: https://aihub.qualcomm.com/")
        print("2. 註冊並登入帳戶")
        print("3. 申請開發者權限")
        print("4. 在 Console 中生成 API Token")
        print()
        
        while True:
            token = input("請輸入您的 API Token (或輸入 'skip' 跳過): ").strip()
            
            if token.lower() == 'skip':
                print("⏭️  跳過 API Token 配置")
                print("系統將使用 CPU 模式運行，所有功能仍然可用")
                return False
                
            if self.validate_token_format(token):
                break
            else:
                print("❌ Token 格式無效，請重新輸入")
                print("   Token 應該是較長的字符串，通常以 qai_hub_ 開頭")
                
        # 更新 .env 文件
        self.update_env_file(token)
        print(f"✅ API Token 已設置: {token[:10]}...")
        return True
        
    def update_env_file(self, token: str):
        """更新 .env 文件"""
        if not self.env_file.exists():
            print("❌ .env 文件不存在")
            return
            
        # 讀取現有內容
        with open(self.env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 替換 Token
        pattern = r'QAI_HUB_API_TOKEN=.*'
        replacement = f'QAI_HUB_API_TOKEN={token}'
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
        else:
            new_content = content + f'\nQAI_HUB_API_TOKEN={token}\n'
            
        # 寫回文件
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    def test_configuration(self):
        """測試配置"""
        print("\n🧪 測試配置...")
        print("-" * 30)
        
        try:
            # 重新加載配置
            config = ConfigManager()
            config.display_config_status()
            
            # 測試 QAI Hub 連接
            print("\n🔌 測試 QAI Hub 連接...")
            from qai_hub_integration import QAIHubOptimizer
            optimizer = QAIHubOptimizer()
            
            if optimizer.qai_available:
                print("✅ QAI Hub 模塊加載成功")
                
                # 測試性能
                import numpy as np
                test_data = np.random.rand(224, 224, 3).astype(np.float32)
                result = optimizer.accelerate_inference(test_data)
                
                if result['accelerated']:
                    print("✅ 硬件加速測試成功")
                    print(f"   推理時間: {result['inference_time']:.4f}s")
                else:
                    print("⚠️  使用 CPU 模式運行")
            else:
                print("⚠️  QAI Hub 不可用，使用 CPU 模式")
                
        except Exception as e:
            print(f"❌ 測試過程中出錯: {e}")
            
    def show_usage_guide(self):
        """顯示使用指南"""
        print("\n📖 使用指南")
        print("=" * 50)
        print("配置完成後，您可以使用以下命令:")
        print()
        print("🚀 啟動完整系統:")
        print("   python hackathon_launcher.py")
        print()
        print("🎪 啟動 Web 演示:")
        print("   streamlit run hackathon_demo.py")
        print()
        print("🎯 啟動實時檢測:")
        print("   python hackathon_main.py")
        print()
        print("🔧 重新配置:")
        print("   python qai_setup_helper.py")
        print()
        
    def run(self):
        """運行配置助手"""
        self.display_welcome()
        
        # 檢查當前配置
        has_token = self.check_current_config()
        
        if has_token:
            choice = input("\n🤔 API Token 已配置，是否重新設置? (y/N): ").strip().lower()
            if choice not in ['y', 'yes']:
                print("✅ 使用現有配置")
                self.test_configuration()
                self.show_usage_guide()
                return
                
        # 設置 API Token
        success = self.set_api_token()
        
        if success:
            # 測試配置
            self.test_configuration()
            
        # 顯示使用指南
        self.show_usage_guide()
        
        print("\n🎉 配置完成！準備開始黑客松演示！")

def main():
    """主函數"""
    try:
        helper = QAIHubConfigHelper()
        helper.run()
    except KeyboardInterrupt:
        print("\n\n👋 配置已取消")
    except Exception as e:
        print(f"\n❌ 配置過程中出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
