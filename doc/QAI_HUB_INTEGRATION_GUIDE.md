# Dragon X Fall Detection - QAI Hub 整合指南

## 1. 概述

本指南提供了 Dragon X Fall Detection 系統與 QAI Hub 整合的完整解決方案，包括常見問題的修復步驟和診斷工具。我們為 Windows 和 macOS 環境提供了專門的工具和腳本。

## 2. 已創建的修復工具

### 2.1 Windows 環境工具

| 文件名 | 說明 |
|--------|------|
| `fix_qai_hub_client.bat` | 全面的 Windows 修復批處理腳本 |
| `fix_client_ini_windows.py` | Windows 環境的 client.ini 文件修復工具 |
| `test_qai_hub_api_windows.py` | Windows 環境的 API 連接測試工具 |

### 2.2 macOS 環境工具

| 文件名 | 說明 |
|--------|------|
| `fix_qai_hub_macos.sh` | 全面的 macOS 修復 shell 腳本 |
| `fix_client_ini_macos.py` | macOS 環境的 client.ini 文件修復工具 |
| `test_qai_hub_api.py` | macOS 環境的 API 連接測試工具 |

### 2.3 通用工具

| 文件名 | 說明 |
|--------|------|
| `qai_hub_demo_offline.py` | 離線演示模式，可在無法連接 API 時使用 |
| `check_qai_hub_status.py` | 檢查 QAI Hub 任務狀態的工具 |
| `QAI_HUB_TROUBLESHOOTING.md` | 全面的故障排除指南 |

## 3. 修復流程

### 3.1 Windows 環境

1. 運行全面修復批處理腳本：

   ```batch
   fix_qai_hub_client.bat
   ```

2. 使用 Python 診斷工具檢查問題：

   ```batch
   python fix_client_ini_windows.py
   python test_qai_hub_api_windows.py
   ```

3. 檢查 QAI Hub 狀態：

   ```batch
   python check_qai_hub_status.py
   ```

### 3.2 macOS 環境

1. 運行全面修復 shell 腳本：

   ```bash
   chmod +x fix_qai_hub_macos.sh
   ./fix_qai_hub_macos.sh
   ```

2. 使用 Python 診斷工具檢查問題：

   ```bash
   python fix_client_ini_macos.py
   python test_qai_hub_api.py
   ```

3. 檢查 QAI Hub 狀態：

   ```bash
   python check_qai_hub_status.py
   ```

## 4. 常見問題解決方案

### 4.1 配置文件問題

最常見的問題是 client.ini 文件格式不正確。正確的格式為：

```ini
[default]
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
```

### 4.2 網絡連接問題

如果您無法連接到 QAI Hub API，請檢查：

- 網絡連接是否正常
- 防火牆設置
- DNS 設置
- 是否在使用公司/學校網絡（可能有限制）

### 4.3 相依性問題

確保安裝了正確版本的相依性：

```bash
# 安裝正確版本的 protobuf
pip install protobuf==4.25.3

# 升級 QAI Hub SDK
pip install -U qai-hub qai-hub-models

# 配置 API 令牌
qai-hub configure --api_token <您的令牌>
```

### 4.4 Windows on ARM (Snapdragon X) 注意事項

如果您在 Windows on ARM 設備（如 Snapdragon X）上使用本系統：

1. 請使用 x64 版本的 Python 3.10（原生 ARM Python 暫不支援 AI Hub 客戶端）
2. 按照以下步驟驗證配置：

```python
# 驗證配置是否成功
import qai_hub as hub
print(hub.get_devices())
```

能列出裝置就表示配置成功。

## 5. 離線模式

如果網絡問題無法解決，您可以使用我們提供的離線演示模式：

```bash
python qai_hub_demo_offline.py
```

這將模擬 QAI Hub 的功能，讓您可以展示系統的主要功能。

## 6. 進階故障排除

更詳細的故障排除指南請參閱 `QAI_HUB_TROUBLESHOOTING.md` 文件。

---

希望這份指南能幫助您解決 Dragon X Fall Detection 系統與 QAI Hub 整合的問題。如有任何疑問，請參考相關文檔或聯絡我們的支持團隊。
