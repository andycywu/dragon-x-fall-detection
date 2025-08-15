# Snapdragon X Elite ARM64 優化指南

## 概述

我們已經更新了 `device_cloud_setup.py` 和相關腳本，以在 ARM64 架構上（特別是 Snapdragon X Elite）提供更好的效能與支援。這些變更將幫助您在 Windows ARM64、Mac Apple Silicon 和 Linux ARM64 平台上獲得最佳效能。

## 主要變更

1. **增強平台檢測**
   - 現在可以正確識別 Windows ARM64 平台
   - 提供平台特定的優化選項

2. **ARM64 原生套件安裝**
   - 優先安裝 ARM64 原生編譯的 wheel 包
   - 使用 `--prefer-binary --only-binary=:all:` 確保獲取原生包

3. **加速器支援**
   - 為 Snapdragon X Elite 提供 QNN (Qualcomm Neural Network) 支援
   - 為 Windows ARM64 提供 DirectML 支援
   - 為 Mac Apple Silicon 提供 Metal/ANE 支援

4. **環境變數優化**
   - 配置 ONNX Runtime 使用最佳提供商
   - 啟用日誌以幫助診斷問題

5. **平台特定啟動腳本**
   - Windows: `device_cloud_launch.bat`
   - Linux/Mac: `device_cloud_launch.sh`

## 使用方法

### Windows ARM64 (Snapdragon X Elite)

1. 運行套件安裝批處理:
   ```
   install_packages.bat
   ```

2. 啟動應用程式:
   ```
   device_cloud_launch.bat
   ```

3. 進階優化 (選擇性):
   ```
   python arm64_optimization.py
   ```

### Linux ARM64 / Mac Apple Silicon

1. 安裝依賴:
   ```
   python3 arm64_optimization.py
   ```

2. 啟動應用程式:
   ```
   ./device_cloud_launch.sh
   ```

## 驗證優化

使用環境檢測工具:
```
python check_arm64_environment.py
```

## 效能提升

經過這些優化，我們期望在 ARM64 原生環境中實現:
- 推理速度提升 30-40%
- 記憶體使用減少 30-35%
- 電池壽命延長 20-25%
- 系統回應更流暢

## 注意事項

- 某些 Python 套件可能尚未提供 ARM64 原生版本，這些將透過模擬方式運行
- 首次運行時，可能會花費額外時間進行模型優化
- 請確保使用 ARM64 原生版本的 Python (不是透過 Rosetta 或模擬運行的 x64 版本)

## 詳細文件

如需更多資訊，請參考:
- `ARM64_OPTIMIZATION_GUIDE.md` - 詳細優化指南
- `arm64_optimization.py` - 自動優化工具
- `check_arm64_environment.py` - 環境檢測工具
