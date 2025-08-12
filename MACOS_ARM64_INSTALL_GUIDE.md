# macOS ARM64 (Apple Silicon) 安裝指南

本指南提供在 Apple Silicon Mac 上安裝 Dragon X Fall Detection 系統的詳細步驟。

## 系統要求

- macOS 11.0 (Big Sur) 或更高版本
- Apple Silicon Mac (M1/M2/M3 系列處理器)
- Python 3.8 或更高版本 (建議使用 Python 3.11)
- 最少 4GB 可用記憶體
- 最少 2GB 可用磁碟空間

## 前置準備

1. 安裝 Homebrew (如果尚未安裝)：
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. 安裝 Python (如果尚未安裝)：
   ```bash
   brew install python@3.11
   ```

3. 安裝 git (如果尚未安裝)：
   ```bash
   brew install git
   ```

## 安裝步驟

### 1. 創建並啟動虛擬環境

```bash
# 創建虛擬環境
python3 -m venv .venv_dragon_x

# 啟動虛擬環境
source .venv_dragon_x/bin/activate
```

### 2. 使用自動安裝腳本

```bash
# 確保腳本有執行權限
chmod +x install_dependencies.sh

# 執行安裝腳本
./install_dependencies.sh
```

或者，使用 Python 腳本：

```bash
python3 setup_dev_environment.py
```

### 3. 設置 QAI Hub

按照提示完成 QAI Hub 的設置：
```bash
python3 qai_hub_setup_assistant.py
```

## Apple Silicon 特定優化

Dragon X Fall Detection 系統在 Apple Silicon Mac 上進行了以下優化：

1. **CoreML 加速器**：利用 Apple 的 Neural Engine 進行硬體加速。

2. **Metal Performance Shaders (MPS)**：自動啟用 PyTorch 的 MPS 後端，以利用 Apple GPU。

3. **ARM64 原生二進制包**：所有依賴包都使用 ARM64 原生編譯版本，而非通過 Rosetta 2 轉譯的 x86 版本。

## 驗證安裝

運行以下命令檢查安裝是否成功：

```bash
# 檢查平台優化
python3 check_platform_optimizations.py

# 測試 QAI Hub 連接
python3 test_qai_hub_connection.py
```

## 故障排除

### 安裝依賴失敗

如果使用 `pip install` 時出現 "No matching distribution found" 錯誤，可能是因為某些包沒有 ARM64 原生版本。嘗試以下解決方案：

```bash
# 使用平台特定安裝腳本
python3 install_platform_accelerators.py
```

### QAI Hub 連接問題

如果無法連接到 QAI Hub，請確保：

1. 您已創建並設置了 QAI Hub 帳戶
2. 您的 API Token 已正確配置在 `~/.qai_hub/client.ini`
3. 您的網絡連接正常

如需更多幫助，請運行：
```bash
python3 qai_hub_setup_assistant.py
```

## 性能最佳實踐

為了在 Apple Silicon Mac 上獲得最佳性能：

1. 確保 CoreML 加速器已啟用
2. 使用 PyTorch MPS 後端進行 GPU 加速
3. 保持系統和依賴包更新至最新版本
4. 關閉不必要的背景應用程序以釋放系統資源
