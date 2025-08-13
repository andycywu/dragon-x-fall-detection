# QAI Hub 修復與設置工具

根據最新的官方信息，QAI Hub 的正確設定非常關鍵。本專案提供了多個工具來協助您正確設置 QAI Hub 配置。

## 重要更新

**重要通知:** 唯一正確的 QAI Hub URL 是 `https://app.aihub.qualcomm.com`。

## 工具說明

我們提供了以下工具來幫助您正確設置 QAI Hub：

### Windows 用戶工具

1. **`qai_hub_fix.bat`** - 最新的簡易修復工具
   - 自動設置正確的 API URL
   - 檢查 Python 環境
   - 檢查 QAI Hub 安裝狀態
   - 檢查 Windows 長路徑支持
   - 驗證配置是否正確

2. **`qai_hub_url_switcher.bat`** - API URL 設定工具
   - 設置正確的 URL
   - 提供配置驗證

3. **`qai_hub_fixer_zh.bat`** - 完整中文版修復工具
   - 中文介面，適合中文用戶
   - 完整的互動式設置流程
   - 支持自定義 API 令牌

4. **`simple_fix_qai_hub_zh.bat`** - 簡易中文版修復工具
   - 中文介面，適合中文用戶
   - 簡單快速的配置修復
   - 自動設置 API URL 和令牌

### macOS/Linux 用戶工具

1. **`qai_hub_fix.py`** - 跨平台 Python 修復工具
   - 支持自定義 API 令牌
   - 設置正確的 API URL
   - 檢查並安裝 QAI Hub
   - 驗證配置是否正確

## 使用說明

### Windows 用戶

1. 雙擊運行 `qai_hub_fix.bat`
2. 按照提示進行操作
3. 如遇到問題，參考 `QAI_HUB_TROUBLESHOOTING.md`

### macOS/Linux 用戶

```bash
# 設置執行權限
chmod +x qai_hub_fix.py

# 運行修復工具
./qai_hub_fix.py
```

## QAI Hub 配置文件格式

正確的配置文件格式如下：

```ini
[default]
api_token = YOUR_API_TOKEN
api_key = YOUR_API_TOKEN
base_api_url = https://app.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
```

## 常見問題解決

詳細的問題排解指南，請參考 `QAI_HUB_TROUBLESHOOTING.md`。

## 推薦安裝版本

為了確保最佳兼容性，建議安裝以下版本：

```bash
pip install qai-hub==0.31.0 qai-hub-models==0.31.0
```
