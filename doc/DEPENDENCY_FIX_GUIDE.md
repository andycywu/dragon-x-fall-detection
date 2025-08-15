# 🛠️ Dragon X Fall Detection 依賴問題修復指南

## 問題概述

在安裝過程中，我們發現了以下幾個關鍵問題：

1. **版本衝突**：
   - NumPy 版本衝突：不同套件需要不同版本的 NumPy
   - Protobuf 版本衝突：MediaPipe 需要 4.x 而 QAI Hub 需要 3.x
   - PyTorch 安裝問題：CPU 特定版本格式不適用於 macOS

2. **QAI Hub 連接問題**：
   - 配置文件不存在或不正確
   - API Token 設置問題

## 修復方案

我們創建了以下工具來解決這些問題：

### 1. 🍎 修復版 Apple Silicon 安裝腳本

文件: `install_macos_apple_silicon_fixed.sh`

此腳本是專為 Apple Silicon Mac 設計的修復版安裝腳本，它：
- 安裝兼容版本的 NumPy (1.26.0)，解決版本衝突
- 使用 macOS 原生 PyTorch 版本，而非 CPU 特定版本
- 安裝兼容版本的 Protobuf (3.20.3)
- 按順序安裝依賴，避免相互覆蓋

使用方法：
```bash
chmod +x install_macos_apple_silicon_fixed.sh
./install_macos_apple_silicon_fixed.sh
```

### 2. 🔧 簡化版 QAI Hub 設置工具

文件: `setup_qai_hub_fixed.py`

這是一個簡化版的 QAI Hub 設置工具，它：
- 直接從 .env 文件讀取 API Token
- 自動創建 ~/.qai_hub/client.ini 配置文件
- 無需用戶輸入

使用方法：
```bash
python setup_qai_hub_fixed.py
```

### 3. 🌐 QAI Hub 環境變數設置腳本

文件: `setup_qai_hub_env.sh`

此腳本用於設置 QAI Hub 相關的環境變數：
- 從 .env 文件讀取 API Token 並設置為環境變數
- 設置其他 QAI Hub 相關環境變數

使用方法：
```bash
source setup_qai_hub_env.sh
```

### 4. 🔍 簡化版 QAI Hub 連接測試

文件: `test_qai_hub_simple.py`

這是一個簡化版的 QAI Hub 連接測試工具，它：
- 檢查環境變數和配置文件
- 測試是否可以連接到 QAI Hub
- 顯示可用的設備列表

使用方法：
```bash
python test_qai_hub_simple.py
```

## 推薦步驟

如果您遇到了依賴問題，請按照以下步驟操作：

1. **設置環境**：
   ```bash
   source setup_qai_hub_env.sh
   ```

2. **使用修復版安裝腳本**：
   ```bash
   ./install_macos_apple_silicon_fixed.sh
   ```

3. **檢查 QAI Hub 連接**：
   ```bash
   python test_qai_hub_simple.py
   ```

## 注意事項

- 某些依賴關係被設置為特定版本以解決衝突
- 對於特定的模塊，可能需要額外安裝相關依賴
- 如果您需要使用特定功能，可能需要手動調整相應的依賴版本
