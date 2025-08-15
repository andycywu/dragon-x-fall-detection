# QAI Hub 配置修復說明

## 問題原因

QAI Hub 的 API 網址已經從 `api.qai-hub.qualcomm.com` 更新為 `api.aihub.qualcomm.com`，需要更新配置文件。

## 修復方法

### 1) 手動修復

#### 1.1) client.ini 檔案位置

- macOS：`~/.qai_hub/client.ini`
- Windows：`C:\Users\你的用戶名\.qai_hub\client.ini`

#### 1.2) 修改內容為

```ini
[default]
api_token = [你的token]
api_key = [你的token]
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
```

### 2) 自動修復

#### 2.1) 使用提供的腳本

- macOS/Linux：運行 `python update_qai_hub_config.py`
- Windows：雙擊運行 `update_qai_hub_config.bat`

#### 2.2) 或使用以下命令（適用所有平台）

```bash
pip install -U qai-hub qai-hub-models
qai-hub configure --api_token [你的token]
```

## 驗證配置

執行以下 Python 代碼來驗證設置是否正確：

```python
import qai_hub as hub
print(hub.get_devices())
```

如果能列出裝置，就表示設定成功。

## 特別說明

對於 Windows on ARM 裝置（如 Snapdragon X）：

- 需要使用 x64 版本的 Python 3.10
- 不要使用 ARM64 版本的 Python，因為目前 QAI Hub Python API 不支援原生 ARM Python

## API URL 與 Token 匹配問題

某些情況下，不同的 API URL 可能需要使用不同的 token。這是因為 Qualcomm 在 API 遷移過程中可能為新舊 API 端點分配了不同的認證信息。

### 症狀

- 使用某個 API URL 時，即使 token 正確也無法連接
- 配置更新後連接失敗，錯誤信息包含身份驗證或授權相關內容
- 某些 SDK 版本只能與特定 API URL 配合使用

### 自動診斷與修復

我們提供了一個智能工具，可以自動檢測並解決 API URL 與 token 匹配問題：

```bash
# 運行自動診斷與修復工具
python fix_qai_hub_api_url.py
```

在 Windows 上，可以直接雙擊運行 `fix_qai_hub_api_url.bat`

這個工具會：

1. 測試不同的 API URL 和 token 組合
2. 找出能夠成功連接的最佳組合
3. 自動更新配置文件
4. 提供詳細的診斷信息

### 手動解決方法

如果自動工具無法解決問題，您可以：

1. 聯絡 Qualcomm 支持團隊獲取特定 API URL 對應的正確 token
2. 嘗試不同的 SDK 版本（某些版本可能與特定 API URL 更兼容）
3. 針對您的特定 SDK 版本，在配置文件中手動測試兩種 URL：
   - `https://api.aihub.qualcomm.com`
   - `https://api.qai-hub.qualcomm.com`

## Windows 長路徑問題

在 Windows 上安裝 QAI Hub 相關套件時，可能會遇到以下錯誤：

```console
ERROR: Could not install packages due to an OSError: [WinError 3] The system cannot find the path specified
HINT: This error might have occurred since this system does not have Windows Long Path support enabled.
```

### 解決方法

1. **啟用 Windows 長路徑支援**：
   - 以管理員身份開啟 PowerShell
   
   ```powershell
   # 啟用長路徑支援
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord
   ```
   
   - 重新啟動電腦

2. **使用虛擬環境安裝**：
   
   ```batch
   # 建立虛擬環境（路徑短）
   python -m venv C:\qai_env

   # 啟用虛擬環境
   C:\qai_env\Scripts\activate

   # 安裝套件
   pip install -U qai-hub qai-hub-models
   ```

3. **使用管理員權限安裝**：
   - 以管理員身份開啟命令提示字元
   - 執行安裝命令
   
   ```batch
   pip install -U qai-hub qai-hub-models
   ```

4. **使用較舊版本的套件**：
   - 如果上述方法都不起作用，嘗試安裝較舊版本
   
   ```batch
   pip install qai-hub==0.30.0 qai-hub-models==0.30.0
   ```

安裝完成後，別忘了配置您的 API token：

```batch
qai-hub configure --api_token [你的token]
```
