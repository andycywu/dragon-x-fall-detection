# QAI Hub 連接問題排解指南 - macOS 版本

## 問題摘要

在 macOS 上，`QAI Hub` 連接問題通常與以下幾個方面有關：

1. **配置文件格式不正確** - `client.ini` 文件格式需要特別注意
2. **網絡連接問題** - 無法連接到 Qualcomm 的 API 服務器
3. **API 令牌認證失敗** - 令牌無效或格式不正確
4. **相依性衝突** - 例如 `protobuf` 版本不兼容

## 修復步驟

### 1. 執行全面修復腳本

我們已經創建了一個專門針對 macOS 的修復腳本，它會嘗試多種方法修復問題：

```bash
# 給腳本添加執行權限
chmod +x fix_qai_hub_macos.sh

# 執行腳本
./fix_qai_hub_macos.sh
```

### 2. 配置文件格式問題

QAI Hub 的配置文件格式需要非常精確。以下是正確的格式：

```ini
[default]
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
base_api_url = https://api.qai-hub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
```

如果修復腳本無法解決問題，請手動編輯配置文件：

```bash
# 打開配置文件
nano ~/.qai_hub/client.ini
```

### 3. 網絡連接問題

如果您遇到網絡連接問題，可以嘗試以下步驟：

```bash
# 測試連接到 API 服務器
ping -c 3 api.qai-hub.qualcomm.com

# 或使用我們的診斷工具
python test_qai_hub_api.py
```

如果您無法連接，請檢查：

- 網絡連接是否正常
- 防火牆設置
- DNS 設置
- 是否在使用公司/學校網絡（可能有限制）

### 4. 相依性問題

QAI Hub 需要特定版本的 `protobuf`：

```bash
# 安裝正確版本的 protobuf
pip install protobuf==4.25.3

# 重新安裝 QAI Hub
pip install qai-hub==0.31.0 qai-hub-models==0.33.1
```

### 5. 環境變數設置

確保環境變數正確設置：

```bash
# 設置環境變數
export QAI_HUB_API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
export QAI_API_KEY=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d

# 檢查環境變數
echo $QAI_HUB_API_TOKEN
```

## 診斷工具

我們提供了多個診斷工具來幫助您排查問題：

1. **基本配置修復**：

   ```bash
   python fix_client_ini_macos.py
   ```

2. **API 連接測試**：

   ```bash
   python test_qai_hub_api.py
   ```

3. **QAI Hub 狀態檢查**：

   ```bash
   python check_qai_hub_status.py
   ```

## 如果所有方法都失敗

如果您嘗試了所有方法但仍然無法連接到 QAI Hub API，我們提供了一個離線演示模式：

```bash
python qai_hub_demo_offline.py
```

這將模擬 QAI Hub 的功能，讓您仍然可以展示系統的主要功能。

## 常見錯誤訊息解析

1. **Failed to load configuration file**
   - 原因：找不到配置文件或格式不正確
   - 解決方案：運行 `fix_client_ini_macos.py`

2. **API key validation failed**
   - 原因：API 令牌無效或過期
   - 解決方案：確認使用正確的 API 令牌

3. **Connection refused**
   - 原因：網絡連接問題
   - 解決方案：檢查網絡設置和防火牆

4. **No module named 'qai_hub'**
   - 原因：QAI Hub SDK 未安裝
   - 解決方案：`pip install qai-hub==0.31.0`

## 聯絡支持

如果您仍然遇到問題，請嘗試以下資源：

- 訪問 [QAI Hub 文檔](https://app.aihub.qualcomm.com/docs)
- 聯絡 Qualcomm AI Hub 支持團隊

---

希望這份指南能幫助您解決 QAI Hub 的連接問題。如有任何疑問，請隨時聯絡我們。
