#!/usr/bin/env python3
"""
調試QAI Hub MediaPipe Face模型
"""

import logging
import cv2
import numpy as np
from PIL import Image

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_qai_hub_face_model():
    """測試QAI Hub MediaPipe Face模型"""
    try:
        # 初始化QAI Hub Face檢測器
        logger.info("🚀 初始化 QAI Hub MediaPipe Face 檢測器...")
        
        from qai_hub_models.models.mediapipe_face.app import MediaPipeFaceApp
        from qai_hub_models.models.mediapipe_face.model import MediaPipeFace
        
        face_model = MediaPipeFace.from_pretrained()
        face_detector = MediaPipeFaceApp.from_pretrained(face_model)
        logger.info("✅ 模型初始化成功")
        
        # 讀取測試圖像
        image_path = "andy.jpg"
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"無法讀取圖像: {image_path}")
            return
            
        logger.info(f"圖像尺寸: {image.shape}")
        
        # 轉換為RGB PIL圖像
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # 檢查模型的可用方法
        logger.info("模型的可用方法:")
        for attr in dir(face_detector):
            if not attr.startswith('_'):
                logger.info(f"  - {attr}")
        
        # 嘗試不同的預測方法
        methods_to_try = [
            'predict_landmarks_from_image',
            'predict_from_image', 
            'predict',
            'detect',
            'inference'
        ]
        
        for method_name in methods_to_try:
            if hasattr(face_detector, method_name):
                logger.info(f"\n🔍 嘗試方法: {method_name}")
                try:
                    method = getattr(face_detector, method_name)
                    result = method(pil_image)
                    logger.info(f"結果類型: {type(result)}")
                    
                    if isinstance(result, np.ndarray):
                        logger.info(f"NumPy陣列形狀: {result.shape}")
                        logger.info(f"數據類型: {result.dtype}")
                        logger.info(f"值範圍: {result.min()} - {result.max()}")
                    elif isinstance(result, list):
                        logger.info(f"列表長度: {len(result)}")
                        if len(result) > 0:
                            logger.info(f"第一個元素類型: {type(result[0])}")
                            if hasattr(result[0], 'shape'):
                                logger.info(f"第一個元素形狀: {result[0].shape}")
                    else:
                        logger.info(f"結果: {result}")
                        
                except Exception as e:
                    logger.error(f"方法 {method_name} 失敗: {e}")
            else:
                logger.info(f"❌ 方法 {method_name} 不存在")
    
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_qai_hub_face_model()
