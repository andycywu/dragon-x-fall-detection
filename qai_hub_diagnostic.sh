#!/bin/bash

# QAI Hub 環境檢查與修復彙總腳本
# 此腳本執行所有診斷工具，提供全面的狀態報告

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 無顏色

# 標題
echo -e "\n${BLUE}=========================================================${NC}"
echo -e "${BLUE}            QAI Hub 環境檢查與修復彙總工具                ${NC}"
echo -e "${BLUE}=========================================================${NC}\n"

# 檢查操作系統
echo -e "${BLUE}檢測操作系統...${NC}"
OS="未知"

if [[ "$(uname)" == "Darwin" ]]; then
    OS="macOS"
    echo -e "${GREEN}檢測到 macOS 系統${NC}"
elif [[ "$(uname)" == "Linux" ]]; then
    OS="Linux"
    echo -e "${GREEN}檢測到 Linux 系統${NC}"
elif [[ "$(uname)" == "MINGW"* ]] || [[ "$(uname)" == "MSYS"* ]] || [[ "$(uname)" == "CYGWIN"* ]]; then
    OS="Windows"
    echo -e "${GREEN}檢測到 Windows 系統${NC}"
else
    echo -e "${YELLOW}無法確定操作系統類型，將嘗試通用修復方法${NC}"
fi

# 創建臨時目錄存放報告
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_DIR="qai_hub_diagnostic_report_${TIMESTAMP}"
mkdir -p "${REPORT_DIR}"

echo -e "${BLUE}診斷報告將保存在: ${REPORT_DIR}${NC}\n"

# 步驟 1: 檢查 Python 環境
echo -e "${BLUE}步驟 1: 檢查 Python 環境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}錯誤: 未找到 Python3${NC}"
    echo -e "${YELLOW}請安裝 Python 3.7 或更高版本${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}已找到 Python 版本: ${PYTHON_VERSION}${NC}"

# 檢查 pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}錯誤: 未找到 pip3${NC}"
    echo -e "${YELLOW}請安裝 pip3${NC}"
    exit 1
fi
echo -e "${GREEN}已找到 pip3${NC}\n"

# 步驟 2: 檢查 QAI Hub 狀態
echo -e "${BLUE}步驟 2: 檢查 QAI Hub 狀態...${NC}"
echo -e "${YELLOW}運行 QAI Hub 狀態檢查...${NC}"
python3 check_qai_hub_status.py > "${REPORT_DIR}/qai_hub_status.txt" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}QAI Hub 狀態檢查完成${NC}"
    echo -e "${YELLOW}報告已保存到 ${REPORT_DIR}/qai_hub_status.txt${NC}"
else
    echo -e "${RED}QAI Hub 狀態檢查失敗${NC}"
    echo -e "${YELLOW}請查看 ${REPORT_DIR}/qai_hub_status.txt 獲取詳細信息${NC}"
fi

# 步驟 3: 執行 API 連接測試
echo -e "\n${BLUE}步驟 3: 測試 QAI Hub API 連接...${NC}"
if [[ "$OS" == "Windows" ]]; then
    echo -e "${YELLOW}運行 Windows 版 API 測試工具...${NC}"
    python3 test_qai_hub_api_windows.py > "${REPORT_DIR}/api_test.txt" 2>&1
else
    echo -e "${YELLOW}運行 macOS/Linux 版 API 測試工具...${NC}"
    python3 test_qai_hub_api.py > "${REPORT_DIR}/api_test.txt" 2>&1
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}API 連接測試成功${NC}"
    echo -e "${YELLOW}測試結果已保存到 ${REPORT_DIR}/api_test.txt${NC}"
else
    echo -e "${RED}API 連接測試失敗${NC}"
    echo -e "${YELLOW}請查看 ${REPORT_DIR}/api_test.txt 獲取詳細信息${NC}"
fi

# 步驟 4: 修復配置 (如果需要)
echo -e "\n${BLUE}步驟 4: 檢查是否需要修復配置...${NC}"

# 嘗試導入 qai_hub 模塊
if python3 -c "import qai_hub" &> /dev/null; then
    echo -e "${GREEN}qai_hub 模塊可以正常導入，配置可能已經正確${NC}"
    NEEDS_FIX=false
else
    echo -e "${YELLOW}qai_hub 模塊無法正常導入，可能需要修復配置${NC}"
    NEEDS_FIX=true
fi

# 根據前面的測試結果判斷是否需要修復
if grep -q "總體狀態: 需要修復" "${REPORT_DIR}/qai_hub_status.txt"; then
    echo -e "${YELLOW}根據狀態檢查，配置需要修復${NC}"
    NEEDS_FIX=true
fi

if [ "$NEEDS_FIX" = true ]; then
    echo -e "${YELLOW}嘗試修復 QAI Hub 配置...${NC}"
    
    if [[ "$OS" == "Windows" ]]; then
        echo -e "${YELLOW}運行 Windows 修復工具...${NC}"
        if [ -f "fix_qai_hub_client.bat" ]; then
            cmd.exe /c fix_qai_hub_client.bat > "${REPORT_DIR}/fix_results.txt" 2>&1
        else
            python3 fix_client_ini_windows.py > "${REPORT_DIR}/fix_results.txt" 2>&1
        fi
    else
        echo -e "${YELLOW}運行 macOS/Linux 修復工具...${NC}"
        if [ -f "fix_qai_hub_macos.sh" ]; then
            chmod +x fix_qai_hub_macos.sh
            ./fix_qai_hub_macos.sh > "${REPORT_DIR}/fix_results.txt" 2>&1
        else
            python3 fix_client_ini_macos.py > "${REPORT_DIR}/fix_results.txt" 2>&1
        fi
    fi
    
    echo -e "${GREEN}修復嘗試完成${NC}"
    echo -e "${YELLOW}修復結果已保存到 ${REPORT_DIR}/fix_results.txt${NC}"
