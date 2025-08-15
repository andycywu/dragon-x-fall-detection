#!/usr/bin/env python3
"""
🧪 QAI Hub Live Demo 測試腳本
驗證所有功能正常運行
"""

import os
import sys
import time
import requests
import cv2
import numpy as np
from PIL import Image
import tempfile

def test_systems_loading():
    """測試系統載入"""
    print("🔬 測試系統載入...")
    
    try:
        from official_qai_hub_detector import OfficialQAIHubDetector
        from elderly_behavior_predictor import ElderlyBehaviorPredictor
        
        detector = OfficialQAIHubDetector()
        predictor = ElderlyBehaviorPredictor()
        
        print("✅ QAI Hub檢測系統載入成功")
        print("✅ 老人行為預測系統載入成功")
        return detector, predictor
        
    except Exception as e:
        print(f"❌ 系統載入失敗: {e}")
        return None, None

def test_image_processing(detector, predictor):
    """測試圖像處理功能"""
    print("\n🖼️ 測試圖像處理功能...")
    
    test_images = ['andy.jpg', 'official_test_image.jpg']
    
    for img_path in test_images:
        if os.path.exists(img_path):
            print(f"📷 測試圖像: {img_path}")
            
            try:
                # 載入圖像
                image = cv2.imread(img_path)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # 執行檢測
                unified_result = detector.unified_detection(rgb_image)
                print(f"   🔍 統一檢測完成: {unified_result.get('total_detections', {})}")
                
                # 行為分析
                user_id = f"test_user_{int(time.time())}"
                interaction_result = predictor.process_user_interaction(user_id, image)
                
                if interaction_result and 'risk_assessment' in interaction_result:
                    risk = interaction_result['risk_assessment']
                    print(f"   🚨 風險評估: {risk.get('level', 'unknown')} (評分: {risk.get('score', 0):.2f})")
                
                print(f"   ✅ {img_path} 處理成功")
                
            except Exception as e:
                print(f"   ❌ {img_path} 處理失敗: {e}")
        else:
            print(f"⏭️ 跳過: {img_path} (文件不存在)")

def test_streamlit_app():
    """測試Streamlit應用是否運行"""
    print("\n📊 測試Streamlit應用...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit應用正常運行")
            print("🌐 訪問地址: http://localhost:8501")
            return True
        else:
            print(f"❌ Streamlit應用響應異常: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Streamlit應用連接失敗: {e}")
        print("💡 請先啟動Streamlit: python demo_launcher.py --mode streamlit")
        return False

def test_web_demo_functionality():
    """測試Web演示功能"""
    print("\n🌐 測試Web演示組件...")
    
    try:
        # 測試導入Web演示模塊
        from qai_hub_web_demo import QAIHubWebDemo
        
        demo = QAIHubWebDemo()
        print("✅ Web演示系統初始化成功")
        
        # 測試基礎功能
        if demo.detector and demo.predictor:
            print("✅ 檢測系統整合正常")
        else:
            print("❌ 檢測系統整合失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ Web演示測試失敗: {e}")
        return False

def test_camera_availability():
    """測試攝影機可用性"""
    print("\n📹 測試攝影機可用性...")
    
    try:
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ 攝影機可用且正常工作")
                print(f"   攝影機解析度: {frame.shape[1]}x{frame.shape[0]}")
            else:
                print("❌ 攝影機無法獲取幀")
            cap.release()
        else:
            print("❌ 無法開啟攝影機")
            
    except Exception as e:
        print(f"❌ 攝影機測試失敗: {e}")

def generate_test_report():
    """生成測試報告"""
    print("\n📋 生成測試報告...")
    
    detector, predictor = test_systems_loading()
    
    if detector and predictor:
        test_image_processing(detector, predictor)
    
    streamlit_ok = test_streamlit_app()
    web_demo_ok = test_web_demo_functionality()
    
    test_camera_availability()
    
    print("\n" + "="*60)
    print("📊 測試總結報告")
    print("="*60)
    
    print(f"🧠 QAI Hub檢測系統: {'✅ 正常' if detector else '❌ 異常'}")
    print(f"👨‍⚕️ 行為預測系統: {'✅ 正常' if predictor else '❌ 異常'}")
    print(f"📊 Streamlit應用: {'✅ 運行中' if streamlit_ok else '❌ 未運行'}")
    print(f"🌐 Web演示功能: {'✅ 正常' if web_demo_ok else '❌ 異常'}")
    
    print("\n🚀 啟動建議:")
    if not streamlit_ok:
        print("   1. 啟動Streamlit: python demo_launcher.py --mode streamlit")
    print("   2. 啟動Web演示: python demo_launcher.py --mode web")
    print("   3. 選擇模式: python demo_launcher.py --mode both")
    
    print("\n🌐 訪問地址:")
    print("   📊 Streamlit: http://localhost:8501")
    print("   🌐 Web Demo: http://localhost:8080")

def main():
    """主函數"""
    print("🧪 QAI Hub Live Demo 系統測試")
    print("="*60)
    
    # 檢查必要文件
    required_files = [
        'official_qai_hub_detector.py',
        'elderly_behavior_predictor.py',
        'qai_hub_streamlit_demo.py',
        'qai_hub_web_demo.py',
        'demo_launcher.py'
    ]
    
    print("📁 檢查必要文件...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ 缺少必要文件: {missing_files}")
        print("請確保所有文件都在當前目錄中")
        return
    
    # 執行測試
    generate_test_report()

if __name__ == "__main__":
    main()
