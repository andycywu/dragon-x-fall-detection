# QAI Hub 連接故障排除指南

## QAI Hub 連接失敗問題

如果您在執行 `unified_ai_detector.py` 時看到以下錯誤：

```
ERROR:__main__:❌ QAI Hub初始化失敗: Failed to load client configuration file.

┌────────────────────────────────────────────────────────────────────┐
| ~/.qai_hub/client.ini not found. Please request access at          |
| https://aihub.qualcomm.com/. If you have access, please refer to   |
| https://app.aihub.qualcomm.com/docs for instructions on            |
| configuring the API key.                                           |
└────────────────────────────────────────────────────────────────────┘
```

這表示系統找不到 QAI Hub 的客戶端設定檔案 `~/.qai_hub/client.ini`。

## 解決方法

### 1. 使用我們的設置工具

我們提供了一個專用工具來設置 QAI Hub 認證：

```bash
# Windows
python setup_qai_hub.py

# Linux/macOS
python3 setup_qai_hub.py
```

如果您有 API 令牌，工具會提示您輸入。如果沒有，請參考步驟 2。

### 2. 獲取 QAI Hub API 令牌

如果您沒有 QAI Hub API 令牌：

1. 訪問 [Qualcomm AI Hub](https://aihub.qualcomm.com/)
2. 點擊 "Request Access" 或註冊/登錄
3. 按照指示獲取 API 令牌
4. 獲取令牌後，運行我們的設置工具：

```bash
python setup_qai_hub.py --token YOUR_API_TOKEN
```

### 3. 手動設置

如果自動工具不起作用，您可以手動設置：

1. 創建目錄：
   ```bash
   # Windows
   mkdir %USERPROFILE%\.qai_hub
   
   # Linux/macOS
   mkdir -p ~/.qai_hub
   ```

2. 創建配置文件：
   ```bash
   # Windows - 使用記事本
   notepad %USERPROFILE%\.qai_hub\client.ini
   
   # Linux/macOS
   nano ~/.qai_hub/client.ini
   ```

3. 添加以下內容（替換 YOUR_API_KEY）：
   ```ini
   [DEFAULT]
   api_key = YOUR_API_KEY
   ```

4. 保存文件

### 4. 測試連接

設置完成後，您可以測試連接：

```bash
# Windows
python test_qai_hub_connection.py

# Linux/macOS
python3 test_qai_hub_connection.py
```

如果測試成功，您應該能夠看到可用的 QAI Hub 設備和模型列表。

### 5. 環境變量

您也可以通過設置環境變量來提供 API 令牌：

```bash
# Windows
set QAI_HUB_API_TOKEN=YOUR_API_TOKEN

# Linux/macOS
export QAI_HUB_API_TOKEN=YOUR_API_TOKEN
```

## 常見問題

### Q: 我已經設置了令牌，但仍然收到錯誤

確保：
- 令牌格式正確（沒有多餘的空格或引號）
- 配置文件位於正確的位置
- 您有正確的網絡連接
- 您的令牌未過期或被撤銷

### Q: 我沒有 QAI Hub 訪問權限

您需要在 [Qualcomm AI Hub](https://aihub.qualcomm.com/) 請求訪問權限。如果您正在參加 Qualcomm 黑客松或其他活動，請聯繫組織者獲取臨時令牌。

### Q: 我可以在沒有 QAI Hub 的情況下運行系統嗎？

是的，系統會自動回退到 MediaPipe 和 ONNX Runtime CPU 後端。但是，您將無法使用 Qualcomm 加速器和預訓練模型。
