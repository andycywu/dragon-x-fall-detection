#!/usr/bin/env python3
"""
Snapdragon X Elite Fall Detection System Documentation
"""

import os
import sys
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def main():
    """Main documentation function"""
    print_header("Snapdragon X Elite Fall Detection System")
    
    print("本文檔提供了基於Snapdragon X Elite平台的跌倒檢測系統的使用說明。")
    print("本系統利用了Hexagon NPU硬體加速，可以實現高效率的即時跌倒檢測。\n")
    
    print_header("系統需求")
    
    print("硬體要求:")
    print("- Snapdragon X Elite處理器")
    print("- 至少8GB記憶體")
    print("- 網路攝影機\n")
    
    print("軟體要求:")
    print("- Windows作業系統")
    print("- Python 3.8+")
    print("- OpenCV 4.x")
    print("- QAI Hub API")
    print("- MediaPipe")
    print("- ONNX Runtime\n")
    
    print_header("檔案說明")
    
    print("主要檔案:")
    print("- fall_detector.py: 核心跌倒檢測邏輯")
    print("- unified_ai_detector_ascii.py: 統一AI檢測器，支援多種後端")
    print("- snapdragon_optimized_demo.py: 優化後的圖像處理腳本")
    print("- snapdragon_performance_benchmark.py: 性能基準測試腳本")
    print("- snapdragon_video_demo.py: 視頻處理腳本")
    print("- snapdragon_realtime_demo.py: 即時相機檢測腳本\n")
    
    print_header("使用說明")
    
    print("1. 即時跌倒檢測 (使用相機):")
    print("   python snapdragon_realtime_demo.py [選項]")
    print("   選項:")
    print("   --camera CAMERA         相機索引 (預設: 0)")
    print("   --output OUTPUT         輸出視頻檔案路徑 (可選)")
    print("   --duration DURATION     最長運行時間(秒) (可選)")
    print("   --disable-acceleration  禁用硬體加速")
    print("   --resolution RESOLUTION 相機解析度，格式為WIDTHxHEIGHT (例如: 640x480)\n")
    
    print("2. 處理視頻檔案:")
    print("   python snapdragon_video_demo.py [選項]")
    print("   選項:")
    print("   --input INPUT           輸入視頻檔案路徑")
    print("   --output OUTPUT         輸出視頻檔案路徑 (可選)")
    print("   --disable-acceleration  禁用硬體加速\n")
    
    print("3. 性能基準測試:")
    print("   python snapdragon_performance_benchmark_ascii.py [選項]")
    print("   選項:")
    print("   --image IMAGE           測試圖像路徑 (預設: test_images/andy.jpg)")
    print("   --iterations ITERATIONS 每次測試的迭代次數 (預設: 5)")
    print("   --mode {compare,single} 測試模式 (預設: compare)")
    print("   --accelerator {hexagon_npu,cpu,none} 在single模式下使用的加速器\n")
    
    print_header("性能數據")
    
    print("在Snapdragon X Elite上的測試結果:")
    print("- 使用Hexagon NPU加速: 平均處理時間 0.0555秒 (18.02 FPS)")
    print("- 僅使用CPU: 平均處理時間 0.0571秒 (17.50 FPS)")
    print("- 加速比: 1.03x (提升約3%)\n")
    
    print("在即時相機模式下，系統可達到約22 FPS的處理速度，")
    print("足以滿足即時跌倒檢測的需求。\n")
    
    print_header("注意事項")
    
    print("1. 首次運行時，系統會下載必要的模型檔案，可能需要一些時間。")
    print("2. 使用相機時，請確保環境光線充足，以提高檢測準確性。")
    print("3. 跌倒檢測演示在人體姿勢清晰可見時效果最佳。")
    print("4. 若檢測結果不穩定，可嘗試調整相機位置或改善光線條件。")
    print("5. 若要使用硬體加速，必須確保QAI Hub配置正確。\n")
    
    print_header("聯繫方式")
    
    print("如有任何問題或建議，請聯繫項目維護者。")
    print("项目GitHub: https://github.com/andycywu/dragon-x-fall-detection")
    print("\n")

if __name__ == "__main__":
    main()
