#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QAI Hub MediaPipe 調試和修復工具
解決解析結果和檢測問題
"""

import cv2
import numpy as np
from PIL import Image
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_qai_hub_detailed():
    """詳細調試 QAI Hub MediaPipe"""
    print("🔍 詳細調試 QAI Hub MediaPipe...")
    
    try:
        from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
        from qai_hub_models.models.mediapipe_pose.model import MediaPipePose
        
        # 載入模型
        print("📥 載入模型...")
        pose_model = MediaPipePose.from_pretrained()
        pose_app = MediaPipePoseApp.from_pretrained(pose_model)
        print("✅ 模型載入完成")
        
        # 測試不同類型的圖像
        test_images = []
        
        # 1. 創建一個更真實的人形圖像
        human_image = create_realistic_human_image()
        test_images.append(("realistic_human", human_image))
        
        # 2. 使用官方測試圖像（如果可用）
        try:
            from qai_hub_models.models.mediapipe_pose.model import MODEL_ID, MODEL_ASSET_VERSION
            from qai_hub_models.utils.asset_loaders import CachedWebModelAsset, load_image
            
            official_image_asset = CachedWebModelAsset.from_asset_store(
                MODEL_ID, MODEL_ASSET_VERSION, "pose.jpeg"
            )
            official_image = load_image(official_image_asset)
            if isinstance(official_image, Image.Image):
                official_image = np.array(official_image)
            test_images.append(("official_test", official_image))
            print("✅ 載入官方測試圖像")
        except Exception as e:
            print(f"⚠️ 無法載入官方測試圖像: {e}")
        
        # 3. 創建簡單的黑白人形
        simple_image = create_simple_human_silhouette()
        test_images.append(("simple_silhouette", simple_image))
        
        # 測試每個圖像
        for image_name, test_image in test_images:
            print(f"\n🧪 測試圖像: {image_name}")
            print("-" * 40)
            
            try:
                # 確保圖像格式正確
                if test_image.dtype != np.uint8:
                    test_image = (test_image * 255).astype(np.uint8)
                
                if len(test_image.shape) == 3 and test_image.shape[2] == 3:
                    # BGR to RGB
                    rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
                else:
                    rgb_image = test_image
                
                pil_image = Image.fromarray(rgb_image)
                print(f"  圖像尺寸: {pil_image.size}")
                print(f"  圖像模式: {pil_image.mode}")
                
                # 測試 raw_output=True
                print("  測試 raw_output=True...")
                result_raw = pose_app.predict_landmarks_from_image(pil_image, raw_output=True)
                print(f"  Raw 結果類型: {type(result_raw)}")
                print(f"  Raw 結果長度: {len(result_raw) if hasattr(result_raw, '__len__') else 'N/A'}")
                
                if isinstance(result_raw, tuple) and len(result_raw) >= 4:
                    batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, *landmarks_out = result_raw
                    
                    print(f"  Boxes: {len(batched_selected_boxes)} batches")
                    print(f"  Keypoints: {len(batched_selected_keypoints)} batches")
                    print(f"  ROI corners: {len(batched_roi_4corners)} batches")
                    print(f"  Landmarks out: {len(landmarks_out)} outputs")
                    
                    # 檢查每個 batch 的內容
                    for i, (boxes, keypoints, roi, landmarks) in enumerate(zip(
                        batched_selected_boxes, batched_selected_keypoints, 
                        batched_roi_4corners, landmarks_out if landmarks_out else [None]
                    )):
                        print(f"    Batch {i}:")
                        print(f"      Boxes shape: {boxes.shape if hasattr(boxes, 'shape') else type(boxes)}")
                        print(f"      Keypoints shape: {keypoints.shape if hasattr(keypoints, 'shape') else type(keypoints)}")
                        print(f"      ROI shape: {roi.shape if hasattr(roi, 'shape') else type(roi)}")
                        if landmarks is not None:
                            print(f"      Landmarks type: {type(landmarks)}")
                            if hasattr(landmarks, 'shape'):
                                print(f"      Landmarks shape: {landmarks.shape}")
                            elif isinstance(landmarks, list):
                                print(f"      Landmarks list length: {len(landmarks)}")
                                if landmarks:
                                    print(f"      First landmark type: {type(landmarks[0])}")
                                    if hasattr(landmarks[0], 'shape'):
                                        print(f"      First landmark shape: {landmarks[0].shape}")
                
                # 測試 raw_output=False
                print("  測試 raw_output=False...")
                result_normal = pose_app.predict_landmarks_from_image(pil_image, raw_output=False)
                print(f"  Normal 結果類型: {type(result_normal)}")
                if isinstance(result_normal, list):
                    print(f"  Normal 結果長度: {len(result_normal)}")
                    if result_normal:
                        print(f"  第一個結果類型: {type(result_normal[0])}")
                        if hasattr(result_normal[0], 'shape'):
                            print(f"  第一個結果形狀: {result_normal[0].shape}")
                
                print(f"  ✅ {image_name} 測試完成")
                
                # 保存測試圖像以供檢查
                cv2.imwrite(f"debug_{image_name}.jpg", test_image)
                
            except Exception as e:
                print(f"  ❌ {image_name} 測試失敗: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"❌ 整體測試失敗: {e}")
        import traceback
        traceback.print_exc()

def create_realistic_human_image():
    """創建一個更真實的人形圖像"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 背景設為灰色
    img[:] = (128, 128, 128)
    
    center_x, center_y = 320, 240
    
    # 頭部 (橢圓形)
    cv2.ellipse(img, (center_x, center_y - 120), (25, 35), 0, 0, 360, (220, 180, 150), -1)
    
    # 脖子
    cv2.rectangle(img, (center_x - 8, center_y - 85), (center_x + 8, center_y - 70), (220, 180, 150), -1)
    
    # 身體 (矩形)
    cv2.rectangle(img, (center_x - 30, center_y - 70), (center_x + 30, center_y + 80), (100, 150, 200), -1)
    
    # 手臂
    cv2.rectangle(img, (center_x - 70, center_y - 50), (center_x - 30, center_y + 20), (220, 180, 150), -1)
    cv2.rectangle(img, (center_x + 30, center_y - 50), (center_x + 70, center_y + 20), (220, 180, 150), -1)
    
    # 前臂
    cv2.rectangle(img, (center_x - 75, center_y + 20), (center_x - 55, center_y + 70), (220, 180, 150), -1)
    cv2.rectangle(img, (center_x + 55, center_y + 20), (center_x + 75, center_y + 70), (220, 180, 150), -1)
    
    # 腿部
    cv2.rectangle(img, (center_x - 20, center_y + 80), (center_x - 5, center_y + 160), (50, 100, 150), -1)
    cv2.rectangle(img, (center_x + 5, center_y + 80), (center_x + 20, center_y + 160), (50, 100, 150), -1)
    
    # 小腿
    cv2.rectangle(img, (center_x - 18, center_y + 160), (center_x - 7, center_y + 220), (220, 180, 150), -1)
    cv2.rectangle(img, (center_x + 7, center_y + 160), (center_x + 18, center_y + 220), (220, 180, 150), -1)
    
    # 腳
    cv2.ellipse(img, (center_x - 12, center_y + 230), (15, 8), 0, 0, 360, (0, 0, 0), -1)
    cv2.ellipse(img, (center_x + 12, center_y + 230), (15, 8), 0, 0, 360, (0, 0, 0), -1)
    
    return img

