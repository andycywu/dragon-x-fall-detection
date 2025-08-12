#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QAI Hub MediaPipe 輸出格式調試器
用於理解 QAI Hub MediaPipe 的實際輸出結構
"""

import cv2
import numpy as np
from PIL import Image
import torch

from qai_hub_models.models.mediapipe_pose.app import MediaPipePoseApp
from qai_hub_models.models.mediapipe_pose.model import MediaPipePose

def debug_qai_hub_output():
    """調試 QAI Hub MediaPipe 的輸出格式"""
    print("🔍 調試 QAI Hub MediaPipe 輸出格式...")
    
    # 載入模型
    print("📥 載入模型...")
    pose_model = MediaPipePose.from_pretrained()
    pose_app = MediaPipePoseApp.from_pretrained(pose_model)
    print("✅ 模型載入完成")
    
    # 創建測試圖像（一個簡單的白色背景）
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
    pil_image = Image.fromarray(test_image)
    
    print("\n🧪 測試 1: 檢查非 raw_output 模式...")
    try:
        result_normal = pose_app.predict_landmarks_from_image(pil_image, raw_output=False)
        print(f"normal 模式結果類型: {type(result_normal)}")
        if isinstance(result_normal, (list, tuple)):
            print(f"normal 模式結果長度: {len(result_normal)}")
            for i, item in enumerate(result_normal):
                print(f"  項目 {i}: 類型={type(item)}, 形狀={(item.shape if hasattr(item, 'shape') else '無形狀')}")
    except Exception as e:
        print(f"normal 模式錯誤: {e}")
    
    print("\n🧪 測試 2: 檢查 raw_output 模式...")
    try:
        result_raw = pose_app.predict_landmarks_from_image(pil_image, raw_output=True)
        print(f"raw 模式結果類型: {type(result_raw)}")
        if isinstance(result_raw, (list, tuple)):
            print(f"raw 模式結果長度: {len(result_raw)}")
            for i, item in enumerate(result_raw):
                print(f"  項目 {i}: 類型={type(item)}")
                if isinstance(item, list):
                    print(f"    列表長度: {len(item)}")
                    for j, subitem in enumerate(item):
                        print(f"      子項目 {j}: 類型={type(subitem)}, 形狀={(subitem.shape if hasattr(subitem, 'shape') else '無形狀')}")
                        if hasattr(subitem, 'shape') and len(subitem.shape) > 0:
                            print(f"        內容預覽: {subitem}")
                elif hasattr(item, 'shape'):
                    print(f"    形狀: {item.shape}")
                    if len(item.shape) > 0:
                        print(f"    內容預覽: {item}")
    except Exception as e:
        print(f"raw 模式錯誤: {e}")
    
    # 嘗試使用一個包含人的測試圖像
    print("\n🧪 測試 3: 使用真實人像測試...")
    try:
        # 創建一個簡單的人形輪廓圖像
        person_image = create_simple_person_image()
        pil_person = Image.fromarray(person_image)
        
        result_person = pose_app.predict_landmarks_from_image(pil_person, raw_output=True)
        print(f"人像測試結果類型: {type(result_person)}")
        if isinstance(result_person, (list, tuple)):
            print(f"人像測試結果長度: {len(result_person)}")
            for i, item in enumerate(result_person):
                print(f"  項目 {i}: 類型={type(item)}")
                if isinstance(item, list):
                    print(f"    列表長度: {len(item)}")
                    if len(item) > 0:
                        print(f"      第一個元素類型: {type(item[0])}")
                        if hasattr(item[0], 'shape'):
                            print(f"      第一個元素形狀: {item[0].shape}")
    except Exception as e:
        print(f"人像測試錯誤: {e}")

def create_simple_person_image():
    """創建一個簡單的人形輪廓圖像用於測試"""
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 畫一個簡單的人形輪廓
    center_x, center_y = 320, 240
    
    # 頭部（圓形）
    cv2.circle(image, (center_x, center_y - 100), 30, (255, 255, 255), -1)
    
    # 身體（矩形）
    cv2.rectangle(image, (center_x - 25, center_y - 70), (center_x + 25, center_y + 50), (255, 255, 255), -1)
    
    # 手臂
    cv2.rectangle(image, (center_x - 60, center_y - 50), (center_x - 25, center_y), (255, 255, 255), -1)
    cv2.rectangle(image, (center_x + 25, center_y - 50), (center_x + 60, center_y), (255, 255, 255), -1)
    
    # 腿部
    cv2.rectangle(image, (center_x - 15, center_y + 50), (center_x - 5, center_y + 120), (255, 255, 255), -1)
    cv2.rectangle(image, (center_x + 5, center_y + 50), (center_x + 15, center_y + 120), (255, 255, 255), -1)
    
    return image

if __name__ == "__main__":
    debug_qai_hub_output()
