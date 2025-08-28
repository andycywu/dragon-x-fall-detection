#!/usr/bin/env python3
"""
🏥 老人行為預測系統 - Streamlit 演示介面
"""

import streamlit as st
import cv2
import numpy as np
import time
import os
import json
from datetime import datetime, timedelta
import pandas as pd

# Optional plotly imports (fallback if not installed)
try:
    import plotly.graph_objects as go
    import plotly.express as px
    _HAS_PLOTLY = True
except Exception:
    go = None
    px = None
    _HAS_PLOTLY = False
from elderly_behavior_predictor import ElderlyBehaviorPredictor
import tempfile

# 設置頁面配置
st.set_page_config(
    page_title="🏥 老人行為預測系統",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #2E8B57;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 5px solid #2E8B57;
}
.alert-high {
    background-color: #ffebee;
    border-left: 5px solid #f44336;
    padding: 1rem;
    border-radius: 0.5rem;
}
.alert-medium {
    background-color: #fff3e0;
    border-left: 5px solid #ff9800;
    padding: 1rem;
    border-radius: 0.5rem;
}
.alert-low {
    background-color: #e8f5e8;
    border-left: 5px solid #4caf50;
    padding: 1rem;
    border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# 初始化系統
@st.cache_resource
def init_predictor():
    return ElderlyBehaviorPredictor()

def main():
    st.markdown('<div class="main-header">🏥 老人行為預測與風險評估系統</div>', 
                unsafe_allow_html=True)
    
    # 初始化預測器
    predictor = init_predictor()
    
    # 側邊欄
    with st.sidebar:
        st.title("🔧 系統控制")
        
        # 功能選擇
        function = st.selectbox(
            "選擇功能",
            ["🏠 監控儀表板", "👤 用戶管理", "📊 數據分析", "🎥 即時監測", "🔊 語音互動測試"]
        )
        
        st.markdown("---")
        
        # 用戶選擇
        user_profiles = predictor.user_profiles
        if user_profiles:
            selected_user = st.selectbox(
                "選擇用戶",
                list(user_profiles.keys()),
                format_func=lambda x: f"{user_profiles[x]['name']} ({x})"
            )
        else:
            selected_user = None
            st.warning("⚠️ 尚未註冊任何用戶")
    
    # 主要內容區域
    if function == "🏠 監控儀表板":
        show_dashboard(predictor, selected_user)
    elif function == "👤 用戶管理":
        show_user_management(predictor)
    elif function == "📊 數據分析":
        show_data_analysis(predictor, selected_user)
    elif function == "🎥 即時監測":
        show_live_monitoring(predictor)
    elif function == "🔊 語音互動測試":
        show_voice_interaction(predictor, selected_user)

def show_dashboard(predictor, user_id):
    """顯示監控儀表板"""
    st.header("🏠 監控儀表板")
    
    if not user_id:
        st.warning("請先在側邊欄選擇用戶或註冊新用戶")
        return
    
    # 獲取儀表板數據
    dashboard_data = predictor.get_user_dashboard_data(user_id)
    
    if dashboard_data.get('status') == 'error':
        st.error(f"數據載入失敗: {dashboard_data.get('message')}")
        return
    
    # 用戶基本信息
    user_info = dashboard_data['user_info']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👤 用戶", user_info.get('name', '未知'))
    
    with col2:
        risk_score = dashboard_data['current_risk_score']
        risk_color = "🔴" if risk_score > 0.7 else "🟡" if risk_score > 0.3 else "🟢"
        st.metric("⚠️ 風險評分", f"{risk_score:.2f} {risk_color}")
    
    with col3:
        activity_count = dashboard_data['recent_activity_count']
        st.metric("📊 近期活動", f"{activity_count} 次")
    
    with col4:
        status = dashboard_data['monitoring_status']
        status_icon = "🟢" if status == "active" else "🔴"
        st.metric("📡 監控狀態", f"{status} {status_icon}")
    
    # 風險警報
    risk_score = dashboard_data['current_risk_score']
    if risk_score > 0.7:
        st.markdown(f"""
        <div class="alert-high">
        <h4>🚨 高風險警報</h4>
        <p>用戶 {user_info.get('name')} 的跌倒風險評分為 {risk_score:.2f}，建議立即關注！</p>
        </div>
        """, unsafe_allow_html=True)
    elif risk_score > 0.3:
        st.markdown(f"""
        <div class="alert-medium">
        <h4>⚠️ 中等風險提醒</h4>
        <p>用戶 {user_info.get('name')} 的跌倒風險評分為 {risk_score:.2f}，請留意觀察。</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-low">
        <h4>✅ 狀況良好</h4>
        <p>用戶 {user_info.get('name')} 的跌倒風險評分為 {risk_score:.2f}，狀況穩定。</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 最近活動圖表
    if dashboard_data['recent_activity_count'] > 0:
        st.subheader("📈 最近活動趨勢")
        
        # 模擬時間序列數據（實際應該從數據庫獲取）
        time_points = [datetime.now() - timedelta(minutes=i*10) for i in range(6)]
        risk_scores = [risk_score + np.random.normal(0, 0.1) for _ in range(6)]
        
        if _HAS_PLOTLY:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_points,
                y=risk_scores,
                mode='lines+markers',
                name='風險評分',
                line=dict(color='#2E8B57', width=3)
            ))
            fig.update_layout(
                title="過去1小時風險評分變化",
                xaxis_title="時間",
                yaxis_title="風險評分",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Plotly not installed — skipping interactive charts. Install optional dependencies listed in requirements_optional.txt to enable plots.")

def show_user_management(predictor):
    """顯示用戶管理界面"""
    st.header("👤 用戶管理")
    
    tab1, tab2 = st.tabs(["註冊新用戶", "管理現有用戶"])
    
    with tab1:
        st.subheader("註冊新用戶")
        
        with st.form("register_user"):
            user_id = st.text_input("用戶ID", placeholder="例如: elderly_001")
            name = st.text_input("姓名", placeholder="例如: 張奶奶")
            
            # 照片上傳
            uploaded_file = st.file_uploader("上傳用戶照片", type=['jpg', 'jpeg', 'png'])
            
            # 額外信息
            age = st.number_input("年齡", min_value=50, max_value=120, value=70)
            medical_conditions = st.text_area("健康狀況", placeholder="例如: 高血壓, 糖尿病")
            
            submitted = st.form_submit_button("註冊用戶")
            
            if submitted:
                if user_id and name and uploaded_file:
                    # 保存上傳的照片
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, f"{user_id}.jpg")
                    
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 準備用戶信息
                    profile_info = {
                        "age": age,
                        "medical_conditions": medical_conditions.split(",") if medical_conditions else []
                    }
                    
                    # 註冊用戶
                    success = predictor.register_user(user_id, name, temp_path, profile_info)
                    
                    if success:
                        st.success(f"✅ 用戶 {name} ({user_id}) 註冊成功！")
                        st.experimental_rerun()
                    else:
                        st.error("❌ 用戶註冊失敗，請檢查照片是否包含清晰的人臉")
                else:
                    st.error("請填寫所有必需信息並上傳照片")
    
    with tab2:
        st.subheader("現有用戶")
        
        if predictor.user_profiles:
            for user_id, user_info in predictor.user_profiles.items():
                with st.expander(f"👤 {user_info['name']} ({user_id})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**註冊時間**: {datetime.fromtimestamp(user_info['registered_time'])}")
                        if user_info.get('last_seen'):
                            st.write(f"**最後見到**: {datetime.fromtimestamp(user_info['last_seen'])}")
                        else:
                            st.write("**最後見到**: 從未")
                    
                    with col2:
                        profile_info = user_info.get('profile_info', {})
                        if profile_info.get('age'):
                            st.write(f"**年齡**: {profile_info['age']}")
                        if profile_info.get('medical_conditions'):
                            st.write(f"**健康狀況**: {', '.join(profile_info['medical_conditions'])}")
        else:
            st.info("尚未註冊任何用戶")

def show_data_analysis(predictor, user_id):
    """顯示數據分析"""
    st.header("📊 數據分析")
    
    if not user_id:
        st.warning("請先選擇用戶")
        return
    
    # 時間範圍選擇
    time_range = st.selectbox("分析時間範圍", ["過去1小時", "過去24小時", "過去7天"])
    
    # 模擬分析數據
    st.subheader(f"📈 {predictor.user_profiles[user_id]['name']} 的行為分析")
    
    # 風險評分趨勢
    # 模擬數據
    dates = pd.date_range(end=datetime.now(), periods=24, freq='H')
    risk_scores = np.random.normal(0.4, 0.2, 24)
    risk_scores = np.clip(risk_scores, 0, 1)

    if _HAS_PLOTLY:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=dates,
            y=risk_scores,
            mode='lines+markers',
            name='風險評分',
            line=dict(color='#FF6B6B', width=2)
        ))

        fig1.update_layout(
            title="風險評分趨勢",
            xaxis_title="時間",
            yaxis_title="風險評分",
            height=400
        )

        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("Plotly not installed — skipping interactive charts. Install optional dependencies listed in requirements_optional.txt to enable plots.")
    
    # 姿態指標分析
    col1, col2 = st.columns(2)
    
    with col1:
        # 平衡評分分佈
        balance_scores = np.random.normal(0.7, 0.15, 100)
        balance_scores = np.clip(balance_scores, 0, 1)
        
        if _HAS_PLOTLY:
            fig2 = px.histogram(
                x=balance_scores,
                nbins=20,
                title="平衡評分分佈",
                labels={'x': '平衡評分', 'y': '頻次'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Plotly not installed — histogram unavailable.")
    
    with col2:
        # 活動水平
        activity_levels = np.random.normal(0.5, 0.2, 100)
        activity_levels = np.clip(activity_levels, 0, 1)
        
        if _HAS_PLOTLY:
            fig3 = px.histogram(
                x=activity_levels,
                nbins=20,
                title="活動水平分佈",
                labels={'x': '活動水平', 'y': '頻次'}
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Plotly not installed — histogram unavailable.")

def show_live_monitoring(predictor):
    """顯示即時監測"""
    st.header("🎥 即時監測")
    
    st.info("💡 這個功能需要攝像頭權限。點擊下方按鈕開始監測。")
    
    if st.button("🎥 開始攝像頭監測"):
        # 創建攝像頭預覽區域
        image_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # 嘗試開啟攝像頭
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ 無法開啟攝像頭")
            return
        
        try:
            # 監測循環
            for i in range(30):  # 只運行30幀作為演示
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 人臉識別
                user_id = predictor.identify_user(frame)
                
                # 在圖像上繪製信息
                if user_id:
                    name = predictor.user_profiles[user_id]['name']
                    cv2.putText(frame, f"User: {name}", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # 計算風險
                    risk_score = predictor.calculate_fall_risk_score(user_id)
                    risk_color = (0, 0, 255) if risk_score > 0.7 else (0, 255, 255) if risk_score > 0.3 else (0, 255, 0)
                    cv2.putText(frame, f"Risk: {risk_score:.2f}", (10, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, risk_color, 2)
                    
                    status_placeholder.success(f"✅ 檢測到用戶: {name}, 風險評分: {risk_score:.2f}")
                else:
                    cv2.putText(frame, "No user detected", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    status_placeholder.warning("⚠️ 未檢測到已註冊用戶")
                
                # 顯示圖像
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
                
                time.sleep(0.1)  # 控制幀率
                
        finally:
            cap.release()

def show_voice_interaction(predictor, user_id):
    """顯示語音互動測試"""
    st.header("🔊 語音互動測試")
    
    if not user_id:
        st.warning("請先選擇用戶")
        return
    
    user_name = predictor.user_profiles[user_id]['name']
    st.subheader(f"與 {user_name} 的語音互動")
    
    # 語音問題測試
    st.subheader("🗣️ 語音提問")
    
    question = st.selectbox(
        "選擇問題",
        [
            f"您好 {user_name}，今天感覺怎麼樣？",
            f"{user_name}，您今天有感到頭暈或不舒服嗎？",
            f"親愛的 {user_name}，請告訴我您現在的感受如何？"
        ]
    )
    
    if st.button("🔊 播放問題"):
        predictor.ask_user_checkin_question(user_id, question, speak=True)
        st.success("✅ 問題已播放")
    
    # 模擬語音回覆測試
    st.subheader("🎤 模擬語音回覆")
    
    test_responses = {
        "正面回應": "我今天感覺很好，謝謝關心",
        "中性回應": "還可以，沒什麼特別的",
        "負面回應": "我今天有點頭暈，感覺不太舒服",
        "警報回應": "我覺得很虛弱，剛才差點跌倒"
    }
    
    for response_type, response_text in test_responses.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{response_type}**: {response_text}")
        
        with col2:
            if st.button(f"測試", key=response_type):
                result = predictor.interpret_user_reply(text_input=response_text)
                
                if result['status'] == 'success':
                    sentiment = result['sentiment_score']
                    keywords = result['keywords']
                    alert_level = result['alert_level']
                    
                    # 顯示分析結果
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("情感評分", f"{sentiment:.2f}")
                    with col_b:
                        st.metric("關鍵詞", len(keywords))
                    with col_c:
                        alert_color = "🔴" if alert_level == "high" else "🟡" if alert_level == "medium" else "🟢"
                        st.metric("警報等級", f"{alert_level} {alert_color}")
                    
                    if keywords:
                        st.write(f"檢測到的關鍵詞: {', '.join(keywords)}")

if __name__ == "__main__":
    main()
