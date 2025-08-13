# QDC (Qualcomm Device Cloud) 安裝包準備指南

此文檔說明如何準備一個包含 Git 和 Python 的安裝包，用於在 QDC 創建 session 時上傳。

## 概述

Qualcomm Device Cloud (QDC) 允許您在創建 session 時上傳 .zip 文件。此文件會在 session 開始前解壓到 `C:\Temp\file\` 目錄中。您可以利用這個功能預先上傳必要的安裝檔案和自動化腳本，使 session 啟動後立即具備所需的開發環境。

## 安裝包內容

準備的安裝包包含：

1. **Git 安裝程序**: 離線安裝 Git 的執行檔
2. **Python 安裝程序**: 離線安裝 Python 的執行檔
3. **PowerShell 安裝腳本**: 自動執行安裝、配置環境的腳本
4. **自動運行批處理檔**: 用於啟動 PowerShell 腳本
5. **說明文件**: 說明如何使用安裝包

## 準備安裝包

我提供了一個腳本 `prepare_qdc_package.sh` 來自動下載所需安裝檔案並創建完整的安裝包：

```bash
# 給予腳本執行權限
chmod +x prepare_qdc_package.sh

# 運行腳本
./prepare_qdc_package.sh
```

運行後，腳本會：
1. 下載 Git 和 Python 的安裝檔
2. 創建必要的 PowerShell 安裝腳本
3. 打包所有文件為 `qdc_installer.zip`

## 在 QDC 創建 session 時使用

在 QDC 創建 session 時：

1. 在 "Job Details" 部分找到 "Package Upload" 選項
2. 選擇 "Upload Type" 為 "Application"
3. 上傳生成的 `qdc_installer.zip` 文件
4. 提交 session 創建請求

當 session 啟動後，文件會被解壓到 `C:\Temp\file\` 目錄。用戶可以：

1. 打開 Windows 檔案管理器，導航到 `C:\Temp\file\package\`
2. 雙擊執行 `RunMe.bat` 啟動自動安裝
3. 等待安裝過程完成

## 安裝腳本功能

PowerShell 安裝腳本 `install.ps1` 會自動：

1. 安裝 Git 和 Python
2. 驗證安裝結果
3. 克隆 Dragon-X-Fall-Detection 專案
4. 安裝必要的 Python 套件
5. 配置 QAI Hub 設定
6. 創建桌面捷徑方便啟動系統
7. 生成詳細的安裝日誌

## 手動安裝方式

如果自動安裝腳本無法正常運行，用戶可以手動：

1. 在 `C:\Temp\file\package\` 目錄中找到安裝檔
2. 依次運行 Git 和 Python 的安裝程序
3. 打開 PowerShell 並運行安裝腳本：
   ```powershell
   cd C:\Temp\file\package\scripts
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

## 運行系統

安裝完成後，可以通過：

1. 點擊創建的桌面捷徑
2. 或者在命令提示符中運行：
   ```cmd
   cd C:\dragon-x-fall-detection
   python dragon_x_fall_detection_system.py
   ```
