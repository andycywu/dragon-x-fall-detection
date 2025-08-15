# Snapdragon X Elite 強制 Git Pull 指南

如果您想在 Snapdragon X Elite Windows 11 裝置上強制拉取最新代碼並覆蓋所有本地更改，可以使用以下方法：

## 方法 1：使用提供的腳本（推薦）

我們提供了兩個腳本供您選擇：

1. **批處理腳本**：雙擊 `git_pull_overwrite.bat` 文件
2. **PowerShell 腳本**：右鍵點擊 `git_pull_overwrite.ps1` 並選擇「使用 PowerShell 運行」

這兩個腳本都會詢問確認，然後執行強制拉取操作。

> **注意**：如果您在命令提示符中看到中文顯示為亂碼，我們已經在最新版本的腳本中添加了 Unicode 支援。請確保您使用的是最新版本的腳本。

## 方法 2：直接執行命令

如果您想直接在命令行中執行，請按照以下步驟操作：

### 在命令提示符 (CMD) 中：

```cmd
cd C:\path\to\dragon-x-fall-detection
git reset --hard
git clean -fd
git pull origin main
```

### 在 PowerShell 中：

```powershell
cd C:\path\to\dragon-x-fall-detection
git reset --hard
git clean -fd
git pull origin main
```

## 警告

**請注意**：上述所有方法都會：
1. 丟失所有未提交的更改
2. 刪除所有未被 Git 跟踪的文件
3. 用遠程倉庫的內容完全覆蓋本地文件

如果您有任何重要的本地更改或文件，請先備份它們！
