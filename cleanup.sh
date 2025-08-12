#!/bin/bash
# 清理腳本 - 移除非必要檔案
# 使用前請確保已經備份所有檔案

# 顯示彩色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}警告：此腳本將移除非必要的檔案。請確保已備份重要資料。${NC}"
echo -e "${YELLOW}此操作無法撤銷！請確認您已了解將要執行的操作。${NC}"
echo -e "按下 Ctrl+C 取消，或按 Enter 繼續..."
read

# 確認用戶理解
echo -e "${YELLOW}確認：精簡版專案已經位於 dragon_x_core/ 目錄中。${NC}"
echo -e "${YELLOW}此腳本將僅清理當前目錄，不會影響精簡版專案。${NC}"
read -p "是否繼續? (y/n): " CONFIRM
if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
    echo -e "${BLUE}操作已取消${NC}"
    exit 0
fi

# 創建備份
echo -e "${GREEN}創建最終備份...${NC}"
BACKUP_DIR="../mvp_fall_detection_final_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r ./* "$BACKUP_DIR/"
echo -e "${GREEN}備份已創建: $BACKUP_DIR${NC}"

# 保護核心文件
echo -e "${GREEN}檢查核心檔案安全性...${NC}"
if [ ! -d "dragon_x_core" ]; then
    echo -e "${RED}錯誤: 未找到 dragon_x_core 目錄，無法繼續！${NC}"
    echo -e "${YELLOW}請確保您已創建精簡版專案，並運行在正確的目錄中。${NC}"
    exit 1
fi

# 確認用戶知道將被刪除的文件
echo -e "${YELLOW}以下類型的檔案將被移除:${NC}"
echo -e " - 除錯和測試檔案 (debug_*.py, test_*.py, 等)"
echo -e " - 完全固定和改進版本 (*completely_fixed*.py, 等)"
echo -e " - 模擬和假資料檔案 (*simulate*.py, 等)"
echo -e " - 測試圖像 (*.jpg, *.HEIC)"
echo -e " - 黑客松相關檔案 (hackathon_*.py, HACKATHON_*.md)"
echo -e " - 多餘的報告和文檔 (*_REPORT.md, *_GUIDE.md)"

read -p "最後確認，是否繼續? (y/n): " FINAL_CONFIRM
if [[ $FINAL_CONFIRM != "y" && $FINAL_CONFIRM != "Y" ]]; then
    echo -e "${BLUE}操作已取消${NC}"
    exit 0
fi

# 刪除除錯和測試檔案
echo -e "${BLUE}移除除錯和測試檔案...${NC}"
find . -name "debug_*.py" -o -name "test_*.py" -o -name "quick_test.py" -o -name "simple_test.py" -o -name "camera_test.py" -delete

# 刪除固定和改進版本
echo -e "${BLUE}移除固定和改進版本...${NC}"
find . -name "*completely_fixed*.py" -o -name "*fixed_hackathon*.py" -o -name "*improved_hackathon*.py" -delete

# 刪除模擬檔案
echo -e "${BLUE}移除模擬檔案...${NC}"
find . -name "*simulate*.py" -o -name "*simulation*.py" -delete

# 刪除測試圖像
echo -e "${BLUE}移除測試圖像...${NC}"
find . -name "*.jpg" -o -name "*.HEIC" -delete

# 刪除黑客松相關檔案
echo -e "${BLUE}移除黑客松相關檔案...${NC}"
find . -name "hackathon_*.py" -o -name "HACKATHON_*.md" -delete

# 刪除多餘的報告和文檔
echo -e "${BLUE}整理報告和文檔...${NC}"
find . -name "*_REPORT.md" ! -name "FINAL_REPORT.md" -delete
find . -name "*_GUIDE.md" ! -name "DEPLOYMENT_GUIDE.md" ! -name "QDC_CONNECTION_GUIDE.md" -delete

echo -e "${GREEN}清理完成！專案已經過精簡。${NC}"
echo -e "${GREEN}精簡版專案在: dragon_x_core/${NC}"
echo -e "${YELLOW}建議：檢查並驗證精簡版專案的功能是否正常。${NC}"
