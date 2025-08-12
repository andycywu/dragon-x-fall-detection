#!/usr/bin/env python3
"""
Snapdragon X Elite Performance Benchmark
比較不同加速方式的性能表現
"""

import os
import sys
import cv2
import time
import numpy as np
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def benchmark_fall_detection(image_path, accelerator=None, iterations=5):
    """運行性能基準測試"""
    print(f"正在測試圖像: {image_path}")
    print(f"加速器: {accelerator if accelerator else '預設'}")
    print(f"迭代次數: {iterations}")
    
    # 加載測試圖像
    image = cv2.imread(image_path)
    if image is None:
        print(f"無法加載圖像: {image_path}")
        return
    
    print(f"圖像尺寸: {image.shape}")
    
    # 設定環境變數以控制加速
    if accelerator:
        if accelerator == "hexagon_npu":
            os.environ['ENABLE_QAI_ACCELERATION'] = 'true'
            os.environ['QAI_HUB_ACCELERATOR'] = 'hexagon_npu'
            os.environ['QAI_OPTIMIZATION_LEVEL'] = 'performance'
        elif accelerator == "cpu":
            if 'ENABLE_QAI_ACCELERATION' in os.environ:
                del os.environ['ENABLE_QAI_ACCELERATION']
            if 'QAI_HUB_ACCELERATOR' in os.environ:
                del os.environ['QAI_HUB_ACCELERATOR']
    
    try:
        # 載入UnifiedAIDetector (檢測平台和可用的加速器)
        print("初始化AI檢測器...")
        from unified_ai_detector_ascii import UnifiedAIDetector
        detector = UnifiedAIDetector()
        print(f"檢測到平台: {detector.platform}")
        print(f"可用加速器: {detector.accelerators}")
        
        # 載入fall detector
        print("初始化跌倒檢測器...")
        from fall_detector import FallDetector
        fall_detector = FallDetector()
        
        # 進行基準測試
        print("\n開始性能測試...")
        times = []
        
        for i in range(iterations):
            print(f"迭代 {i+1}/{iterations}...")
            
            # 測量處理時間
            start_time = time.time()
            result = fall_detector.detect_fall_from_frame(image)
            end_time = time.time()
            
            process_time = end_time - start_time
            times.append(process_time)
            
            if result is None:
                print(f"  沒有檢測到姿勢，處理時間: {process_time:.4f}秒")
            else:
                is_falling, confidence = result
                status = "跌倒" if is_falling else "正常"
                print(f"  結果: {status}, 置信度: {confidence:.2f}, 處理時間: {process_time:.4f}秒")
        
        # 計算統計數據
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("\n測試結果摘要:")
        print(f"平台: {detector.platform}")
        print(f"加速器: {accelerator if accelerator else '預設'}")
        print(f"平均處理時間: {avg_time:.4f}秒")
        print(f"最小處理時間: {min_time:.4f}秒")
        print(f"最大處理時間: {max_time:.4f}秒")
        print(f"每秒處理幀數 (FPS): {1/avg_time:.2f}")
        
        return {
            "platform": detector.platform,
            "accelerator": accelerator,
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "fps": 1/avg_time
        }
        
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_accelerators(image_path, iterations=5):
    """比較不同加速器的性能"""
    print("=" * 70)
    print("Snapdragon X Elite 加速器性能比較")
    print("=" * 70)
    
    results = {}
    
    # 測試CPU (無加速)
    print("\n=== 測試 CPU (無加速) ===")
    results["cpu"] = benchmark_fall_detection(image_path, "cpu", iterations)
    
    # 測試Hexagon NPU
    print("\n=== 測試 Hexagon NPU 加速 ===")
    results["hexagon_npu"] = benchmark_fall_detection(image_path, "hexagon_npu", iterations)
    
    # 結果比較
    print("\n" + "=" * 70)
    print("性能比較結果")
    print("=" * 70)
    
    if "cpu" in results and "hexagon_npu" in results:
        cpu_time = results["cpu"]["average_time"]
        npu_time = results["hexagon_npu"]["average_time"]
        speedup = cpu_time / npu_time
        
        print(f"CPU 平均處理時間: {cpu_time:.4f}秒 ({1/cpu_time:.2f} FPS)")
        print(f"Hexagon NPU 平均處理時間: {npu_time:.4f}秒 ({1/npu_time:.2f} FPS)")
        print(f"加速比: {speedup:.2f}x")
        
        if speedup > 1:
            print(f"Hexagon NPU 加速使處理速度提高了 {(speedup-1)*100:.1f}%")
        else:
            print(f"Hexagon NPU 沒有提供加速，性能降低了 {(1-speedup)*100:.1f}%")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Snapdragon X Elite 性能基準測試")
    parser.add_argument("--image", default="test_images/andy.jpg", help="測試圖像路徑")
    parser.add_argument("--iterations", type=int, default=5, help="每次測試的迭代次數")
    parser.add_argument("--mode", choices=["compare", "single"], default="compare", 
                        help="測試模式: compare (比較不同加速器) 或 single (單一加速器)")
    parser.add_argument("--accelerator", choices=["hexagon_npu", "cpu", "none"], default=None,
                        help="在single模式下使用的加速器")
    
    args = parser.parse_args()
    
    if args.mode == "compare":
        compare_accelerators(args.image, args.iterations)
    else:
        benchmark_fall_detection(args.image, args.accelerator, args.iterations)

if __name__ == "__main__":
    main()
