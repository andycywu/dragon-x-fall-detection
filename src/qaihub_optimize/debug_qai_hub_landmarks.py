#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度調試 QAI Hub MediaPipe 關鍵點解析
"""

import cv2
import numpy as np
from PIL import Image
import torch

def debug_qai_hub_landmarks():
    """深度調試 QAI Hub 關鍵點結構"""
    try:
        from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
        from qai_hub_models.models.mediapipe_pose.model import MediaPipePose, MODEL_ID, MODEL_ASSET_VERSION
        from qai_hub_models.utils.asset_loaders import CachedWebModelAsset, load_image
        
        # 載入模型和圖像
        pose_model = MediaPipePose.from_pretrained()
        pose_app = MediaPipePoseApp.from_pretrained(pose_model)
        
        official_image_asset = CachedWebModelAsset.from_asset_store(
            MODEL_ID, MODEL_ASSET_VERSION, "pose.jpeg"
        )
        official_image = load_image(official_image_asset)
        
        if isinstance(official_image, Image.Image):
            official_image = np.array(official_image)
            official_image = cv2.cvtColor(official_image, cv2.COLOR_RGB2BGR)
        
        rgb_image = cv2.cvtColor(official_image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        print("🔍 QAI Hub MediaPipe 深度調試")
        print("=" * 50)
        
        # 獲取原始結果
        result = pose_app.predict_landmarks_from_image(pil_image, raw_output=True)
        batched_selected_boxes, batched_selected_keypoints, batched_roi_4corners, landmarks_out = result
        
        print(f"整體結果: {len(result)} 個元素")
        print(f"Boxes: {len(batched_selected_boxes)} batches")
        print(f"Keypoints: {len(batched_selected_keypoints)} batches")  
        print(f"ROI corners: {len(batched_roi_4corners)} batches")
        print(f"Landmarks out: {len(landmarks_out)} tensors")
        
        # 詳細檢查 landmarks_out
        print("\n📊 詳細檢查 landmarks_out:")
        for i, landmark_tensor in enumerate(landmarks_out):
            print(f"\nLandmark tensor {i}:")
            print(f"  類型: {type(landmark_tensor)}")
            if hasattr(landmark_tensor, 'shape'):
                print(f"  形狀: {landmark_tensor.shape}")
                print(f"  元素數量: {landmark_tensor.numel()}")
                print(f"  數據類型: {landmark_tensor.dtype}")
                
                # 檢查數據範圍
                if landmark_tensor.numel() > 0:
                    print(f"  最小值: {landmark_tensor.min().item()}")
                    print(f"  最大值: {landmark_tensor.max().item()}")
                    
                    # 嘗試不同的解析方式
                    if len(landmark_tensor.shape) == 3:
                        batch, num_landmarks, coords = landmark_tensor.shape
                        print(f"  解釋為: [batch={batch}, landmarks={num_landmarks}, coords={coords}]")
                        
                        if batch > 0 and num_landmarks > 0:
                            first_batch = landmark_tensor[0]
                            print(f"  第一個batch形狀: {first_batch.shape}")
                            
                            # 顯示前5個關鍵點
                            print(f"  前5個關鍵點:")
                            for j in range(min(5, num_landmarks)):
                                coords_data = first_batch[j]
                                print(f"    點{j}: {coords_data.tolist()}")
                    
                    elif len(landmark_tensor.shape) == 2:
                        num_landmarks, coords = landmark_tensor.shape
                        print(f"  解釋為: [landmarks={num_landmarks}, coords={coords}]")
                        
                        # 顯示前5個關鍵點
                        print(f"  前5個關鍵點:")
                        for j in range(min(5, num_landmarks)):
                            coords_data = landmark_tensor[j]
                            print(f"    點{j}: {coords_data.tolist()}")
        
        # 嘗試解析關鍵點
        print("\n🎯 嘗試解析關鍵點:")
        
        if landmarks_out and len(landmarks_out) >= 1:
            pose_landmarks_tensor = landmarks_out[0]
            height, width = official_image.shape[:2]
            
            print(f"使用第一個tensor: {pose_landmarks_tensor.shape}")
            
            pose_landmarks = []
            
            if len(pose_landmarks_tensor.shape) == 3:
                # [batch, landmarks, coords]
                landmarks_data = pose_landmarks_tensor[0]  # 第一個batch
            elif len(pose_landmarks_tensor.shape) == 2:
                # [landmarks, coords]
                landmarks_data = pose_landmarks_tensor
            else:
                print(f"❌ 無法處理的形狀: {pose_landmarks_tensor.shape}")
                return
            
            num_landmarks = landmarks_data.shape[0]
            num_coords = landmarks_data.shape[1]
            
            print(f"關鍵點數量: {num_landmarks}")
            print(f"座標維度: {num_coords}")
            
            # 嘗試解析每個關鍵點
            for i in range(min(num_landmarks, 33)):  # MediaPipe 最多33個
                coords = landmarks_data[i]
                
                if num_coords >= 2:
                    x, y = float(coords[0]), float(coords[1])
                    
                    # 檢查是否為歸一化座標
                    if 0 <= x <= 1 and 0 <= y <= 1:
                        img_x = x * width
                        img_y = y * height
                        
                        # 檢查可見性
                        if num_coords >= 4:
                            visibility = float(coords[3])
                            if visibility > 0.1:
                                pose_landmarks.append((img_x, img_y))
                                if i < 5:  # 顯示前5個
                                    print(f"  點{i}: ({x:.3f}, {y:.3f}) -> ({img_x:.1f}, {img_y:.1f}), vis={visibility:.3f}")
                        else:
                            pose_landmarks.append((img_x, img_y))
                            if i < 5:  # 顯示前5個
                                print(f"  點{i}: ({x:.3f}, {y:.3f}) -> ({img_x:.1f}, {img_y:.1f})")
            
            print(f"\n✅ 成功解析 {len(pose_landmarks)} 個關鍵點")
            
            if pose_landmarks:
                # 繪製結果
                result_image = official_image.copy()
                for i, (x, y) in enumerate(pose_landmarks):
                    cv2.circle(result_image, (int(x), int(y)), 8, (0, 255, 0), -1)
                    cv2.putText(result_image, str(i), (int(x)+10, int(y)-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imwrite("qai_hub_debug_result.jpg", result_image)
                print("💾 保存調試結果: qai_hub_debug_result.jpg")
        
    except Exception as e:
        print(f"❌ 調試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_qai_hub_landmarks()
