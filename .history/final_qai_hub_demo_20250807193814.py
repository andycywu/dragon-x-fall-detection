#!/usr/bin/env python3
"""
🎯 最終官方QAI Hub檢測系統演示
展示完整的老人行為預測與風險評估功能
"""

import cv2
import numpy as np
import os
import logging
import time
from datetime import datetime

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def final_qai_hub_demo():
    """最終QAI Hub演示"""
    print("🎯 === 官方QAI Hub老人行為預測系統 - 最終演示 ===")
    print()
    
    try:
        # 1. 系統初始化
        print("1️⃣ 系統初始化...")
        from elderly_behavior_predictor import ElderlyBehaviorPredictor
        from official_qai_hub_detector import OfficialQAIHubDetector
        
        # 創建檢測器實例
        detector = OfficialQAIHubDetector()
        predictor = ElderlyBehaviorPredictor()
        
        print("   ✅ 系統初始化完成")
        print()
        
        # 2. 測試圖像
        test_images = [
            {'path': 'andy.jpg', 'description': '單人肖像'},
            {'path': 'official_test_image.jpg', 'description': '多人場景'},
            {'path': 'enhanced_test_image.jpg', 'description': '增強測試圖像'}
        ]
        
        for idx, image_info in enumerate(test_images, 1):
            image_path = image_info['path']
            description = image_info['description']
            
            if not os.path.exists(image_path):
                print(f"⏭️ 跳過 {image_path} ({description}) - 檔案不存在")
                continue
                
            print(f"2️⃣.{idx} 處理 {image_path} ({description})")
            
            # 載入圖像
            frame = cv2.imread(image_path)
            if frame is None:
                print(f"   ❌ 無法載入圖像")
                continue
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 3. 官方QAI Hub檢測
            print("   🔍 執行官方QAI Hub檢測...")
            
            # 人臉檢測
            face_result = detector.detect_faces(rgb_frame, raw_output=True)
            print(f"      👤 人臉: {face_result.get('num_faces', 0)}個")
            
            # 姿態檢測
            pose_result = detector.detect_pose(rgb_frame, raw_output=True)
            print(f"      🚶 姿態: {pose_result.get('num_poses', 0)}個")
            
            # 手部檢測
            hand_result = detector.detect_hands(rgb_frame, raw_output=True)
            print(f"      ✋ 手部: {hand_result.get('num_hands', 0)}個")
            
            # 統一檢測
            unified_result = detector.unified_detection(rgb_frame)
            if unified_result.get('success'):
                total = unified_result['total_detections']
                print(f"      📊 統一檢測結果: {total['faces']}臉, {total['poses']}姿態, {total['hands']}手")
            
            # 4. 行為分析
            print("   🧠 執行行為分析...")
            user_id = f"test_user_{idx}"
            interaction_result = predictor.process_user_interaction(user_id, frame)
            
            if interaction_result:
                face_detected = interaction_result.get('face_detected', False)
                pose_analysis = interaction_result.get('pose_analysis', {})
                risk_assessment = interaction_result.get('risk_assessment', {})
                
                print(f"      👁️ 人臉檢測: {'是' if face_detected else '否'}")
                
                if pose_analysis and 'error' not in pose_analysis:
                    print(f"      ⚖️ 平衡評分: {pose_analysis.get('balance_score', 0):.2f}")
                    print(f"      🎯 穩定性評分: {pose_analysis.get('stability_score', 0):.2f}")
                    print(f"      📐 姿態偏差: {pose_analysis.get('posture_deviation', 0):.2f}")
                
                if risk_assessment:
                    risk_score = risk_assessment.get('score', 0)
                    risk_level = risk_assessment.get('level', 'unknown')
                    risk_color = '🟢' if risk_level == 'low' else '🟡' if risk_level == 'medium' else '🔴'
                    print(f"      {risk_color} 風險評估: {risk_score:.2f} ({risk_level})")
                
                if interaction_result.get('alert_triggered', False):
                    print("      🚨 警報觸發!")
            
            # 5. 保存結果
            if face_result.get('success'):
                annotated_face = detector.detect_faces(rgb_frame, raw_output=False)
                if 'annotated_image' in annotated_face:
                    result_filename = f"final_qai_hub_face_{os.path.basename(image_path)}"
                    detector.save_annotated_result(annotated_face['annotated_image'], result_filename)
                    print(f"      💾 人臉檢測結果已保存: {result_filename}")
            
            if pose_result.get('success'):
                annotated_pose = detector.detect_pose(rgb_frame, raw_output=False)
                if 'annotated_image' in annotated_pose:
                    result_filename = f"final_qai_hub_pose_{os.path.basename(image_path)}"
                    detector.save_annotated_result(annotated_pose['annotated_image'], result_filename)
                    print(f"      💾 姿態檢測結果已保存: {result_filename}")
            
            print()
        
        # 6. 系統總結
        print("3️⃣ 系統性能總結")
        print("   ✅ 官方QAI Hub模型集成: MediaPipe Face + Pose + Hand")
        print("   ✅ 實時檢測與分析功能")
        print("   ✅ 行為預測與風險評估")
        print("   ✅ 多模態檢測統一接口")
        print("   ✅ 完全按照Qualcomm AI Hub官方文檔實現")
        print()
        
        print("🎉 === 官方QAI Hub老人行為預測系統演示完成 ===")
        
    except Exception as e:
        logger.error(f"演示執行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_qai_hub_demo()
