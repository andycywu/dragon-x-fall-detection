# 🔧 Qualcomm AI Hub API 配置指南

## 📱 獲取 QAI Hub API Token

### 步驟 1: 註冊 AI Hub 帳戶
1. 訪問 [Qualcomm AI Hub](https://aihub.qualcomm.com/)
2. 點擊 "Sign Up" 註冊新帳戶
3. 填寫必要信息並驗證郵箱

### 步驟 2: 申請 API 訪問權限
1. 登入後訪問 [API文檔頁面](https://app.aihub.qualcomm.com/docs)
2. 申請開發者訪問權限
3. 等待審核通過（通常1-2個工作日）

### 步驟 3: 獲取 API Token
1. 登入 [AI Hub Console](https://app.aihub.qualcomm.com/)
2. 進入 "Settings" -> "API Keys"
3. 點擊 "Generate New Token"
4. 複製生成的 API Token

## ⚙️ 配置 API Token

### 方法 1: 使用 .env 文件 (推薦)
1. 打開項目根目錄的 `.env` 文件
2. 找到 `QAI_HUB_API_TOKEN=your_api_token_here`
3. 將 `your_api_token_here` 替換為你的實際 API Token

```bash
# 範例
QAI_HUB_API_TOKEN=qai_hub_xxxxxxxxxxxxxxxxxxxxxxxx
```

### 方法 2: 使用環境變量
```bash
# macOS/Linux
export QAI_HUB_API_TOKEN="your_actual_token_here"

# Windows
set QAI_HUB_API_TOKEN=your_actual_token_here
```

### 方法 3: 直接配置文件
系統會自動創建 `~/.qai_hub/client.ini` 文件：
```ini
[default]
api_token = your_actual_token_here
```

## 🧪 測試 API 配置

### 使用配置管理器測試
```bash
cd /Users/andycyw/mvp_fall_detection_starter
source .venv_mediapipe/bin/activate
python config_manager.py
```

### 使用 QAI Hub 集成測試
```bash
python qai_hub_integration.py
```

### 預期輸出
```
🔧 配置狀態檢查
========================================
📱 QAI Hub API Token: ✅ 已設置
🚀 硬件加速: ✅ 啟用
⚡ 優化級別: balanced
```

## 🚨 常見問題

### Q1: API Token 無效
**症狀**: "Invalid API token" 錯誤
**解決方案**:
1. 檢查 Token 是否正確複製（沒有多餘空格）
2. 確認 Token 沒有過期
3. 重新生成新的 Token

### Q2: 網絡連接問題
**症狀**: "Connection timeout" 錯誤
**解決方案**:
1. 檢查網絡連接
2. 確認防火牆設置
3. 嘗試使用代理（如有需要）

### Q3: 權限不足
**症狀**: "Access denied" 錯誤
**解決方案**:
1. 確認帳戶已通過審核
2. 檢查 API 使用配額
3. 聯繫 Qualcomm 支持

## 📊 API 使用限制

### 免費帳戶限制
- **推理次數**: 1000次/月
- **模型大小**: 100MB以下
- **設備類型**: CPU, GPU
- **併發請求**: 5個

### 商業帳戶限制
- **推理次數**: 無限制
- **模型大小**: 無限制
- **設備類型**: CPU, GPU, NPU, DSP
- **併發請求**: 50個

## 🔄 無 API Token 的備用方案

如果無法獲取 API Token，系統會自動:

1. **禁用 QAI Hub 加速**
2. **使用 CPU 推理**
3. **保持所有核心功能**
4. **顯示性能對比**

```python
# 系統會自動降級到 CPU 模式
INFO: QAI Hub API Token未配置，使用CPU模式
INFO: 檢測功能正常，但無硬件加速
```

## 🎯 黑客松演示建議

### 有 API Token 的情況
- ✅ 展示硬件加速效果
- ✅ 性能對比演示
- ✅ 功耗降低展示
- ✅ 實時推理速度

### 無 API Token 的情況
- ✅ 展示完整檢測功能
- ✅ 強調技術整合
- ✅ 說明商業化潛力
- ✅ 展示系統穩定性

## 📞 技術支持

### Qualcomm AI Hub 支持
- **文檔**: https://app.aihub.qualcomm.com/docs
- **社區**: https://developer.qualcomm.com/forums
- **支持**: support@qti.qualcomm.com

### 項目技術支持
- **GitHub Issues**: 項目 Issues 頁面
- **配置檢查**: `python config_manager.py`
- **系統測試**: `python hackathon_launcher.py`

---

## 🚀 快速開始

```bash
# 1. 配置 API Token
echo "QAI_HUB_API_TOKEN=your_token_here" >> .env

# 2. 測試配置
python config_manager.py

# 3. 啟動系統
python hackathon_launcher.py
```

**準備好征服黑客松了！** 🏆