else
    echo -e "${GREEN}配置似乎正常，無需修復${NC}"
fi

# 步驟 5: 檢查 QAI Hub 離線模式
echo -e "\n${BLUE}步驟 5: 測試 QAI Hub 離線模式...${NC}"
if [ -f "qai_hub_demo_offline.py" ]; then
    echo -e "${YELLOW}測試離線演示模式功能...${NC}"
    python3 qai_hub_demo_offline.py --test-all > "${REPORT_DIR}/offline_mode_test.txt" 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}離線模式測試成功${NC}"
        echo -e "${YELLOW}測試結果已保存到 ${REPORT_DIR}/offline_mode_test.txt${NC}"
    else
        echo -e "${RED}離線模式測試失敗${NC}"
        echo -e "${YELLOW}請查看 ${REPORT_DIR}/offline_mode_test.txt 獲取詳細信息${NC}"
    fi
else
    echo -e "${YELLOW}未找到離線演示模式腳本，跳過此步驟${NC}"
fi

# 步驟 6: 總結診斷結果
echo -e "\n${BLUE}步驟 6: 總結診斷結果...${NC}"

# 創建總結報告
SUMMARY_FILE="${REPORT_DIR}/diagnostic_summary.txt"
echo "QAI Hub 診斷彙總報告" > "${SUMMARY_FILE}"
echo "======================" >> "${SUMMARY_FILE}"
echo "時間: $(date)" >> "${SUMMARY_FILE}"
echo "操作系統: ${OS}" >> "${SUMMARY_FILE}"
echo "Python 版本: ${PYTHON_VERSION}" >> "${SUMMARY_FILE}"
echo "" >> "${SUMMARY_FILE}"

# 檢查狀態
if grep -q "總體狀態: 良好" "${REPORT_DIR}/qai_hub_status.txt"; then
    echo "QAI Hub 狀態: 良好 ✓" >> "${SUMMARY_FILE}"
    STATUS_OK=true
else
    echo "QAI Hub 狀態: 需要修復 ✗" >> "${SUMMARY_FILE}"
    STATUS_OK=false
fi

# 檢查 API 測試
if grep -q "全部成功" "${REPORT_DIR}/api_test.txt"; then
    echo "API 連接: 成功 ✓" >> "${SUMMARY_FILE}"
    API_OK=true
else
    echo "API 連接: 失敗 ✗" >> "${SUMMARY_FILE}"
    API_OK=false
fi

# 總體診斷
echo "" >> "${SUMMARY_FILE}"
echo "總體診斷:" >> "${SUMMARY_FILE}"

if [ "$STATUS_OK" = true ] && [ "$API_OK" = true ]; then
    echo "QAI Hub 環境正常，可以正常使用" >> "${SUMMARY_FILE}"
    FINAL_STATUS="PASS"
elif [ -f "${REPORT_DIR}/fix_results.txt" ]; then
    # 檢查修復後的狀態
    echo "已嘗試修復配置，請重新運行診斷工具檢查修復結果" >> "${SUMMARY_FILE}"
    FINAL_STATUS="NEEDS_RECHECK"
else
    echo "QAI Hub 環境存在問題，請參考以下建議:" >> "${SUMMARY_FILE}"
    echo "1. 查看詳細診斷報告 (${REPORT_DIR}/qai_hub_status.txt)" >> "${SUMMARY_FILE}"
    echo "2. 參考故障排除指南 (QAI_HUB_TROUBLESHOOTING.md)" >> "${SUMMARY_FILE}"
    echo "3. 如果問題持續存在，可以使用離線模式 (python qai_hub_demo_offline.py)" >> "${SUMMARY_FILE}"
    FINAL_STATUS="FAIL"
fi

# 顯示總結
if [ "$FINAL_STATUS" = "PASS" ]; then
    echo -e "\n${GREEN}診斷完成: QAI Hub 環境正常，可以正常使用 ✓${NC}"
elif [ "$FINAL_STATUS" = "NEEDS_RECHECK" ]; then
    echo -e "\n${YELLOW}診斷完成: 已嘗試修復配置，請重新運行診斷工具檢查修復結果${NC}"
else
    echo -e "\n${RED}診斷完成: QAI Hub 環境存在問題 ✗${NC}"
    echo -e "${YELLOW}請參考以下建議:${NC}"
    echo -e "1. 查看詳細診斷報告 (${REPORT_DIR}/qai_hub_status.txt)"
    echo -e "2. 參考故障排除指南 (QAI_HUB_TROUBLESHOOTING.md)"
    echo -e "3. 如果問題持續存在，可以使用離線模式 (python qai_hub_demo_offline.py)"
fi

echo -e "\n${BLUE}診斷報告已保存在: ${REPORT_DIR}/diagnostic_summary.txt${NC}"
echo -e "${BLUE}完整的診斷數據已保存在: ${REPORT_DIR}${NC}"

echo -e "\n${BLUE}=========================================================${NC}"
echo -e "${BLUE}            QAI Hub 環境檢查與修復彙總工具完成            ${NC}"
echo -e "${BLUE}=========================================================${NC}\n"

exit 0
