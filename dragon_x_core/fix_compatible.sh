#!/bin/bash
# 跨平台兼容版本修復腳本

# 顯示彩色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Dragon X 跌倒檢測系統 - 修復工具   ${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

echo -e "${YELLOW}檢查跨平台兼容版檔案...${NC}"

# 檢查 main_compatible.py 是否存在
if [ ! -f "main_compatible.py" ]; then
    echo -e "${RED}錯誤: 找不到 main_compatible.py 文件！${NC}"
    exit 1
fi

# 檢查 detectors 目錄是否存在
if [ ! -d "detectors" ]; then
    echo -e "${RED}錯誤: 找不到 detectors 目錄！${NC}"
    exit 1
fi

# 檢查 fall_detector_opencv.py 是否存在
if [ ! -f "detectors/fall_detector_opencv.py" ]; then
    echo -e "${RED}錯誤: 找不到 fall_detector_opencv.py 文件！${NC}"
    exit 1
fi

echo -e "${GREEN}修復導入路徑...${NC}"
sed -i '' 's/from fall_detector_opencv import FallDetector/from detectors.fall_detector_opencv import FallDetector/g' main_compatible.py
sed -i '' 's/from detectors.fall_detector_opencv import OpenCVFallDetector as FallDetector/from detectors.fall_detector_opencv import FallDetector/g' main_compatible.py

echo -e "${YELLOW}檢查 sounddevice 模組...${NC}"
python3 -c "import sounddevice" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${GREEN}安裝 sounddevice 模組...${NC}"
    pip3 install sounddevice
fi

echo -e "${GREEN}修復完成！現在您可以運行跨平台兼容版系統了。${NC}"
echo -e "${YELLOW}請使用 ./start.sh 並選擇選項 3 啟動系統。${NC}"
