#!/usr/bin/env python3
"""
人臉註冊診斷工具
幫助用戶診斷和解決人臉註冊問題
"""

import cv2
import face_recognition
import numpy as np
import os
from pathlib import Path

def diagnose_face_detection(image_path):
    """診斷照片中的人臉檢測問題"""
    print(f"🔍 診斷照片: {image_path}")
    print("=" * 50)
    
    # 1. 檢查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 錯誤: 照片文件不存在!")
        return False
    
    print(f"✅ 照片文件存在")
    
    # 2. 檢查文件大小
    file_size = os.path.getsize(image_path)
    print(f"📏 文件大小: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    if file_size == 0:
        print(f"❌ 錯誤: 照片文件為空!")
        return False
    
    # 3. 使用 OpenCV 讀取圖片
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ 錯誤: OpenCV 無法讀取照片，可能是格式問題")
            return False
        
        height, width, channels = image.shape
        print(f"📐 圖片尺寸: {width} x {height} pixels, {channels} 通道")
        print(f"✅ OpenCV 成功讀取照片")
        
    except Exception as e:
        print(f"❌ OpenCV 讀取失敗: {e}")
        return False
    
    # 4. 轉換為 RGB (face_recognition 需要 RGB)
    try:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        print(f"✅ 成功轉換為 RGB 格式")
    except Exception as e:
        print(f"❌ RGB 轉換失敗: {e}")
        return False
    
    # 5. 使用 face_recognition 檢測人臉
    try:
        print(f"\n🎯 開始人臉檢測...")
        
        # 嘗試不同的檢測模式
        models = ['hog', 'cnn']
        
        for model in models:
            print(f"\n📊 使用 {model.upper()} 模型檢測:")
            try:
                face_locations = face_recognition.face_locations(rgb_image, model=model)
                print(f"  檢測到 {len(face_locations)} 個人臉")
                
                if len(face_locations) > 0:
                    print(f"  ✅ {model.upper()} 模型檢測成功!")
                    
                    # 顯示人臉位置
                    for i, (top, right, bottom, left) in enumerate(face_locations):
                        print(f"    人臉 {i+1}: 位置 ({left}, {top}) 到 ({right}, {bottom})")
                        print(f"    人臉 {i+1}: 大小 {right-left} x {bottom-top} pixels")
                    
                    # 嘗試提取人臉編碼
                    try:
                        face_encodings = face_recognition.face_encodings(rgb_image, face_locations, model='large')
                        print(f"  ✅ 成功提取 {len(face_encodings)} 個人臉編碼")
                        
                        # 保存帶標記的圖片用於預覽
                        marked_image = image.copy()
                        for (top, right, bottom, left) in face_locations:
                            cv2.rectangle(marked_image, (left, top), (right, bottom), (0, 255, 0), 2)
                            cv2.putText(marked_image, "Face", (left, top-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        
                        output_path = "face_detection_result.jpg"
                        cv2.imwrite(output_path, marked_image)
                        print(f"  💾 已保存標記結果到: {output_path}")
                        
                        return True
                        
                    except Exception as e:
                        print(f"  ❌ 人臉編碼失敗: {e}")
                        
                else:
                    print(f"  ❌ {model.upper()} 模型未檢測到人臉")
                    
            except Exception as e:
                print(f"  ❌ {model.upper()} 檢測失敗: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ 人臉檢測過程失敗: {e}")
        return False

def suggest_fixes():
    """提供修復建議"""
    print(f"\n💡 人臉註冊問題解決建議:")
    print("=" * 50)
    
    suggestions = [
        "📸 照片質量建議:",
        "  • 使用清晰、高分辨率的照片 (建議 >300x300 像素)",
        "  • 確保人臉佔照片的顯著部分 (至少 1/4 大小)",
        "  • 避免過暗或過亮的照片",
        "  • 人臉應該正面朝向攝像頭",
        "",
        "🖼️ 照片格式建議:",
        "  • 支持格式: JPG, JPEG, PNG, BMP",
        "  • 避免使用 HEIC 或其他特殊格式",
        "  • 確保文件沒有損壞",
        "",
        "👤 人臉條件建議:",
        "  • 人臉完整可見，沒有被遮擋",
        "  • 避免戴帽子、口罩或太陽鏡",
        "  • 確保有足夠的光線照亮人臉",
        "  • 避免強烈陰影或反光",
        "",
        "🔧 技術解決方案:",
        "  • 嘗試調整照片大小 (推薦 500-1000 像素寬度)",
        "  • 使用圖片編輯軟件增強亮度/對比度",
        "  • 確保照片是正向的 (不要旋轉或顛倒)",
        "  • 如果人很多，請裁剪只包含目標人臉的區域"
    ]
    
    for suggestion in suggestions:
        print(suggestion)

def interactive_test():
    """互動式測試"""
    print(f"\n🔧 互動式人臉檢測測試")
    print("=" * 50)
    
    while True:
        print(f"\n請選擇測試選項:")
        print(f"1. 📷 測試特定照片")
        print(f"2. 📂 測試文件夾中的所有照片")
        print(f"3. 🎥 測試攝像頭實時拍照")
        print(f"4. 💡 查看修復建議")
        print(f"5. 🚪 退出")
        
        choice = input(f"\n請選擇 (1-5): ").strip()
        
        if choice == '1':
            image_path = input(f"請輸入照片完整路徑: ").strip()
            if image_path:
                diagnose_face_detection(image_path)
        
        elif choice == '2':
            folder_path = input(f"請輸入文件夾路徑: ").strip()
            if os.path.exists(folder_path):
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
                found_images = False
                
                for file_path in Path(folder_path).rglob('*'):
                    if file_path.suffix.lower() in image_extensions:
                        found_images = True
                        print(f"\n" + "="*30)
                        diagnose_face_detection(str(file_path))
                
                if not found_images:
                    print(f"❌ 文件夾中沒有找到圖片文件")
            else:
                print(f"❌ 文件夾不存在")
        
        elif choice == '3':
            test_camera_capture()
        
        elif choice == '4':
            suggest_fixes()
        
        elif choice == '5':
            print(f"👋 測試結束")
            break
        
        else:
            print(f"❌ 無效選擇，請重新輸入")

def test_camera_capture():
    """測試攝像頭拍照功能"""
    print(f"\n📷 攝像頭拍照測試")
    print("按 's' 拍照，按 'q' 退出")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print(f"❌ 無法開啟攝像頭")
        return
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 顯示提示
            cv2.putText(frame, "Press 's' to capture, 'q' to quit", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow('Camera Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                # 保存照片
                filename = f"captured_photo_{int(cv2.getTickCount())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"\n📸 照片已保存: {filename}")
                
                # 立即測試這張照片
                diagnose_face_detection(filename)
                
            elif key == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print(f"🔍 人臉註冊診斷工具")
    print(f"幫助解決 '未檢測到人臉' 的問題")
    
    # 首先提供建議
    suggest_fixes()
    
    # 然後提供互動測試
    interactive_test()
