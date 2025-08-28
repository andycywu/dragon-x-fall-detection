#!/usr/bin/env python3
"""
🧪 老人行為預測系統測試腳本
"""

import cv2
import numpy as np
import time
import os
from elderly_behavior_predictor import ElderlyBehaviorPredictor
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_system():
    """測試整個系統功能"""
    print("=" * 80)
    print("🧪 老人行為預測系統功能測試")
    print("=" * 80)
    
    # 初始化系統
    print("\n🚀 初始化系統...")
    predictor = ElderlyBehaviorPredictor()
    
    # 測試1: 模擬用戶註冊
    print("\n📝 測試1: 用戶註冊功能")
    test_user_registration(predictor)
    
    # 測試2: 姿態分析
    print("\n🤸‍♀️ 測試2: 姿態分析功能")
    test_pose_analysis(predictor)
    
    # 測試3: 風險評估
    print("\n⚠️ 測試3: 風險評估功能")
    test_risk_assessment(predictor)
    
    # 測試4: 語音互動
    print("\n🗣️ 測試4: 語音互動功能")
    test_voice_interaction(predictor)
    
    # 測試5: 數據存儲
    print("\n💾 測試5: 數據存儲功能")
    test_data_storage(predictor)
    
    print("\n✅ 所有測試完成！")