def create_simple_human_silhouette():
    """創建簡單的人形輪廓"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 白色背景
    img[:] = (255, 255, 255)
    
    center_x, center_y = 320, 240
    
    # 黑色人形輪廓
    # 頭
    cv2.circle(img, (center_x, center_y - 100), 30, (0, 0, 0), -1)
    
    # 身體
    cv2.rectangle(img, (center_x - 25, center_y - 70), (center_x + 25, center_y + 50), (0, 0, 0), -1)
    
    # 手臂
    cv2.rectangle(img, (center_x - 60, center_y - 50), (center_x - 25, center_y + 10), (0, 0, 0), -1)
    cv2.rectangle(img, (center_x + 25, center_y - 50), (center_x + 60, center_y + 10), (0, 0, 0), -1)
    
    # 腿
    cv2.rectangle(img, (center_x - 15, center_y + 50), (center_x - 5, center_y + 150), (0, 0, 0), -1)
    cv2.rectangle(img, (center_x + 5, center_y + 50), (center_x + 15, center_y + 150), (0, 0, 0), -1)
    
    return img

def test_standard_mediapipe():
    """測試標準 MediaPipe"""
    print("\n🎯 測試標準 MediaPipe...")
    
    try:
        import mediapipe as mp
        
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        
        pose = mp_pose.Pose(
            static_image_mode=True,  # 改為 True 用於圖像檢測
            model_complexity=2,      # 提高模型複雜度
            smooth_landmarks=True,
            min_detection_confidence=0.3,  # 降低檢測閾值
            min_tracking_confidence=0.3    # 降低追蹤閾值
        )
        
        print("✅ 標準 MediaPipe 初始化成功")
        
        # 測試圖像
        test_images = [
            ("realistic_human", create_realistic_human_image()),
            ("simple_silhouette", create_simple_human_silhouette())
        ]
        
        for image_name, test_image in test_images:
            print(f"\n  測試圖像: {image_name}")
            
            try:
                # 轉換為 RGB
                rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
                
                # 處理圖像
                results = pose.process(rgb_image)
                
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    print(f"    ✅ 檢測到 {len(landmarks)} 個關鍵點")
                    
                    # 檢查關鍵點質量
                    visible_landmarks = sum(1 for lm in landmarks if lm.visibility > 0.5)
                    print(f"    可見關鍵點: {visible_landmarks}/{len(landmarks)}")
                    
                    # 繪製結果
                    annotated_image = test_image.copy()
                    mp_drawing.draw_landmarks(
                        annotated_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                    )
                    cv2.imwrite(f"mediapipe_result_{image_name}.jpg", annotated_image)
                    print(f"    保存結果圖像: mediapipe_result_{image_name}.jpg")
                    
                else:
                    print(f"    ❌ 未檢測到姿態")
                    
            except Exception as e:
                print(f"    ❌ 處理 {image_name} 時出錯: {e}")
        
        pose.close()
        
    except Exception as e:
        print(f"❌ 標準 MediaPipe 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_qai_hub_detailed()
    test_standard_mediapipe()
