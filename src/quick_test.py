#!/usr/bin/env python3
"""
快速測試老人行為預測系統的核心功能
"""

import os
import sys
import cv2
import numpy as np
from elderly_behavior_predictor import ElderlyBehaviorPredictor

def quick_test():
    """快速測試系統核心功能"""
    print("🚀 老人行為預測系統 - 快速測試")
    print("=" * 50)
    
    try:
        # 初始化系統
        print("🔧 初始化系統...")
        predictor = ElderlyBehaviorPredictor()
        print("✅ 系統初始化成功")
        
        # 測試姿態分析
        print("\n🤸‍♀️ 測試姿態分析...")
        # 創建模擬關鍵點
        mock_landmarks = [(200 + i*10, 200 + i*5) for i in range(33)]
        
        stability = predictor.analyze_pose_stability(mock_landmarks)
        print(f"  平衡評分: {stability['balance_score']:.2f}")
        print(f"  穩定性評分: {stability['stability_score']:.2f}")
        print("✅ 姿態分析正常")
        
        # 測試風險評估
        print("\n⚠️ 測試風險評估...")
        risk_score = predictor.calculate_fall_risk_score("test_user")
        print(f"  風險評分: {risk_score:.2f}")
        print("✅ 風險評估正常")
        
        # 測試語音功能
        print("\n🗣️ 測試語音功能...")
        question = predictor.ask_user_checkin_question()
        print(f"  測試問題: {question}")
        print("✅ 語音功能正常")
        
        print("\n🎉 所有核心功能測試通過！")
        
        # 詢問是否運行攝像頭演示
        response = input("\n📸 是否測試攝像頭功能？(y/n): ")
        if response.lower() == 'y':
            test_camera(predictor)
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_camera(predictor):
    """測試攝像頭功能"""
    print("\n📸 攝像頭測試（按 'q' 退出）")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法開啟攝像頭")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 顯示幀
            cv2.putText(frame, "Elder Care System", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Elder Care Camera Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ 攝像頭測試完成")

if __name__ == "__main__":
    quick_test()
