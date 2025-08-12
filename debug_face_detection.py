#!/usr/bin/env python3
"""
人臉檢測診斷工具
"""

import cv2
import face_recognition
import os

def debug_face_detection(image_path):
    """診斷指定圖片的人臉檢測"""
    print(f"🔍 診斷圖片: {image_path}")
    
    # 檢查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在: {image_path}")
        return False
    
    try:
        # 使用OpenCV載入圖片
        cv_image = cv2.imread(image_path)
        if cv_image is None:
            print(f"❌ OpenCV無法載入圖片")
            return False
        
        print(f"✅ OpenCV載入成功")
        print(f"   圖片尺寸: {cv_image.shape}")
        
        # 使用face_recognition載入圖片
        fr_image = face_recognition.load_image_file(image_path)
        print(f"✅ face_recognition載入成功")
        print(f"   圖片尺寸: {fr_image.shape}")
        
        # 檢測人臉位置
        face_locations = face_recognition.face_locations(fr_image)
        print(f"📍 檢測到 {len(face_locations)} 個人臉位置")
        
        if face_locations:
            for i, (top, right, bottom, left) in enumerate(face_locations):
                print(f"   人臉 {i+1}: top={top}, right={right}, bottom={bottom}, left={left}")
        
        # 生成人臉編碼
        face_encodings = face_recognition.face_encodings(fr_image)
        print(f"🔢 生成了 {len(face_encodings)} 個人臉編碼")
        
        if face_encodings:
            for i, encoding in enumerate(face_encodings):
                print(f"   編碼 {i+1}: 長度={len(encoding)}")
        
        # 嘗試不同的人臉檢測模型
        print("\n🔄 嘗試不同檢測模型:")
        
        # HOG模型 (預設)
        face_locations_hog = face_recognition.face_locations(fr_image, model="hog")
        print(f"   HOG模型: {len(face_locations_hog)} 個人臉")
        
        # CNN模型 (更準確但較慢)
        try:
            face_locations_cnn = face_recognition.face_locations(fr_image, model="cnn")
            print(f"   CNN模型: {len(face_locations_cnn)} 個人臉")
        except Exception as e:
            print(f"   CNN模型失敗: {e}")
        
        # 如果檢測到人臉，顯示結果
        if face_locations:
            # 在圖片上標記人臉
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(cv_image, (left, top), (right, bottom), (0, 255, 0), 2)
            
            # 顯示結果
            cv2.imshow('Face Detection Result', cv_image)
            print("\n👁️ 顯示結果圖片，按任意鍵關閉...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            return True
        else:
            print("❌ 未檢測到任何人臉")
            return False
            
    except Exception as e:
        print(f"❌ 處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_images():
    """測試項目中的樣本圖片"""
    test_images = [
        "andy.jpg",
        "official_test_image.jpg",
        "test_image.jpg",
        "debug_realistic_human.jpg"
    ]
    
    print("🧪 測試項目中的圖片文件:")
    print("=" * 50)
    
    for img in test_images:
        if os.path.exists(img):
            print(f"\n📷 測試: {img}")
            success = debug_face_detection(img)
            print(f"結果: {'✅ 成功' if success else '❌ 失敗'}")
        else:
            print(f"\n📷 跳過: {img} (文件不存在)")

if __name__ == "__main__":
    print("🔍 人臉檢測診斷工具")
    print("=" * 50)
    
    # 測試andy.jpg
    debug_face_detection("andy.jpg")
    
    # 測試其他圖片
    print("\n" + "=" * 50)
    test_sample_images()
