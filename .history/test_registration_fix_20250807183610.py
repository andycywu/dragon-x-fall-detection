#!/usr/bin/env python3
"""
測試改進後的人臉註冊功能
"""

import sys
import os
sys.path.append('/Users/andycyw/mvp_fall_detection_starter')

from elderly_behavior_predictor import ElderlyBehaviorPredictor

def test_registration():
    """測試人臉註冊"""
    print("🔄 初始化系統...")
    predictor = ElderlyBehaviorPredictor()
    
    # 測試您的照片
    image_path = "/var/folders/0z/28nbzz893ybf73x7j9vqzg3w0000gn/T/tmpu5g674wc/andy.jpg"
    
    print(f"\n📷 測試註冊照片: {image_path}")
    
    # 嘗試註冊
    result = predictor.register_user(
        user_id="andy_001",
        name="Andy",
        image_path=image_path,
        profile_info={
            "age": 30,
            "health_status": "良好",
            "emergency_contact": "未設定"
        }
    )
    
    if result:
        print(f"\n🎉 註冊成功！")
        print(f"📊 系統狀態:")
        print(f"  - 已註冊用戶數: {len(predictor.known_faces)}")
        print(f"  - 用戶資料: {predictor.user_profiles}")
    else:
        print(f"\n❌ 註冊失敗")
    
    return result

if __name__ == "__main__":
    print("🧪 測試改進後的人臉註冊功能")
    print("=" * 50)
    
    success = test_registration()
    
    print(f"\n📋 測試結果: {'✅ 成功' if success else '❌ 失敗'}")
