#!/usr/bin/env python3
"""
QAI Hub雲端設置指南
"""

def print_setup_instructions():
    """打印QAI Hub設置說明"""
    
    print("""
🌐 Qualcomm AI Hub 雲端設置指南
==============================================

📋 為什麼需要QAI Hub雲端？
- 獲得官方的profiling數據
- 在真正的Qualcomm硬體上測試
- 獲得準確的效能指標
- 符合黑客松提交要求

🔧 設置步驟：

1️⃣ 註冊QAI Hub帳戶
   訪問: https://aihub.qualcomm.com
   點擊 "Sign Up" 註冊新帳戶

2️⃣ 獲取API Token
   登入後訪問: https://aihub.qualcomm.com/profile
   複製您的API Token

3️⃣ 設置環境變數
   在終端執行:
   export QAI_HUB_API_TOKEN='your_api_token_here'

4️⃣ 安裝必要套件
   pip install qai-hub

5️⃣ 運行雲端測試
   python setup_qai_hub_cloud.py

📊 您將獲得的官方數據：
- 在Samsung Galaxy S23上的實際推理時間
- 真實的記憶體使用量
- CPU/GPU使用率
- 能耗數據
- Qualcomm硬體加速效益分析

⚠️ 注意事項：
- QAI Hub可能需要等待隊列
- 某些功能需要付費帳戶
- 建議在黑客松前提前設置

🎯 完成後您將擁有：
✅ 官方的Qualcomm profiling報告
✅ 真實硬體的效能數據  
✅ 符合黑客松要求的技術文檔
✅ 可信的benchmark結果

需要幫助嗎？
訪問: https://aihub.qualcomm.com/docs
""")

if __name__ == "__main__":
    print_setup_instructions()
