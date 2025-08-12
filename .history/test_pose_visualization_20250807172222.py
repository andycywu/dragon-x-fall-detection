#!/usr/bin/env python3
"""
測試姿態可視化功能
驗證所有四種檢測方法的骨架顯示
"""

import cv2
import numpy as np
from pathlib import Path
import sys

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from completely_fixed_detector import CompletelyFixedHackathonDetector

def test_pose_visualization():
    """測試姿態可視化功能"""
    
    print("=" * 80)
    print("🧪 測試姿態可視化功能")
    print("=" * 80)
    
    # 初始化檢測器
    detector = CompletelyFixedHackathonDetector()
    
    # 載入測試圖像
    test_image_path = "assets/test_images/person_standing.jpg"
    if not Path(test_image_path).exists():
        print(f"⚠️ 測試圖像不存在: {test_image_path}")
        print("使用攝像頭進行測試...")
        
        # 使用攝像頭
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ 無法打開攝像頭")
            return
        
        print("📹 使用攝像頭測試姿態可視化...")
        print("控制說明:")
        print("  - 按 '1' 測試 QAI Hub MediaPipe")
        print("  - 按 '2' 測試 Standard MediaPipe") 
        print("  - 按 '3' 測試 OpenCV Fallback")
        print("  - 按 '4' 測試 Simulation Demo")
        print("  - 按 'q' 退出")
        
        current_method = "QAI_Hub_MediaPipe"
        method_names = {
            "1": "QAI_Hub_MediaPipe",
            "2": "Standard_MediaPipe",
            "3": "OpenCV_Fallback", 
            "4": "Simulation_Demo"
        }
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 檢測姿態
            result = detector.detect_pose(frame, method=current_method)
            
            if result['success'] and result['landmarks']:
                # 繪製姿態骨架
                frame = draw_pose_skeleton(frame, result['landmarks'], current_method)
                
                # 顯示檢測信息
                info_text = f"Method: {current_method} | Keypoints: {len(result['landmarks'])}"
                cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                status_text = f"Status: {result.get('fall_risk', 'Unknown')}"
                cv2.putText(frame, status_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            else:
                # 顯示檢測失敗
                cv2.putText(frame, f"Detection Failed: {current_method}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # 顯示幀
            cv2.imshow("Pose Visualization Test", frame)
            
            # 處理按鍵
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif chr(key) in method_names:
                current_method = method_names[chr(key)]
                print(f"🔄 切換到檢測方法: {current_method}")
        
        cap.release()
        cv2.destroyAllWindows()
    
    else:
        # 使用靜態圖像測試
        image = cv2.imread(test_image_path)
        if image is None:
            print(f"❌ 無法載入圖像: {test_image_path}")
            return
        
        print(f"📸 使用靜態圖像測試: {test_image_path}")
        
        # 測試所有檢測方法
        methods = ["QAI_Hub_MediaPipe", "Standard_MediaPipe", "OpenCV_Fallback", "Simulation_Demo"]
        
        for i, method in enumerate(methods):
            print(f"\n🧪 測試方法 {i+1}/4: {method}")
            
            result = detector.detect_pose(image.copy(), method=method)
            
            if result['success'] and result['landmarks']:
                print(f"  ✅ 檢測成功，關鍵點數量: {len(result['landmarks'])}")
                
                # 繪製姿態骨架
                vis_image = draw_pose_skeleton(image.copy(), result['landmarks'], method)
                
                # 添加標題
                title = f"{method} - {len(result['landmarks'])} keypoints"
                cv2.putText(vis_image, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # 顯示結果
                cv2.imshow(f"Pose Test - {method}", vis_image)
                print(f"  💡 按任意鍵繼續下一個測試...")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                print(f"  ❌ 檢測失敗: {result.get('error', 'Unknown error')}")
    
    print("\n🎉 姿態可視化測試完成！")

def draw_pose_skeleton(frame: np.ndarray, landmarks: list, method: str) -> np.ndarray:
    """
    繪製姿態骨架
    根據不同的檢測方法使用對應的連接方式
    """
    if not landmarks:
        return frame
    
    # MediaPipe 姿態連接 (33個關鍵點)
    MEDIAPIPE_POSE_CONNECTIONS = [
        # 臉部輪廓
        (0, 1), (1, 2), (2, 3), (3, 7),
        (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10),
        # 軀幹
        (11, 12), (11, 13), (12, 14), (13, 15), (14, 16),
        (11, 23), (12, 24), (23, 24),
        # 手臂
        (15, 17), (15, 19), (15, 21), (16, 18), (16, 20), (16, 22),
        (17, 19), (18, 20), (19, 21), (20, 22),
        # 腿部
        (23, 25), (24, 26), (25, 27), (26, 28),
        (27, 29), (28, 30), (29, 31), (30, 32),
        (27, 31), (28, 32)
    ]
    
    # OpenCV/COCO 姿態連接 (25個關鍵點)
    OPENCV_POSE_CONNECTIONS = [
        # 軀幹
        (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
        (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
        # 手臂
        (1, 0), (0, 14), (14, 16), (0, 15), (15, 17),
        # 腿部
        (8, 9), (9, 10), (11, 12), (12, 13),
        (10, 20), (10, 21), (13, 22), (13, 23)
    ]
    
    # 選擇連接方式
    if method in ["QAI_Hub_MediaPipe", "Standard_MediaPipe"]:
        connections = MEDIAPIPE_POSE_CONNECTIONS
        point_color = (0, 255, 0)  # 綠色
        line_color = (255, 255, 0)  # 青色
    elif method == "OpenCV_Fallback":
        connections = OPENCV_POSE_CONNECTIONS
        point_color = (255, 0, 0)  # 藍色
        line_color = (0, 255, 255)  # 黃色
    else:  # Simulation_Demo
        connections = MEDIAPIPE_POSE_CONNECTIONS
        point_color = (255, 0, 255)  # 紫色
        line_color = (0, 255, 255)  # 黃色
    
    h, w = frame.shape[:2]
    
    # 繪製連接線
    for connection in connections:
        if connection[0] < len(landmarks) and connection[1] < len(landmarks):
            pt1 = landmarks[connection[0]]
            pt2 = landmarks[connection[1]]
            
            # 轉換坐標
            if isinstance(pt1, tuple) and len(pt1) >= 2:
                x1, y1 = int(pt1[0] * w), int(pt1[1] * h)
                x2, y2 = int(pt2[0] * w), int(pt2[1] * h)
                
                # 檢查坐標有效性
                if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                    cv2.line(frame, (x1, y1), (x2, y2), line_color, 2)
    
    # 繪製關鍵點
    for i, landmark in enumerate(landmarks):
        if isinstance(landmark, tuple) and len(landmark) >= 2:
            x, y = int(landmark[0] * w), int(landmark[1] * h)
            
            if 0 <= x < w and 0 <= y < h:
                cv2.circle(frame, (x, y), 4, point_color, -1)
                cv2.circle(frame, (x, y), 4, (255, 255, 255), 1)
                
                # 可選：顯示關鍵點編號
                cv2.putText(frame, str(i), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    return frame

if __name__ == "__main__":
    test_pose_visualization()
