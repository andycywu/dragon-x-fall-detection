#!/bin/bash
# QAI Hub 環境變數設置腳本
# 從 .env 文件讀取環境變數並設置 QAI Hub 配置

echo "🔧 設置 QAI Hub 環境變數..."

# 檢查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 找不到 .env 文件"
    exit 1
fi

# 從 .env 文件讀取 API Token
API_TOKEN=$(grep -E "^QAI_HUB_API_TOKEN" .env | cut -d'=' -f2 | tr -d ' ')

if [ -z "$API_TOKEN" ]; then
    echo "❌ 在 .env 文件中找不到 QAI_HUB_API_TOKEN"
    exit 1
fi

echo "✅ 從 .env 文件讀取了 API Token"

# 設置環境變數
export QAI_HUB_TOKEN="$API_TOKEN"
export QAI_HUB_API_TOKEN="$API_TOKEN"
echo "✅ 已設置 QAI_HUB_TOKEN 和 QAI_HUB_API_TOKEN 環境變數"

# 如果存在 QAI_HUB_BASE_URL，也設置它
BASE_URL=$(grep -E "^QAI_HUB_BASE_URL" .env | cut -d'=' -f2 | tr -d ' ')
if [ ! -z "$BASE_URL" ]; then
    export QAI_HUB_BASE_URL="$BASE_URL"
    echo "✅ 已設置 QAI_HUB_BASE_URL 環境變數"
else
    export QAI_HUB_BASE_URL="https://app.aihub.qualcomm.com"
    echo "✅ 已設置默認 QAI_HUB_BASE_URL 環境變數"
fi

# 如果存在 QAI_HUB_DEVICE_GROUP，也設置它
DEVICE_GROUP=$(grep -E "^QAI_HUB_DEVICE_GROUP" .env | cut -d'=' -f2 | tr -d ' ')
if [ ! -z "$DEVICE_GROUP" ]; then
    export QAI_HUB_DEVICE_GROUP="$DEVICE_GROUP"
    echo "✅ 已設置 QAI_HUB_DEVICE_GROUP 環境變數"
fi

# 創建 QAI Hub 配置文件
mkdir -p ~/.qai_hub
cat > ~/.qai_hub/client.ini << EOF
[api]
api_token = ${QAI_HUB_API_TOKEN}
api_url = ${QAI_HUB_BASE_URL}/
web_url = ${QAI_HUB_BASE_URL}/
verbose = true
EOF

# 設置文件權限
chmod 600 ~/.qai_hub/client.ini
echo "✅ 已創建 QAI Hub 配置文件: ~/.qai_hub/client.ini"

echo "🎉 QAI Hub 環境變數和配置設置完成！"
echo "您現在可以使用 QAI Hub 功能。"

# 顯示如何在當前 shell 中使用
echo ""
echo "注意：如果您需要在當前 shell 中使用這些環境變數，請使用 source 命令執行此腳本："
echo "source ./setup_qai_hub_env.sh"
