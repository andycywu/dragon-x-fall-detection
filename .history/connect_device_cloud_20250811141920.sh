#!/bin/bash
# Qualcomm Device Cloud SSH連接和部署腳本

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐉 Dragon X Fall Detection System${NC}"
echo -e "${CYAN}Qualcomm Device Cloud 部署腳本${NC}"
echo "=============================================="

# 檢查SSH密鑰
if [ ! -f "qdc_id_2025-8-11_62.pem" ]; then
    echo -e "${RED}❌ SSH密鑰文件不存在: qdc_id_2025-8-11_62.pem${NC}"
    echo "請確保SSH密鑰在當前目錄中"
    exit 1
fi

# 設置SSH密鑰權限
chmod 600 qdc_id_2025-8-11_62.pem
echo -e "${GREEN}✅ SSH密鑰權限設置完成${NC}"

# 獲取Device Cloud設備IP
echo -e "${YELLOW}📋 請提供Device Cloud設備信息:${NC}"
read -p "設備IP地址: " DEVICE_IP
read -p "用戶名 (默認: root): " USERNAME
USERNAME=${USERNAME:-root}

if [ -z "$DEVICE_IP" ]; then
    echo -e "${RED}❌ 設備IP地址不能為空${NC}"
    exit 1
fi

echo -e "${BLUE}🔗 連接信息:${NC}"
echo "   設備IP: $DEVICE_IP"
echo "   用戶名: $USERNAME"
echo "   SSH密鑰: qdc_id_2025-8-11_62.pem"

# 測試SSH連接
echo -e "${YELLOW}🔍 測試SSH連接...${NC}"
ssh -i qdc_id_2025-8-11_62.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no $USERNAME@$DEVICE_IP "echo 'SSH連接成功'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SSH連接測試成功${NC}"
else
    echo -e "${RED}❌ SSH連接失敗，請檢查網絡和設備狀態${NC}"
    exit 1
fi

# 創建部署腳本
echo -e "${YELLOW}📦 創建部署腳本...${NC}"

cat > device_cloud_deploy.sh << 'EOL'
#!/bin/bash
# Device Cloud遠程部署腳本

echo "🐉 在Device Cloud上部署Dragon X Fall Detection System"
echo "=================================================="

# 創建項目目錄
mkdir -p /opt/dragon_x_fall_detection
cd /opt/dragon_x_fall_detection

# 安裝Git（如果不存在）
which git > /dev/null
if [ $? -ne 0 ]; then
    echo "📦 安裝Git..."
    apt update && apt install -y git
fi

# 克隆項目（如果已存在則更新）
if [ -d ".git" ]; then
    echo "🔄 更新現有項目..."
    git pull origin main
else
    echo "📥 克隆項目..."
    # 這裡需要替換為實際的GitHub倉庫URL
    echo "請手動克隆項目或上傳文件"
fi

# 運行設置腳本
if [ -f "device_cloud_setup.py" ]; then
    echo "🚀 運行設置腳本..."
    python3 device_cloud_setup.py
else
    echo "⚠️ 設置腳本不存在，請手動上傳項目文件"
fi

echo "✅ 部署完成！"
EOL

chmod +x device_cloud_deploy.sh

# 上傳項目文件到Device Cloud
echo -e "${YELLOW}📤 上傳項目文件到Device Cloud...${NC}"

# 創建核心文件列表
CORE_FILES=(
    "unified_ai_detector.py"
    "dragon_x_fall_detection_system.py"
    "device_cloud_setup.py"
    "cross_platform_ai_detector.py"
    "real_qai_hub_onnx_detector.py"
    "requirements.txt"
    "README.md"
    "hackathon_final_demo.py"
    "hackathon_success_summary.py"
)

# 上傳核心文件
echo -e "${BLUE}🔄 上傳核心文件...${NC}"
for file in "${CORE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   📁 上傳: $file"
        scp -i qdc_id_2025-8-11_62.pem -o StrictHostKeyChecking=no "$file" $USERNAME@$DEVICE_IP:/tmp/
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✅ $file 上傳成功${NC}"
        else
            echo -e "   ${RED}❌ $file 上傳失敗${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠️ $file 不存在${NC}"
    fi
done

# 上傳部署腳本
echo -e "${BLUE}🔄 上傳部署腳本...${NC}"
scp -i qdc_id_2025-8-11_62.pem -o StrictHostKeyChecking=no device_cloud_deploy.sh $USERNAME@$DEVICE_IP:/tmp/

# 執行遠程部署
echo -e "${YELLOW}🚀 執行遠程部署...${NC}"
ssh -i qdc_id_2025-8-11_62.pem -o StrictHostKeyChecking=no $USERNAME@$DEVICE_IP << 'REMOTE_SCRIPT'

echo "🐉 在Device Cloud設備上開始部署..."

# 創建項目目錄
sudo mkdir -p /opt/dragon_x_fall_detection
cd /opt/dragon_x_fall_detection

# 移動上傳的文件
echo "📁 整理項目文件..."
sudo mv /tmp/unified_ai_detector.py . 2>/dev/null
sudo mv /tmp/dragon_x_fall_detection_system.py . 2>/dev/null
sudo mv /tmp/device_cloud_setup.py . 2>/dev/null
sudo mv /tmp/cross_platform_ai_detector.py . 2>/dev/null
sudo mv /tmp/real_qai_hub_onnx_detector.py . 2>/dev/null
sudo mv /tmp/requirements.txt . 2>/dev/null
sudo mv /tmp/README.md . 2>/dev/null
sudo mv /tmp/hackathon_final_demo.py . 2>/dev/null
sudo mv /tmp/hackathon_success_summary.py . 2>/dev/null
sudo mv /tmp/device_cloud_deploy.sh . 2>/dev/null

# 設置權限
sudo chmod +x *.py
sudo chmod +x *.sh

# 檢查Python
echo "🐍 檢查Python環境..."
python3 --version

# 運行設置腳本
if [ -f "device_cloud_setup.py" ]; then
    echo "🚀 運行設置腳本..."
    sudo python3 device_cloud_setup.py
else
    echo "⚠️ 設置腳本不存在"
fi

echo "✅ Device Cloud部署完成！"
echo "📋 項目位置: /opt/dragon_x_fall_detection"
echo "🚀 可以執行以下命令測試:"
echo "   cd /opt/dragon_x_fall_detection"
echo "   python3 unified_ai_detector.py"
echo "   python3 dragon_x_fall_detection_system.py"
echo "   python3 hackathon_final_demo.py"

REMOTE_SCRIPT

echo -e "${GREEN}🎉 Device Cloud部署完成！${NC}"
echo "=============================================="
echo -e "${CYAN}📋 接下來可以:${NC}"
echo "1. SSH連接到設備:"
echo "   ssh -i qdc_id_2025-8-11_62.pem $USERNAME@$DEVICE_IP"
echo ""
echo "2. 進入項目目錄:"
echo "   cd /opt/dragon_x_fall_detection"
echo ""
echo "3. 運行AI檢測系統:"
echo "   python3 unified_ai_detector.py"
echo "   python3 dragon_x_fall_detection_system.py"
echo "   python3 hackathon_final_demo.py"
echo ""
echo -e "${GREEN}🐉 準備在Snapdragon X Elite上測試你的AI系統！${NC}"
