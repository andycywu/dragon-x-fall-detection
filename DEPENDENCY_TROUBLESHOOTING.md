# 解決 onnxruntime-directml 依賴問題指南

## 問題概述

當執行 `pip download -r requirements.txt -d wheelhouse --only-binary=:all: --prefer-binary` 命令時，出現以下錯誤：

```
ERROR: Could not find a version that satisfies the requirement onnxruntime-directml==1.18.0 (from versions: none)
ERROR: No matching distribution found for onnxruntime-directml==1.18.0
```

這是因為 `onnxruntime-directml` 是 Windows 平台特定的加速器，在 macOS 上不可用。同樣地，其他平台特定的加速器在非目標平台上也會出現類似問題。

## 解決方案

我們已經創建了一系列腳本來解決這個問題，使系統能夠根據您的平台自動安裝適當的加速器：

### 1. 使用平台特定安裝腳本

替代直接使用 `pip install -r requirements.txt`，請使用以下腳本之一：

- **macOS/Linux**: `./install_dependencies.sh`
- **Windows**: `install_dependencies.bat`

這些腳本會檢測您的平台，並只安裝與您的系統兼容的加速器。

### 2. 使用 Python 安裝工具

作為替代選擇，您可以使用我們的 Python 安裝腳本：

```bash
python install_platform_accelerators.py
```

或者使用完整的環境設置工具：

```bash
python setup_dev_environment.py
```

### 3. 手動修改 requirements.txt

如果您需要手動管理依賴，可以根據您的平台從 `requirements.txt` 中註釋掉不相容的加速器：

- **對於 macOS**:
  - 保留: `onnxruntime==1.18.0`
  - 手動安裝: `pip install onnxruntime-coreml`
  - 註釋掉: `onnxruntime-directml` 和 `onnxruntime-qnn`

- **對於 Windows x64**:
  - 保留: `onnxruntime==1.18.0`
  - 手動安裝: `pip install onnxruntime-directml==1.18.0`
  - 註釋掉: `onnxruntime-qnn`

- **對於 Windows ARM64 (Snapdragon)**:
  - 保留: `onnxruntime==1.18.0`
  - 手動安裝: `pip install onnxruntime-directml==1.18.0 onnxruntime-qnn==1.18.0`

- **對於 Linux ARM64**:
  - 保留: `onnxruntime==1.18.0`
  - 手動安裝: `pip install onnxruntime-qnn==1.18.0`

## 平台特定加速器對照表

| 平台 | 架構 | 推薦加速器 | 安裝命令 |
|------|------|------------|----------|
| Windows | x64 | DirectML | `pip install onnxruntime-directml==1.18.0` |
| Windows | ARM64 | QNN + DirectML | `pip install onnxruntime-directml==1.18.0 onnxruntime-qnn==1.18.0` |
| macOS | Intel | CPU only | 使用基本的 `onnxruntime` |
| macOS | ARM64 | CoreML | `pip install onnxruntime-coreml` |
| Linux | x64 | CPU only | 使用基本的 `onnxruntime` |
| Linux | ARM64 | QNN | `pip install onnxruntime-qnn==1.18.0` |

## 下載依賴包到本地

如果您想預先下載所有依賴包到本地 wheelhouse 目錄，請根據您的平台使用以下命令：

### macOS (Apple Silicon)

```bash
# 基本依賴
pip download -r requirements.txt -d wheelhouse --only-binary=:all: --prefer-binary --platform=macosx_11_0_arm64 --python-version=3.11

# CoreML 加速器
pip download onnxruntime-coreml -d wheelhouse --only-binary=:all: --prefer-binary --platform=macosx_11_0_arm64 --python-version=3.11
```

### Windows (x64)

```bash
# 基本依賴
pip download -r requirements.txt -d wheelhouse --only-binary=:all: --prefer-binary --platform=win_amd64 --python-version=3.11

# DirectML 加速器
pip download onnxruntime-directml==1.18.0 -d wheelhouse --only-binary=:all: --prefer-binary --platform=win_amd64 --python-version=3.11
```

### Windows (ARM64)

```bash
# 基本依賴
pip download -r requirements.txt -d wheelhouse --only-binary=:all: --prefer-binary --platform=win_arm64 --python-version=3.11

# DirectML 和 QNN 加速器
pip download onnxruntime-directml==1.18.0 onnxruntime-qnn==1.18.0 -d wheelhouse --only-binary=:all: --prefer-binary --platform=win_arm64 --python-version=3.11
```

## 進一步幫助

如果您仍然遇到問題，請運行診斷工具來檢查您的環境：

```bash
python check_platform_optimizations.py
```

這將顯示關於您的系統和可用加速器的詳細信息，以幫助診斷問題。
