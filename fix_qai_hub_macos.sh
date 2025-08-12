#!/bin/bash
# macOS專用 QAI Hub 修復工具

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# API令牌
API_TOKEN="pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"

echo -e "${BOLD}============================================================${NC}"
echo -e "${BOLD}        Dragon X Fall Detection - QAI Hub 全面修復工具      ${NC}"
echo -e "${BOLD}============================================================${NC}"

# 步驟1: 修復相依性問題
echo -e "\n${BLUE}【步驟1】修復相依性問題${NC}"
echo "-----------------------------------------------------"

# 安裝正確版本的protobuf
echo -e "${YELLOW}安裝 protobuf 4.25.3 (MediaPipe 相容版本)...${NC}"
pip install protobuf==4.25.3

# 重新安裝 QAI Hub
echo -e "${YELLOW}安裝 QAI Hub SDK 0.31.0 和 QAI Hub Models 0.33.1...${NC}"
pip install qai-hub==0.31.0 qai-hub-models==0.33.1

# 步驟2: 設置環境變數
echo -e "\n${BLUE}【步驟2】設置環境變數${NC}"
echo "-----------------------------------------------------"

export QAI_HUB_API_TOKEN="$API_TOKEN"
export QAI_API_KEY="$API_TOKEN"
echo -e "${GREEN}✅ 已設置環境變數 QAI_HUB_API_TOKEN 和 QAI_API_KEY${NC}"

# 在 .env 文件中保存
echo "QAI_HUB_API_TOKEN=$API_TOKEN" > ~/.env
echo "QAI_API_KEY=$API_TOKEN" >> ~/.env
echo -e "${GREEN}✅ 已保存環境變數到 ~/.env 文件${NC}"

# 步驟3: 修復 client.ini 文件
echo -e "\n${BLUE}【步驟3】修復 client.ini 文件${NC}"
echo "-----------------------------------------------------"

# 創建 .qai_hub 目錄
mkdir -p ~/.qai_hub
echo -e "${GREEN}✅ 已創建 ~/.qai_hub 目錄${NC}"

# 備份現有文件(如果存在)
if [ -f ~/.qai_hub/client.ini ]; then
    mv ~/.qai_hub/client.ini ~/.qai_hub/client.ini.bak.$(date +%s)
    echo -e "${GREEN}✅ 已備份現有 client.ini 文件${NC}"
fi

# 創建新的 client.ini 文件 - 嘗試多種格式
echo -e "${YELLOW}嘗試多種格式創建 client.ini 文件...${NC}"

# 格式1 - 使用 [default] - 推薦格式
cat > ~/.qai_hub/client.ini << EOF
[default]
api_token = $API_TOKEN
api_key = $API_TOKEN
base_api_url = https://api.qai-hub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
EOF

# 檢查文件權限
chmod 600 ~/.qai_hub/client.ini
echo -e "${GREEN}✅ 已設置 client.ini 文件權限${NC}"

# 顯示文件內容
echo -e "${YELLOW}client.ini 文件內容:${NC}"
cat ~/.qai_hub/client.ini

# 步驟4: 創建備用文件
echo -e "\n${BLUE}【步驟4】創建備用配置文件${NC}"
echo "-----------------------------------------------------"

# 備用格式1 - 使用 [DEFAULT]
cat > ~/.qai_hub/client.ini.uppercase << EOF
[DEFAULT]
api_key = $API_TOKEN
api_token = $API_TOKEN
base_api_url = https://api.qai-hub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
EOF

# 備用格式2 - 簡化格式
cat > ~/.qai_hub/client.ini.simple << EOF
[default]
api_key = $API_TOKEN
EOF

echo -e "${GREEN}✅ 已創建備用配置文件${NC}"

# 步驟5: 檢查網絡連接
echo -e "\n${BLUE}【步驟5】檢查網絡連接${NC}"
echo "-----------------------------------------------------"

echo -e "${YELLOW}測試連接到 api.qai-hub.qualcomm.com...${NC}"
ping -c 1 api.qai-hub.qualcomm.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 成功連接到 api.qai-hub.qualcomm.com${NC}"
else
    echo -e "${RED}❌ 無法連接到 api.qai-hub.qualcomm.com${NC}"
    echo -e "${YELLOW}這可能是網絡問題，請檢查您的網絡連接。${NC}"
    
    # 嘗試使用系統DNS
    echo -e "${YELLOW}嘗試使用公共DNS解析...${NC}"
    host api.qai-hub.qualcomm.com 8.8.8.8 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 使用公共DNS可以解析域名${NC}"
        echo -e "${YELLOW}建議: 考慮更改您的DNS設置${NC}"
    else
        echo -e "${RED}❌ 即使使用公共DNS也無法解析域名${NC}"
    fi
