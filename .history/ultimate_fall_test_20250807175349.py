#!/usr/bin/env python3
"""
🏆 Ultimate Fall Detection System Test
完全增強版跌倒檢測系統終極測試
"""

import cv2
import numpy as np
import time
from completely_fixed_detector import CompletelyFixedHackathonDetector
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_methods():
    """測試所有檢測方法的跌倒檢測能力"""
    print("=" * 80)
    print("🏆 Ultimate Fall Detection System Test")
    print("=" * 80)
    
    detector = CompletelyFixedHackathonDetector()
    methods = ["QAI_Hub_MediaPipe", "Standard_MediaPipe", "OpenCV_Fallback", "Simulation_Demo"]
    
    # 初始化攝像頭
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法開啟攝像頭")
        return
    
    print(f"✅ 攝像頭已開啟，準備測試 {len(methods)} 種檢測方法...")
    print("📋 測試說明：")
    print("   - 每種方法測試30秒")
    print("   - 嘗試不同的姿勢：站立、坐下、躺下、跌倒模擬")
    print("   - 按 'q' 退出，按 's' 跳過當前方法")
    print()
    
    results = {}
    
    for method in methods:
        print(f"\n🧪 測試方法: {method}")
        print("-" * 50)
        
        detector.switch_detection_method(method)
        
        frame_count = 0
        fall_detected_count = 0
        normal_detected_count = 0
        start_time = time.time()
        fps_list = []
        
        while time.time() - start_time < 30:  # 測試30秒
            ret, frame = cap.read()
            if not ret:
                print("❌ 無法讀取攝像頭幀")
                break
            
            frame_start_time = time.time()
            
            # 檢測姿勢
            success, landmarks, status_info = detector.detect_pose(frame)
            
            # 判斷是否跌倒（簡單的跌倒檢測邏輯）
            is_fall = False
            confidence = 0.0
            
            if success and landmarks:
                # 簡單的跌倒檢測：檢查身體關鍵點的垂直分佈
                try:
                    # 獲取頭部和下身關鍵點
                    head_points = landmarks[:11]  # 頭部區域
                    body_points = landmarks[11:23]  # 身體區域
                    leg_points = landmarks[23:33]  # 腿部區域
                    
                    if len(landmarks) >= 33:
                        head_y = np.mean([p[1] for p in head_points if p and len(p) >= 2])
                        leg_y = np.mean([p[1] for p in leg_points if p and len(p) >= 2])
                        
                        # 如果頭部和腿部的垂直距離太小，可能是跌倒
                        vertical_distance = abs(leg_y - head_y)
                        frame_height = frame.shape[0]
                        
                        if vertical_distance < frame_height * 0.3:  # 小於30%的幀高度
                            is_fall = True
                            confidence = 0.8
                        else:
                            confidence = 0.9
                            
                except Exception as e:
                    confidence = 0.5
            
            frame_end_time = time.time()
            fps = 1.0 / (frame_end_time - frame_start_time)
            fps_list.append(fps)
            
            frame_count += 1
            
            if is_fall:
                fall_detected_count += 1
                status_color = (0, 0, 255)  # 紅色
                status_text = f"⚠️  FALL DETECTED! ({confidence:.2f})"
            else:
                normal_detected_count += 1
                status_color = (0, 255, 0)  # 綠色
                status_text = f"✅ Normal ({confidence:.2f})"
            
            # 顯示信息
            cv2.putText(frame, f"Method: {method}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, status_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Time: {time.time() - start_time:.1f}s", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Falls: {fall_detected_count}", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Normal: {normal_detected_count}", (10, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, status_info, (10, 210), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Ultimate Fall Detection Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n⏹️  測試被用戶中斷")
                cap.release()
                cv2.destroyAllWindows()
                return
            elif key == ord('s'):
                print(f"\n⏭️  跳過 {method}")
                break
        
        # 計算統計
        avg_fps = np.mean(fps_list) if fps_list else 0
        total_time = time.time() - start_time
        
        results[method] = {
            'frames': frame_count,
            'falls': fall_detected_count,
            'normal': normal_detected_count,
            'avg_fps': avg_fps,
            'time': total_time,
            'fall_rate': fall_detected_count / frame_count if frame_count > 0 else 0
        }
        
        print(f"   📊 統計: {frame_count} 幀, {fall_detected_count} 次跌倒檢測, 平均 FPS: {avg_fps:.1f}")
    
    cap.release()
    cv2.destroyAllWindows()
    
    # 顯示最終報告
    print("\n" + "=" * 80)
    print("📊 Ultimate Test Report")
    print("=" * 80)
    
    for method, stats in results.items():
        print(f"\n🔍 {method}:")
        print(f"   總幀數: {stats['frames']}")
        print(f"   跌倒檢測: {stats['falls']} 次 ({stats['fall_rate']*100:.1f}%)")
        print(f"   正常檢測: {stats['normal']} 次")
        print(f"   平均 FPS: {stats['avg_fps']:.1f}")
        print(f"   測試時間: {stats['time']:.1f} 秒")
        
        # 評估性能
        if stats['avg_fps'] >= 15:
            fps_status = "🚀 優秀"
        elif stats['avg_fps'] >= 10:
            fps_status = "✅ 良好"
        elif stats['avg_fps'] >= 5:
            fps_status = "⚠️  可接受"
        else:
            fps_status = "❌ 需優化"
        
        print(f"   性能評級: {fps_status}")
    
    # 推薦最佳方法
    best_method = max(results.keys(), key=lambda m: results[m]['avg_fps'])
    print(f"\n🏆 推薦方法: {best_method} (平均 FPS: {results[best_method]['avg_fps']:.1f})")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    test_all_methods()
