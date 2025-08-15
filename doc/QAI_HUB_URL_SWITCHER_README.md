# QAI Hub URL 切換工具

此工具可以自動測試 QAI Hub 的新舊 API URL，並使用能夠正常工作的那個。

## 問題背景

QAI Hub 的 API URL 已從 `api.qai-hub.qualcomm.com` 更新為 `api.aihub.qualcomm.com`。根據您的 QAI Hub SDK 版本，您可能需要使用特定的 URL 才能正常連接。

## 解決方案

我們提供了兩個簡單的批次檔：

- `qai_hub_url_switcher.bat` - 自動測試並選擇工作的 URL
- `qai_hub_fixer.bat` - 提供完整的互動式修復選項

這些工具可以：

1. 測試新的 API URL (`api.aihub.qualcomm.com`)
2. 如果新 URL 不工作，測試舊的 API URL (`api.qai-hub.qualcomm.com`)
3. 使用能夠正常工作的 URL 設定您的配置
4. 運行測試以確認配置是否有效
5. 檢查 Windows 長路徑支持
6. 提供自訂 API 令牌的選項

## 使用方法

### 簡易模式：

1. 雙擊運行 `qai_hub_url_switcher.bat`
2. 工具會自動測試兩個 URL 並設定能夠工作的那個
3. 最後會顯示測試結果和後續步驟建議

### 互動式修復模式：

1. 雙擊運行 `qai_hub_fixer.bat`
2. 跟隨提示進行操作：
   - 檢查現有配置
   - 檢查 QAI Hub 安裝
   - 輸入您的 API 令牌或使用預設值
   - 選擇 API URL 或自動測試
   - 檢查 Windows 長路徑支持
   - 驗證配置是否正常工作

## 手動設定方法

如果批次檔無法解決問題，您可以手動編輯配置檔：

1. 找到您的 QAI Hub 配置檔：`C:\Users\您的用戶名\.qai_hub\client.ini`
2. 使用記事本打開並編輯以下內容：

使用新 URL：

```ini
[default]
api_token=您的API令牌
api_key=您的API令牌
base_api_url=https://api.aihub.qualcomm.com
web_url=https://app.aihub.qualcomm.com
```

使用舊 URL：

```ini
[default]
api_token=您的API令牌
api_key=您的API令牌
base_api_url=https://api.qai-hub.qualcomm.com
web_url=https://app.aihub.qualcomm.com
```

## QAI Hub 版本相容性

- 較新版本的 QAI Hub SDK (0.34.0+) 通常使用新 URL (`api.aihub.qualcomm.com`)
- 較舊版本的 QAI Hub SDK 可能需要使用舊 URL (`api.qai-hub.qualcomm.com`)

如果您需要指定特定版本，可以使用以下命令：

```bash
pip install qai-hub==0.31.0 qai-hub-models==0.31.0
```

## 常見問題排解

1. **網路連接問題**：確保您能夠訪問 Qualcomm 的伺服器
2. **防火牆設置**：檢查防火牆是否阻擋了 QAI Hub 的連接
3. **無法安裝**：如果遇到"ERROR: Could not install packages due to an OSError"，您可能需要啟用 Windows 長路徑支持
4. **路徑太長錯誤**：修改 Windows 註冊表啟用長路徑支持

```reg
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem]
"LongPathsEnabled"=dword:00000001
```

5. **編碼問題**：如果批次檔顯示亂碼，請嘗試在 cmd 視窗中使用 `chcp 65001` 命令切換到 UTF-8 編碼

## 更多幫助

如果您仍然遇到問題，請參閱 QAI Hub 文檔或聯繫技術支持。
