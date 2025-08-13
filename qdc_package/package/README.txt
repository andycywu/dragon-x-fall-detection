Dragon X Fall Detection System - QDC 安裝包 (修正版)
==========================================

此安裝包包含：
1. Git 安裝程序
2. Python 3.10 安裝程序
3. 自動安裝腳本

安裝說明：
1. 雙擊運行 "RunMe.bat"
2. 等待安裝完成
3. 重啟電腦（重要！）
4. 安裝完成後，打開命令提示符運行系統

手動安裝方式（如自動安裝失敗）：
1. 雙擊運行 Git-2.40.0-64-bit.exe 安裝 Git
2. 雙擊運行 python-3.10.11-amd64.exe 安裝 Python
3. 重啟電腦
4. 開啟命令提示符，執行：
   cd C:\
   git clone https://github.com/andycywu/dragon-x-fall-detection.git
   cd dragon-x-fall-detection
   pip install numpy opencv-python onnxruntime
   pip install -r requirements.txt
   pip install -U qai-hub qai-hub-models "protobuf==4.25.3"
   python dragon_x_fall_detection_system.py

故障排除：
1. 如果安裝過程中出現錯誤，請查看 scripts 資料夾中的日誌文件
2. 確保安裝過程中有管理員權限
3. 安裝後必須重啟電腦，確保環境變數生效

Dragon X Team
==========================================
