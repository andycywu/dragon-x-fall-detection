#!/usr/bin/env python3
"""
測試整合了官方QAI Hub的elderly_behavior_predictor系統
"""

import cv2
import numpy as np
import os
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_elderly_behavior_system():
    """測試老人行為預測系統"""
    try:
        print("=== 測試整合官方QAI Hub的老人行為預測系統 ===")
        
        # 導入系統
        from elderly_behavior_predictor import ElderlyBehaviorPredictor
        
        # 初始化系統
        print("1. 初始化系統...")
        predictor = ElderlyBehaviorPredictor()
        
        # 測試圖像路徑
        test_images = [
            'andy.jpg',
            'official_test_image.jpg'
        ]
        
        for image_path in test_images:
            if not os.path.exists(image_path):
                print(f"跳過 {image_path} (檔案不存在)")
                continue
                
            print(f"\n--- 測試圖像: {image_path} ---")
            
            # 載入圖像
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"無法載入 {image_path}")
                continue
            
            # 2. 用戶識別
            print("2. 用戶識別...")
            user_id = predictor.identify_user(frame)
            if user_id:
                print(f"   識別到用戶: {user_id}")
            else:
                print("   未識別到已知用戶，使用默認ID")
                user_id = "test_user"
            
            # 3. 處理用戶互動
            print("3. 處理用戶互動...")
            interaction_result = predictor.process_user_interaction(user_id, frame)
            
            print(f"   人臉檢測: {interaction_result.get('face_detected', False)}")
            print(f"   處理資訊: {interaction_result.get('processing_info', {})}")
            
            # 顯示姿態分析結果
            pose_analysis = interaction_result.get('pose_analysis', {})
            if pose_analysis and 'error' not in pose_analysis:
                print(f"   平衡評分: {pose_analysis.get('balance_score', 0):.2f}")
                print(f"   穩定性評分: {pose_analysis.get('stability_score', 0):.2f}")
                print(f"   姿態偏差: {pose_analysis.get('posture_deviation', 0):.2f}")
            else:
                print(f"   姿態分析: {pose_analysis}")
            
            # 顯示風險評估
            risk_assessment = interaction_result.get('risk_assessment', {})
            if risk_assessment:
                print(f"   風險評分: {risk_assessment.get('score', 0):.2f}")
                print(f"   風險等級: {risk_assessment.get('level', 'unknown')}")
                
            # 檢查警報
            if interaction_result.get('alert_triggered', False):
                print("   ⚠️ 警報觸發！")
        
        print("\n=== 測試完成 ===")
        
    except Exception as e:
        logger.error(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_elderly_behavior_system()
