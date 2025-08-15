# Dragon X Fall Detection 平台優化安裝指南

## 概述

此專案已針對不同平台進行優化，尤其是針對 ARM64 架構（如 Qualcomm Snapdragon X Elite、Apple Silicon 等）。使用本指南中的安裝腳本可以確保您獲得適合您平台的最佳性能。

## 平台特定優化

本專案支援以下平台的特定優化：

- **Windows ARM64** (Snapdragon X Elite 等)
  - DirectML 加速器
  - QNN (Qualcomm Neural Network) 加速器

- **Windows x64**
  - DirectML 加速器

- **macOS ARM64** (Apple Silicon)
  - CoreML 加速器

- **Linux ARM64**
  - QNN 加速器

## 安裝說明

### 1. 準備環境

強烈建議使用虛擬環境：

```bash
# 創建虛擬環境
python -m venv .venv_dragon_x

# 啟動虛擬環境
# Windows:
.venv_dragon_x\Scripts\activate
# macOS/Linux:
source .venv_dragon_x/bin/activate
```

### 2. 使用自動安裝腳本

#### Windows

直接雙擊運行 `install_dependencies.bat` 或在命令提示字元中執行：

```cmd
install_dependencies.bat
```

#### macOS / Linux

在終端機中執行：

```bash
# 賦予執行權限
chmod +x install_dependencies.sh

# 執行安裝腳本
./install_dependencies.sh
```

### 3. 手動安裝（進階用戶）

如果自動腳本無法正常工作，可以手動執行 Python 安裝腳本：

```bash
python install_platform_accelerators.py
```

## 驗證安裝

安裝完成後，您可以驗證加速器是否正確安裝：

```python
import onnxruntime as ort
print("可用的 ONNX 執行提供者:", ort.get_available_providers())
```

## 故障排除

### 找不到特定加速器包

某些加速器包可能僅在特定平台上可用：

- `onnxruntime-directml`: 僅適用於 Windows
- `onnxruntime-qnn`: 主要適用於 Snapdragon 設備和 Linux ARM64
- `onnxruntime-coreml`: 僅適用於 macOS

如果您在安裝過程中看到 "No matching distribution found" 錯誤，這通常意味著該特定加速器不適用於您的平台。安裝腳本會自動處理這種情況並安裝合適的替代品。

### 性能優化提示

- 在 Snapdragon X Elite 上，確保使用 QNN 加速器可提供最佳性能
- 在 Apple Silicon 上，CoreML 加速器可以顯著提升推理速度
- 使用 `--prefer-binary --only-binary=:all:` 選項可以避免從源代碼編譯，從而加快安裝速度
