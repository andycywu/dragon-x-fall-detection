#!/usr/bin/env python3
"""
🎯 QAI Hub Live Demo - Streamlit Web應用
實時老人行為檢測與風險評估系統
"""

import streamlit as st
import cv2
import numpy as np
import tempfile
import os
import time
from datetime import datetime
import logging
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# 設置頁面配置
st.set_page_config(
    page_title="QAI Hub 老人行為檢測系統",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS樣式
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.sub-header {
    font-size: 1.5rem;
    color: #2c3e50;
    margin: 1rem 0;
}
.metric-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
}
.alert-high {
    background-color: #fee;
    color: #c53030;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #c53030;
}
.alert-medium {
    background-color: #fffbf0;
    color: #d69e2e;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #d69e2e;
}
.alert-low {
    background-color: #f0fff4;
    color: #38a169;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #38a169;
}
</style>
""", unsafe_allow_html=True)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def load_detection_systems():
    """載入檢測系統（使用Streamlit快取）"""
    try:
        from official_qai_hub_detector import OfficialQAIHubDetector
        from elderly_behavior_predictor import ElderlyBehaviorPredictor
        
        detector = OfficialQAIHubDetector()
        predictor = ElderlyBehaviorPredictor()
        
        return detector, predictor, True
    except Exception as e:
        st.error(f"無法載入檢測系統: {e}")
        return None, None, False

def process_uploaded_image(uploaded_file, detector, predictor):
    """處理上傳的圖像"""
    try:
        # 保存上傳的文件到臨時目錄
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name
        
        # 載入圖像
        image = cv2.imread(temp_path)
        if image is None:
            st.error("無法載入圖像")
            return None
        
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 執行檢測
        with st.spinner("🔍 執行QAI Hub檢測..."):
            unified_result = detector.unified_detection(rgb_image)
            
            # 行為分析
            user_id = f"demo_user_{int(time.time())}"
            interaction_result = predictor.process_user_interaction(user_id, image)
        
        # 清理臨時文件
        os.unlink(temp_path)
        
        return {
            'image': rgb_image,
            'unified_result': unified_result,
            'interaction_result': interaction_result
        }
        
    except Exception as e:
        st.error(f"處理圖像時發生錯誤: {e}")
        return None

def process_webcam_frame(frame, detector, predictor):
    """處理網路攝影機幀"""
    try:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 執行檢測
        unified_result = detector.unified_detection(rgb_frame)
        
        # 行為分析
        user_id = f"webcam_user_{int(time.time())}"
        interaction_result = predictor.process_user_interaction(user_id, frame)
        
        return {
            'image': rgb_frame,
            'unified_result': unified_result,
            'interaction_result': interaction_result
        }
        
    except Exception as e:
        st.error(f"處理網路攝影機幀時發生錯誤: {e}")
        return None

def display_detection_results(results):
    """顯示檢測結果"""
    if not results:
        return
    
    unified_result = results['unified_result']
    interaction_result = results['interaction_result']
    
    # 檢測統計
    col1, col2, col3 = st.columns(3)
    
    with col1:
        face_count = unified_result.get('total_detections', {}).get('faces', 0)
        st.metric("👤 人臉檢測", f"{face_count}個")
    
    with col2:
        pose_count = unified_result.get('total_detections', {}).get('poses', 0)
        st.metric("🚶 姿態檢測", f"{pose_count}個")
    
    with col3:
        hand_count = unified_result.get('total_detections', {}).get('hands', 0)
        st.metric("✋ 手部檢測", f"{hand_count}個")
    
    # 行為分析結果
    if interaction_result:
        st.markdown("### 🧠 行為分析")
        
        pose_analysis = interaction_result.get('pose_analysis', {})
        risk_assessment = interaction_result.get('risk_assessment', {})
        
        if pose_analysis and 'error' not in pose_analysis:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                balance_score = pose_analysis.get('balance_score', 0)
                st.metric("⚖️ 平衡評分", f"{balance_score:.2f}")
            
            with col2:
                stability_score = pose_analysis.get('stability_score', 0)
                st.metric("🎯 穩定性評分", f"{stability_score:.2f}")
            
            with col3:
                posture_deviation = pose_analysis.get('posture_deviation', 0)
                st.metric("📐 姿態偏差", f"{posture_deviation:.2f}")
        
        # 風險評估
        if risk_assessment:
            risk_score = risk_assessment.get('score', 0)
            risk_level = risk_assessment.get('level', 'unknown')
            
            st.markdown("### 🚨 風險評估")
            
            # 根據風險等級選擇顏色和圖標
            if risk_level == 'high':
                risk_color = "🔴"
                alert_class = "alert-high"
            elif risk_level == 'medium':
                risk_color = "🟡"
                alert_class = "alert-medium"
            else:
                risk_color = "🟢"
                alert_class = "alert-low"
            
            st.markdown(f"""
            <div class="{alert_class}">
                <h4>{risk_color} 風險等級: {risk_level.upper()}</h4>
                <p>風險評分: {risk_score:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 風險評分圖表
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = risk_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "風險評分"},
                delta = {'reference': 0.5},
                gauge = {
                    'axis': {'range': [None, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 0.3], 'color': "lightgreen"},
                        {'range': [0.3, 0.7], 'color': "yellow"},
                        {'range': [0.7, 1], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.9
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

def display_annotated_images(results, detector):
    """顯示標註圖像"""
    if not results:
        return
    
    rgb_image = results['image']
    
    st.markdown("### 🖼️ 檢測結果視覺化")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 👤 人臉檢測")
        face_result = detector.detect_faces(rgb_image, raw_output=False)
        if face_result.get('success') and 'annotated_image' in face_result:
            st.image(face_result['annotated_image'], use_container_width=True)
        else:
            st.image(rgb_image, caption="無檢測結果", use_container_width=True)
    
    with col2:
        st.markdown("#### 🚶 姿態檢測")
        pose_result = detector.detect_pose(rgb_image, raw_output=False)
        if pose_result.get('success') and 'annotated_image' in pose_result:
            st.image(pose_result['annotated_image'], use_container_width=True)
        else:
            st.image(rgb_image, caption="無檢測結果", use_container_width=True)
    
    with col3:
        st.markdown("#### ✋ 手部檢測")
        hand_result = detector.detect_hands(rgb_image, raw_output=False)
        if hand_result.get('success') and 'annotated_image' in hand_result:
            st.image(hand_result['annotated_image'], use_container_width=True)
        else:
            st.image(rgb_image, caption="無檢測結果", use_container_width=True)

def main():
    """主函數"""
    # 標題
    st.markdown('<h1 class="main-header">🧠 QAI Hub 老人行為檢測系統</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #7f8c8d;">基於Qualcomm AI Hub的實時老人行為監測與風險評估</p>', unsafe_allow_html=True)
    
    # 載入檢測系統
    detector, predictor, system_loaded = load_detection_systems()
    
    if not system_loaded:
        st.error("🚫 檢測系統載入失敗，請檢查系統配置")
        return
    
    # 側邊欄配置
    st.sidebar.markdown("## ⚙️ 系統配置")
    
    demo_mode = st.sidebar.selectbox(
        "選擇演示模式",
        ["📷 圖像上傳", "📹 網路攝影機", "🖼️ 示例圖像"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 系統狀態")
    st.sidebar.success("✅ QAI Hub 檢測系統已載入")
    st.sidebar.success("✅ 行為預測系統已載入")
    
    # 主要內容區域
    if demo_mode == "📷 圖像上傳":
        st.markdown("## 📷 圖像上傳檢測")
        
        uploaded_file = st.file_uploader(
            "選擇圖像文件",
            type=['jpg', 'jpeg', 'png'],
            help="支援JPG、JPEG、PNG格式"
        )
        
        if uploaded_file is not None:
            # 顯示原始圖像
            image = Image.open(uploaded_file)
            st.image(image, caption="上傳的圖像", use_container_width=True)
            
            # 處理圖像
            results = process_uploaded_image(uploaded_file, detector, predictor)
            
            if results:
                # 顯示檢測結果
                display_detection_results(results)
                
                # 顯示標註圖像
                display_annotated_images(results, detector)
    
    elif demo_mode == "📹 網路攝影機":
        st.markdown("## 📹 網路攝影機實時檢測")
        
        # 攝影機控制
        col1, col2 = st.columns([1, 1])
        
        with col1:
            start_camera = st.button("🎥 啟動攝影機", type="primary")
        
        with col2:
            stop_camera = st.button("⏹️ 停止攝影機")
        
        # 攝影機幀顯示區域
        camera_placeholder = st.empty()
        results_placeholder = st.empty()
        
        if start_camera:
            try:
                cap = cv2.VideoCapture(0)
                
                if not cap.isOpened():
                    st.error("無法打開攝影機")
                else:
                    st.success("攝影機已啟動，正在進行實時檢測...")
                    
                    # 實時處理循環
                    frame_count = 0
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # 每隔幾幀處理一次（提高性能）
                        if frame_count % 10 == 0:
                            results = process_webcam_frame(frame, detector, predictor)
                            
                            if results:
                                with camera_placeholder.container():
                                    st.image(results['image'], caption="實時檢測", use_container_width=True)
                                
                                with results_placeholder.container():
                                    display_detection_results(results)
                        
                        frame_count += 1
                        
                        # 檢查停止條件
                        if stop_camera:
                            break
                    
                    cap.release()
                    
            except Exception as e:
                st.error(f"攝影機錯誤: {e}")
    
    elif demo_mode == "🖼️ 示例圖像":
        st.markdown("## 🖼️ 示例圖像檢測")
        
        # 列出可用的示例圖像
        sample_images = []
        image_files = ['andy.jpg', 'official_test_image.jpg', 'enhanced_test_image.jpg']
        
        for img_file in image_files:
            if os.path.exists(img_file):
                sample_images.append(img_file)
        
        if sample_images:
            selected_image = st.selectbox("選擇示例圖像", sample_images)
            
            if selected_image:
                # 載入並顯示圖像
                image = cv2.imread(selected_image)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                st.image(rgb_image, caption=f"示例圖像: {selected_image}", use_container_width=True)
                
                # 執行檢測
                with st.spinner("🔍 執行檢測..."):
                    unified_result = detector.unified_detection(rgb_image)
                    
                    user_id = f"demo_{selected_image}"
                    interaction_result = predictor.process_user_interaction(user_id, image)
                
                results = {
                    'image': rgb_image,
                    'unified_result': unified_result,
                    'interaction_result': interaction_result
                }
                
                # 顯示結果
                display_detection_results(results)
                display_annotated_images(results, detector)
        else:
            st.warning("未找到示例圖像")
    
    # 頁腳信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #7f8c8d; margin-top: 2rem;">
        <p>🧠 QAI Hub 老人行為檢測系統 | 基於 Qualcomm AI Hub MediaPipe 模型</p>
        <p>⚡ 實時檢測 | 🎯 智能分析 | 🚨 風險評估</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
