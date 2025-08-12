#!/bin/bash
# QAI Hub client.ini 修復腳本 - macOS 版本

echo "=== Dragon X Fall Detection System - QAI Hub Client 修復工具 ==="
echo "==========================================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API 令牌
API_TOKEN="pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"

# 設置環境變數
export QAI_HUB_API_TOKEN="$API_TOKEN"
export QAI_API_KEY="$API_TOKEN"

echo -e "${BLUE}步驟 1: 設置環境變數${NC}"
echo "QAI_HUB_API_TOKEN 已設置"

# 在 .env 文件中保存 API 令牌
echo "QAI_HUB_API_TOKEN=$API_TOKEN" > ~/.env
echo "QAI_API_KEY=$API_TOKEN" >> ~/.env
echo -e "${GREEN}✅ 環境變數已保存至 ~/.env${NC}"

# 創建 .qai_hub 目錄
echo -e "${BLUE}步驟 2: 創建 .qai_hub 目錄${NC}"
mkdir -p ~/.qai_hub
echo -e "${GREEN}✅ 創建 ~/.qai_hub 目錄${NC}"

# 創建 client.ini 文件 - 使用 QAI Hub SDK 0.34.0 支持的格式
echo -e "${BLUE}步驟 3: 創建 client.ini 文件${NC}"
cat > ~/.qai_hub/client.ini << EOF
[default]
api_token = $API_TOKEN
api_key = $API_TOKEN
base_api_url = https://api.qai-hub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
EOF

# 檢查文件是否已創建
if [ -f ~/.qai_hub/client.ini ]; then
    echo -e "${GREEN}✅ client.ini 文件已創建${NC}"
    echo "文件內容:"
    cat ~/.qai_hub/client.ini
else
    echo -e "${RED}❌ client.ini 文件創建失敗${NC}"
fi

# 檢查網絡連接
echo -e "${BLUE}步驟 4: 檢查網絡連接${NC}"
ping -c 1 api.qai-hub.qualcomm.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 可以連接到 api.qai-hub.qualcomm.com${NC}"
else
    echo -e "${RED}❌ 無法連接到 api.qai-hub.qualcomm.com${NC}"
    echo "請檢查您的網絡連接或防火牆設置"
fi

# 檢查依賴
echo -e "${BLUE}步驟 5: 檢查相依性${NC}"
python -c "import pkg_resources; print('protobuf 版本:', pkg_resources.get_distribution('protobuf').version)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️ 無法找到 protobuf 包${NC}"
    echo "安裝 protobuf 4.25.3..."
    pip install protobuf==4.25.3
else
    PROTOBUF_VERSION=$(python -c "import pkg_resources; print(pkg_resources.get_distribution('protobuf').version)")
    # 檢查版本是否為 3.x 或 4.x
    if [[ "$PROTOBUF_VERSION" == 3.* ]] || [[ "$PROTOBUF_VERSION" == 4.* ]]; then
        echo -e "${GREEN}✅ protobuf 版本相容: $PROTOBUF_VERSION${NC}"
    else
        echo -e "${YELLOW}⚠️ protobuf 版本可能不相容: $PROTOBUF_VERSION${NC}"
        echo "安裝 protobuf 4.25.3..."
        pip install protobuf==4.25.3
    fi
fi

# 嘗試安裝或更新 QAI Hub
echo -e "${BLUE}步驟 6: 安裝/更新 QAI Hub${NC}"
pip install qai-hub==0.31.0 qai-hub-models==0.33.1

# 測試導入 QAI Hub
echo -e "${BLUE}步驟 7: 測試 QAI Hub 模組導入${NC}"
python -c "import qai_hub; print('QAI Hub 版本:', getattr(qai_hub, '__version__', '未知'))" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ QAI Hub 模組導入成功${NC}"
else
    echo -e "${RED}❌ QAI Hub 模組導入失敗${NC}"
fi

# 執行 Python 修復工具
echo -e "${BLUE}步驟 8: 執行 Python 修復工具${NC}"
python fix_client_ini.py

echo -e "${GREEN}QAI Hub client.ini 修復完成!${NC}"
echo "如果仍有問題，請嘗試以下操作:"
echo "1. 重新啟動終端或系統"
echo "2. 檢查網絡連接和防火牆設置"
echo "3. 運行 'python check_qai_hub_status.py' 來驗證設置"
