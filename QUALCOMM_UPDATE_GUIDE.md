# Qualcomm Snapdragon X Elite Windows 11 裝置上的程式碼更新指南

本文檔提供在 Qualcomm Snapdragon X Elite Windows 11 裝置上更新最新程式碼的步驟。

## 前提條件

- 確保您的 Snapdragon X Elite 裝置已連接到互聯網
- 確保您已在 Windows 11 裝置上安裝了 Git ([下載鏈接](https://git-scm.com/download/win))
- 確保您有權限訪問 GitHub 上的存儲庫

## 更新步驟

### 方法 1：使用提供的腳本（推薦）

我們提供了幾個腳本來簡化更新過程，根據您的偏好選擇其中一個：

#### 使用批處理文件 (.bat)

1. 在文件資源管理器中找到您的存儲庫文件夾
2. 雙擊 `qualcomm_pull_latest.bat` 文件
3. 等待腳本完成，它會自動拉取最新的更改

#### 使用 PowerShell 腳本 (.ps1)

1. 右鍵點擊 Windows 開始菜單，選擇 "Windows PowerShell" 或 "Windows Terminal"
2. 導航到存儲庫目錄：

   ```powershell
   cd C:\path\to\dragon-x-fall-detection
   ```

3. 運行 PowerShell 腳本：

   ```powershell
   .\qualcomm_pull_latest.ps1
   ```

4. 如果遇到執行策略問題，可能需要先運行：

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

### 方法 2：手動更新

如果您更喜歡手動更新：

1. 右鍵點擊 Windows 開始菜單，選擇 "Windows PowerShell" 或 "Windows Terminal"
2. 導航到存儲庫目錄：

   ```powershell
   cd C:\path\to\dragon-x-fall-detection
   ```

3. 檢查本地更改：

   ```powershell
   git status
   ```

4. 如果有本地更改，可以選擇保存它們：

   ```powershell
   git stash
   ```

5. 拉取最新的程式碼：

   ```powershell
   git pull origin main
   ```

6. 如果之前有保存的更改，現在可以恢復：

   ```powershell
   git stash pop
   ```

### 疑難排解

如果您在更新過程中遇到問題：

- **網絡連接問題**：確保您的裝置已連接到互聯網，且可以訪問 GitHub
- **權限問題**：確認您有正確的 GitHub 憑證，或使用 SSH 密鑰進行身份驗證
- **合併衝突**：如果出現合併衝突，您可能需要手動解決這些衝突
- **執行策略限制**：如果 PowerShell 腳本無法執行，可能需要調整執行策略

### Snapdragon X Elite 優化說明

對於 Snapdragon X Elite 平台上的 Windows 11，本專案已包含針對 ARM64 架構的特定優化：

- 用到了 ARM64 原生的依賴包，提升效能和降低功耗
- 最佳化了啟動時間和模型載入速度
- 優化了針對 Snapdragon X Elite NPU 的 AI 模型處理

請參考 `ARM64_OPTIMIZATION_GUIDE.md` 和 `SNAPDRAGON_ARM64_OPTIMIZATION.md` 文件，以獲取更多關於 Snapdragon 平台的優化詳情。

如需任何協助，請聯繫開發團隊。

## 疑難排解

如果您在更新過程中遇到問題：

- **網絡連接問題**：確保您的裝置已連接到互聯網，且可以訪問 GitHub
- **權限問題**：確認您有正確的 GitHub 憑證，或使用 SSH 密鑰進行身份驗證
- **合併衝突**：如果出現合併衝突，您可能需要手動解決這些衝突

## 附加說明

對於特定的 Qualcomm 平台優化，請參考 `ARM64_OPTIMIZATION_GUIDE.md` 文件，其中包含針對 Qualcomm 處理器的特定優化指南。

如需任何協助，請聯繫開發團隊。
