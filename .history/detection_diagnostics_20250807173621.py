#!/usr/bin/env python3
"""
檢測系統診斷工具
專門用於排查各檢測方法的具體問題
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
import time
import traceback

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from completely_fixed_detector import CompletelyFixedHackathonDetector

def test_detection_methods_live():
    """實時測試各檢測方法的具體問題"""
    
    print("=" * 80)
    print("🔍 檢測系統實時診斷")
    print("=" * 80)
    
    # 初始化檢測器
    print("🚀 初始化檢測器...")
    detector = CompletelyFixedHackathonDetector()
    
    # 開啟攝像頭
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法打開攝像頭")
        return
    
    print("✅ 攝像頭已開啟")
    
    # 測試各檢測方法
    methods = ["QAI_Hub_MediaPipe", "Standard_MediaPipe", "OpenCV_Fallback", "Simulation_Demo"]
    method_stats = {method: {"success": 0, "total": 0, "errors": []} for method in methods}
    
    print("\n🧪 開始實時診斷測試...")
    print("說明：每種方法測試10幀，按 'q' 提前退出")
    
    for method in methods:
        print(f"\n{'='*20} 測試 {method} {'='*20}")
        
        # 切換檢測方法
        detector.switch_detection_method(method)
        
        frame_count = 0
        max_frames = 10
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                print("❌ 無法讀取攝像頭畫面")
                break
            
            method_stats[method]["total"] += 1
            
            try:
                # 測試檢測
                start_time = time.time()
                success, landmarks, info = detector.detect_pose(frame)
                detection_time = time.time() - start_time
                
                if success and len(landmarks) > 0:
                    method_stats[method]["success"] += 1
                    status = "✅"
                    result_info = f"檢測到 {len(landmarks)} 個關鍵點"
                else:
                    status = "❌"
                    result_info = f"檢測失敗: {info}"
                    method_stats[method]["errors"].append(info)
                
                print(f"  幀 {frame_count+1:2d}/10: {status} {result_info} ({detection_time:.3f}s)")
                
                # 顯示檢測結果
                frame_copy = frame.copy()
                if success and landmarks:
                    # 簡單繪製關鍵點
                    for i, (x, y) in enumerate(landmarks):
                        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                            cv2.circle(frame_copy, (int(x), int(y)), 3, (0, 255, 0), -1)
                
                # 添加標題
                cv2.putText(frame_copy, f"Testing: {method}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame_copy, f"Frame: {frame_count+1}/10", (10, 70), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.putText(frame_copy, result_info, (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow("Detection Test", frame_copy)
                
                # 檢查退出
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    print("🛑 用戶提前退出")
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                
            except Exception as e:
                status = "💥"
                error_msg = str(e)[:50]
                print(f"  幀 {frame_count+1:2d}/10: {status} 異常: {error_msg}")
                method_stats[method]["errors"].append(f"Exception: {error_msg}")
                
                # 打印詳細錯誤
                print(f"    詳細錯誤: {traceback.format_exc()}")
            
            frame_count += 1
    
    cap.release()
    cv2.destroyAllWindows()
    
    # 生成診斷報告
    print("\n" + "=" * 80)
    print("📊 診斷報告")
    print("=" * 80)
    
    for method in methods:
        stats = method_stats[method]
        total = stats["total"]
        success = stats["success"]
        success_rate = (success / max(total, 1)) * 100
        
        print(f"\n🔍 {method}:")
        print(f"   成功率: {success_rate:.1f}% ({success}/{total})")
        
        if success_rate == 100:
            print("   狀態: ✅ 完全正常")
        elif success_rate >= 70:
            print("   狀態: ⚠️ 基本正常，偶有問題")
        elif success_rate >= 30:
            print("   狀態: 🔧 需要修復")
        else:
            print("   狀態: ❌ 嚴重故障")
        
        # 顯示錯誤信息
        if stats["errors"]:
            print("   常見錯誤:")
            error_counts = {}
            for error in stats["errors"]:
                error_counts[error] = error_counts.get(error, 0) + 1
            
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"     • {error} (出現 {count} 次)")
    
    print(f"\n{'='*80}")
    print("🎯 診斷完成！")

def test_individual_method(method_name):
    """單獨測試特定檢測方法"""
    print(f"🔍 單獨診斷檢測方法: {method_name}")
    
    detector = CompletelyFixedHackathonDetector()
    detector.switch_detection_method(method_name)
    
    # 使用測試圖像
    test_image_path = "completely_fixed_test_image.jpg"
    if Path(test_image_path).exists():
        image = cv2.imread(test_image_path)
        print(f"📸 使用測試圖像: {test_image_path}")
    else:
        print("❌ 測試圖像不存在，使用攝像頭...")
        cap = cv2.VideoCapture(0)
        ret, image = cap.read()
        cap.release()
        if not ret:
            print("❌ 無法獲取攝像頭畫面")
            return
    
    print(f"🧪 測試 {method_name}...")
    
    try:
        start_time = time.time()
        success, landmarks, info = detector.detect_pose(image)
        detection_time = time.time() - start_time
        
        print(f"結果: {'✅ 成功' if success else '❌ 失敗'}")
        print(f"關鍵點數量: {len(landmarks) if landmarks else 0}")
        print(f"檢測時間: {detection_time:.3f}秒")
        print(f"詳細信息: {info}")
        
        if success and landmarks:
            print("前5個關鍵點座標:")
            for i, (x, y) in enumerate(landmarks[:5]):
                print(f"  點{i}: ({x:.2f}, {y:.2f})")
        
    except Exception as e:
        print(f"❌ 異常: {e}")
        print(f"詳細錯誤:\n{traceback.format_exc()}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 測試特定方法
        method = sys.argv[1]
        if method in ["QAI_Hub_MediaPipe", "Standard_MediaPipe", "OpenCV_Fallback", "Simulation_Demo"]:
            test_individual_method(method)
        else:
            print("❌ 無效的檢測方法")
            print("可用方法: QAI_Hub_MediaPipe, Standard_MediaPipe, OpenCV_Fallback, Simulation_Demo")
    else:
        # 實時診斷所有方法
        test_detection_methods_live()