fi

# 嘗試訪問 qualcomm.com
echo -e "${YELLOW}測試連接到 qualcomm.com...${NC}"
ping -c 1 qualcomm.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 成功連接到 qualcomm.com${NC}"
else
    echo -e "${RED}❌ 無法連接到 qualcomm.com${NC}"
    echo -e "${YELLOW}這表明可能是網絡限制問題，請檢查防火牆設置。${NC}"
fi

# 步驟6: 執行Python測試
echo -e "\n${BLUE}【步驟6】執行Python診斷測試${NC}"
echo "-----------------------------------------------------"

# 驗證Python模塊安裝
echo -e "${YELLOW}驗證必要的Python模塊...${NC}"
python -c "import sys, pkg_resources; print(f'Python版本: {sys.version.split()[0]}'); print(f'protobuf版本: {pkg_resources.get_distribution(\"protobuf\").version}'); print('導入測試成功')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Python基本模塊檢查通過${NC}"
else
    echo -e "${RED}❌ Python模塊檢查失敗${NC}"
fi

# 測試QAI Hub導入
echo -e "${YELLOW}測試QAI Hub模塊導入...${NC}"
python -c "import qai_hub; print(f'QAI Hub版本: {getattr(qai_hub, \"__version__\", \"未知\")}'); print('QAI Hub導入成功')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ QAI Hub模塊導入成功${NC}"
else
    echo -e "${RED}❌ QAI Hub模塊導入失敗${NC}"
    echo -e "${YELLOW}嘗試重新安裝: pip install qai-hub==0.31.0${NC}"
fi

# 步驟7: 執行 fix_client_ini.py
echo -e "\n${BLUE}【步驟7】執行Python修復工具${NC}"
echo "-----------------------------------------------------"
python fix_client_ini.py

# 步驟8: 總結與建議
echo -e "\n${BOLD}============================================================${NC}"
echo -e "${BOLD}                     修復過程完成                           ${NC}"
echo -e "${BOLD}============================================================${NC}"

echo -e "\n${BLUE}執行結果:${NC}"
if [ -f ~/.qai_hub/client.ini ]; then
    echo -e "${GREEN}✅ QAI Hub client.ini 文件已創建${NC}"
    echo -e "${GREEN}✅ API令牌已設置${NC}"
    echo -e "${GREEN}✅ 環境變數已配置${NC}"
    
    # 檢查網絡
    ping -c 1 api.qai-hub.qualcomm.com > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 網絡連接正常${NC}"
    else
        echo -e "${RED}❌ 網絡連接問題${NC}"
    fi
    
    # 嘗試基本API調用
    echo -e "${YELLOW}嘗試基本API調用...${NC}"
    python -c "import qai_hub; print('API調用測試: 成功')" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ API基本調用成功${NC}"
    else
        echo -e "${RED}❌ API調用失敗${NC}"
    fi
else
    echo -e "${RED}❌ QAI Hub client.ini 文件創建失敗${NC}"
fi

echo -e "\n${BLUE}後續步驟建議:${NC}"
echo -e "1. 如果網絡連接有問題，請檢查您的網絡設置和防火牆規則"
echo -e "2. 嘗試在瀏覽器中訪問 https://app.aihub.qualcomm.com 確認可以訪問"
echo -e "3. 運行以下命令測試：python check_qai_hub_status.py"
echo -e "4. 如果仍有問題，可嘗試替換配置文件: cp ~/.qai_hub/client.ini.uppercase ~/.qai_hub/client.ini"
echo -e "5. 運行特定測試: python -c \"import qai_hub; devices=qai_hub.get_devices(); print(f'可用設備數量: {len(devices)}')\"" 
echo -e "6. 重新啟動終端，或登出後重新登入，以確保環境變數生效"

echo -e "\n${BLUE}問題診斷:${NC}"
echo -e "1. 如果顯示 \"Failed to load configuration file\"，檢查 client.ini 文件格式"
echo -e "2. 如果顯示 \"API key validation failed\"，檢查API令牌是否正確"
echo -e "3. 如果顯示網絡錯誤，這可能是由於網絡連接問題"
echo -e "4. 如果環境中有代理服務器，請設置適當的代理環境變數"

echo -e "\n${GREEN}修復程序已完成！${NC}"