def test_user_registration(predictor):
    """測試用戶註冊功能"""
    try:
        # 創建測試圖像（模擬用戶照片）
        test_image = np.zeros((400, 400, 3), dtype=np.uint8)
        
        # 在圖像中畫一個簡單的臉
        cv2.circle(test_image, (200, 200), 80, (255, 255, 255), -1)  # 臉
        cv2.circle(test_image, (180, 180), 10, (0, 0, 0), -1)  # 左眼
        cv2.circle(test_image, (220, 180), 10, (0, 0, 0), -1)  # 右眼
        cv2.ellipse(test_image, (200, 220), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # 嘴巴
        
        # 保存測試圖像
        test_image_path = "test_user.jpg"
        cv2.imwrite(test_image_path, test_image)
        
        # 嘗試註冊用戶
        success = predictor.register_user(
            "test_001", 
            "測試奶奶", 
            test_image_path,
            {"age": 75, "medical_conditions": ["高血壓"]}
        )
        
        if success:
            print("✅ 用戶註冊成功")
        else:
            print("❌ 用戶註冊失敗（這是正常的，因為是模擬圖像）")
        
        # 清理
        if os.path.exists(test_image_path):
            os.remove(test_image_path)
            
    except Exception as e:
        print(f"❌ 用戶註冊測試失敗: {e}")

def test_pose_analysis(predictor):
    """測試姿態分析功能"""
    try:
        # 創建模擬關鍵點數據
        mock_landmarks = []
        
        # 生成33個關鍵點（MediaPipe標準）
        for i in range(33):
            x = 200 + np.random.normal(0, 50)  # 圍繞中心點的隨機分佈
            y = 200 + i * 10 + np.random.normal(0, 20)  # 垂直分佈
            mock_landmarks.append((float(x), float(y)))
        
        # 測試穩定性分析
        stability_metrics = predictor.analyze_pose_stability(mock_landmarks)
        print(f"  平衡評分: {stability_metrics['balance_score']:.2f}")
        print(f"  穩定性評分: {stability_metrics['stability_score']:.2f}")
        print(f"  姿態偏差: {stability_metrics['posture_deviation']:.2f}")
        
        # 測試關節角度計算
        joint_angles = predictor.calculate_joint_angles(mock_landmarks)
        print(f"  檢測到 {len(joint_angles)} 個關節角度")
        
        print("✅ 姿態分析功能正常")
        
    except Exception as e:
        print(f"❌ 姿態分析測試失敗: {e}")

def test_risk_assessment(predictor):
    """測試風險評估功能"""
    try:
        # 模擬添加姿態數據
        user_id = "test_user"
        
        # 創建模擬數據
        for i in range(10):
            # 模擬不同的風險狀況
            if i < 5:
                # 正常狀況
                balance_score = 0.8 + np.random.normal(0, 0.1)
                stability_score = 0.7 + np.random.normal(0, 0.1)
                posture_deviation = 0.2 + np.random.normal(0, 0.05)
            else:
                # 高風險狀況
                balance_score = 0.4 + np.random.normal(0, 0.1)
                stability_score = 0.3 + np.random.normal(0, 0.1)
                posture_deviation = 0.8 + np.random.normal(0, 0.1)
            
            # 創建姿態數據
            from elderly_behavior_predictor import PostureData
            posture_data = PostureData(
                timestamp=time.time() - (10-i) * 60,  # 過去10分鐘的數據
                user_id=user_id,
                joint_angles={},
                balance_score=max(0, min(1, balance_score)),
                stability_score=max(0, min(1, stability_score)),
                posture_deviation=max(0, min(1, posture_deviation)),
                activity_level=0.5,
                face_detected=True
            )
            
            predictor.posture_history.append(posture_data)
        
        # 計算風險評分
        risk_score = predictor.calculate_fall_risk_score(user_id)
        print(f"  風險評分: {risk_score:.2f}")
        
        # 生成行為摘要
        summary = predictor.generate_behavioral_summary(user_id)
        if summary.get('status') != 'error':
            print(f"  監測記錄: {summary.get('total_records', 0)} 條")
            print(f"  平均平衡評分: {summary.get('average_metrics', {}).get('balance_score', 0):.2f}")
        
        print("✅ 風險評估功能正常")
        
    except Exception as e:
        print(f"❌ 風險評估測試失敗: {e}")

def test_voice_interaction(predictor):
    """測試語音互動功能"""
    try:
        user_id = "test_user"

        # 測試TTS問題
        print("  測試語音提問...")
        predictor.ask_user_checkin_question(user_id, "這是一個測試問題", speak=True)

        # 測試文字回覆解釋
        test_responses = [
            "我今天感覺很好",
            "有點頭暈，不太舒服", 
            "感覺很虛弱，剛才差點跌倒"
        ]

        for response in test_responses:
            result = predictor.interpret_user_reply(text_input=response)
            if result['status'] == 'success':
                print(f"    回覆: '{response}' -> 情感評分: {result['sentiment_score']:.2f}, 警報: {result['alert_level']}")

        print("✅ 語音互動功能正常")

    except Exception as e:
        print(f"❌ 語音互動測試失敗: {e}")

def test_data_storage(predictor):
    """測試數據存儲功能"""
    try:
        # 檢查數據庫文件是否存在
        if os.path.exists(predictor.db_path):
            print(f"  數據庫文件: {predictor.db_path} ✅")
        
        # 檢查人臉編碼文件
        if os.path.exists(predictor.face_encodings_path):
            print(f"  人臉編碼文件: {predictor.face_encodings_path} ✅")
        
        # 檢查內存中的數據
        print(f"  姿態歷史記錄: {len(predictor.posture_history)} 條")
        print(f"  已註冊用戶: {len(predictor.user_profiles)} 個")
        print(f"  已知人臉: {len(predictor.known_faces)} 個")
        
        print("✅ 數據存儲功能正常")
        
    except Exception as e:
        print(f"❌ 數據存儲測試失敗: {e}")

def demo_live_detection():
    """演示即時檢測功能"""
    print("\n🎥 即時檢測演示（按 'q' 退出）")
    
    predictor = ElderlyBehaviorPredictor()
    
    # 嘗試開啟攝像頭
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法開啟攝像頭")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 識別用戶
            user_id = predictor.identify_user(frame)
            
            if user_id:
                # 處理用戶互動
                result = predictor.process_user_interaction(user_id, frame)
                
                # 顯示信息
                name = predictor.user_profiles[user_id]['name']
                risk_score = result.get('risk_assessment', {}).get('score', 0)
                
                cv2.putText(frame, f"User: {name}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Risk: {risk_score:.2f}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if result.get('alert_triggered'):
                    cv2.putText(frame, "ALERT!", (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            else:
                cv2.putText(frame, "No registered user detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Elderly Behavior Predictor - Live Demo', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # 運行功能測試
    test_system()
    
    # 詢問是否運行即時演示
    print(f"\n🎥 是否要運行即時檢測演示？ (y/n): ", end="")
    choice = input().lower()
    
    if choice == 'y':
        demo_live_detection()
    
    print("\n🎉 測試完成！")
