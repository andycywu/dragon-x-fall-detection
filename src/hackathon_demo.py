#!/usr/bin/env python3
"""
黑客松專用 Streamlit 演示界面
MediaPipe + Qualcomm AI Hub 整合展示
"""

import streamlit as st
import cv2
import numpy as np
import time
import json
from datetime import datetime
import threading
import queue
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# 設置頁面配置
st.set_page_config(
    page_title="🏆 黑客松跌倒檢測系統",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定義CSS
st.markdown("""
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    color: #FF6B6B;
    text-align: center;
    margin-bottom: 2rem;
}

.tech-badge {
    background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    margin: 0.2rem;
    display: inline-block;
    font-weight: bold;
}

.metric-card {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin: 0.5rem 0;
}

.alert-danger {
    background: #ffe6e6;
    border: 2px solid #ff4444;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
}

.alert-success {
    background: #e6ffe6;
    border: 2px solid #44ff44;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

class HackathonDemoApp:
    """黑客松演示應用"""
    
    def __init__(self):
        """初始化演示應用"""
        self.setup_session_state()
        self.load_demo_data()
        
    def setup_session_state(self):
        """設置會話狀態"""
        if 'detection_active' not in st.session_state:
            st.session_state.detection_active = False
        if 'detection_history' not in st.session_state:
            st.session_state.detection_history = []
        if 'performance_data' not in st.session_state:
            st.session_state.performance_data = []
            
    def load_demo_data(self):
        """加載演示數據"""
        # 生成模擬性能數據
        self.generate_performance_data()
        
    def generate_performance_data(self):
        """生成性能數據"""
        timestamps = pd.date_range(
            start=datetime.now() - pd.Timedelta(hours=1),
            end=datetime.now(),
            freq='10S'
        )
        
        performance_data = []
        for i, timestamp in enumerate(timestamps):
            # 模擬QAI Hub加速效果
            base_fps = 15 + np.sin(i * 0.1) * 3
            accelerated_fps = base_fps * (1.5 + np.random.normal(0, 0.1))
            
            performance_data.append({
                'timestamp': timestamp,
                'base_fps': max(0, base_fps),
                'accelerated_fps': max(0, accelerated_fps),
                'acceleration_ratio': accelerated_fps / base_fps if base_fps > 0 else 1,
                'power_usage': 100 - (accelerated_fps - base_fps) * 2,
                'fall_risk': np.random.beta(2, 8) if np.random.random() > 0.9 else np.random.beta(1, 20)
            })
            
        self.performance_df = pd.DataFrame(performance_data)
        
    def render_header(self):
        """渲染頁面頭部"""
        st.markdown('<div class="main-header">🏆 黑客松跌倒檢測系統</div>', unsafe_allow_html=True)
        
        # 技術標籤
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center;">
                <span class="tech-badge">MediaPipe Pose</span>
                <span class="tech-badge">Qualcomm AI Hub</span>
                <span class="tech-badge">Real-time AI</span>
                <span class="tech-badge">Edge Computing</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
    def render_sidebar(self):
        """渲染側邊欄"""
        st.sidebar.markdown("## 🎯 系統控制")
        
        # 檢測控制
        if st.sidebar.button("🚀 啟動檢測" if not st.session_state.detection_active else "⏹️ 停止檢測"):
            st.session_state.detection_active = not st.session_state.detection_active
            
        # 系統配置
        st.sidebar.markdown("### ⚙️ 檢測參數")
        
        fall_threshold = st.sidebar.slider("跌倒風險閾值", 0.0, 1.0, 0.7, 0.1)
        angle_threshold = st.sidebar.slider("身體角度閾值 (度)", 10, 90, 30, 5)
        sensitivity = st.sidebar.selectbox("檢測靈敏度", ["低", "中", "高"], index=1)
        
        # QAI Hub設置
        st.sidebar.markdown("### 🔧 QAI Hub 設置")
        use_acceleration = st.sidebar.checkbox("啟用AI加速", value=True)
        optimization_level = st.sidebar.selectbox("優化級別", ["平衡", "性能", "功耗"], index=0)
        
        # 演示模式
        st.sidebar.markdown("### 🎪 演示模式")
        demo_scenario = st.sidebar.selectbox(
            "選擇演示場景",
            ["正常活動", "模擬跌倒", "緊急情況", "性能測試"]
        )
        
        return {
            'fall_threshold': fall_threshold,
            'angle_threshold': angle_threshold,
            'sensitivity': sensitivity,
            'use_acceleration': use_acceleration,
            'optimization_level': optimization_level,
            'demo_scenario': demo_scenario
        }
        
    def render_real_time_metrics(self):
        """渲染實時指標"""
        st.markdown("## 📊 實時監控")
        
        # 創建指標列
        col1, col2, col3, col4 = st.columns(4)
        
        # 模擬實時數據
        current_fps = 28.5 if st.session_state.detection_active else 0
        fall_risk = np.random.beta(2, 8) if st.session_state.detection_active else 0
        ai_acceleration = "3.2x" if st.session_state.detection_active else "待機"
        power_efficiency = "52%" if st.session_state.detection_active else "0%"
        
        with col1:
            st.metric(
                label="🎯 FPS",
                value=f"{current_fps:.1f}",
                delta="15.3" if st.session_state.detection_active else None
            )
            
        with col2:
            st.metric(
                label="⚠️ 跌倒風險",
                value=f"{fall_risk:.2f}",
                delta="-0.15" if fall_risk < 0.3 else "0.12",
                delta_color="inverse" if fall_risk < 0.3 else "normal"
            )
            
        with col3:
            st.metric(
                label="🚀 AI加速",
                value=ai_acceleration,
                delta="2.1x" if st.session_state.detection_active else None
            )
            
        with col4:
            st.metric(
                label="🔋 功耗優化",
                value=power_efficiency,
                delta="12%" if st.session_state.detection_active else None,
                delta_color="inverse"
            )
            
    def render_performance_charts(self):
        """渲染性能圖表"""
        st.markdown("## 📈 性能分析")
        
        # 創建圖表列
        col1, col2 = st.columns(2)
        
        with col1:
            # FPS對比圖
            fig_fps = go.Figure()
            
            fig_fps.add_trace(go.Scatter(
                x=self.performance_df['timestamp'],
                y=self.performance_df['base_fps'],
                mode='lines',
                name='基礎FPS',
                line=dict(color='#ff7f0e', width=2)
            ))
            
            fig_fps.add_trace(go.Scatter(
                x=self.performance_df['timestamp'],
                y=self.performance_df['accelerated_fps'],
                mode='lines',
                name='QAI Hub加速FPS',
                line=dict(color='#2ca02c', width=3)
            ))
            
            fig_fps.update_layout(
                title="FPS性能對比",
                xaxis_title="時間",
                yaxis_title="幀率 (FPS)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_fps, use_container_width=True)
            
        with col2:
            # 加速比率圖
            fig_ratio = go.Figure()
            
            fig_ratio.add_trace(go.Scatter(
                x=self.performance_df['timestamp'],
                y=self.performance_df['acceleration_ratio'],
                mode='lines+markers',
                name='加速比率',
                line=dict(color='#d62728', width=2),
                marker=dict(size=4)
            ))
            
            fig_ratio.add_hline(
                y=1.0,
                line_dash="dash",
                line_color="gray",
                annotation_text="基準線"
            )
            
            fig_ratio.update_layout(
                title="AI加速效果",
                xaxis_title="時間",
                yaxis_title="加速比率",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_ratio, use_container_width=True)
            
    def render_fall_risk_analysis(self):
        """渲染跌倒風險分析"""
        st.markdown("## 🎯 跌倒風險分析")
        
        # 風險等級分佈
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 創建風險時間序列
            fig_risk = go.Figure()
            
            # 添加風險閾值線
            fig_risk.add_hline(
                y=0.7,
                line_dash="dash",
                line_color="red",
                annotation_text="高風險閾值"
            )
            
            fig_risk.add_hline(
                y=0.3,
                line_dash="dash",
                line_color="orange",
                annotation_text="中風險閾值"
            )
            
            # 添加風險數據
            fig_risk.add_trace(go.Scatter(
                x=self.performance_df['timestamp'],
                y=self.performance_df['fall_risk'],
                mode='lines+markers',
                name='跌倒風險',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=3),
                fill='tonexty'
            ))
            
            fig_risk.update_layout(
                title="實時跌倒風險監控",
                xaxis_title="時間",
                yaxis_title="風險等級",
                yaxis=dict(range=[0, 1]),
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig_risk, use_container_width=True)
            
        with col2:
            # 風險等級統計
            risk_levels = pd.cut(
                self.performance_df['fall_risk'],
                bins=[0, 0.3, 0.7, 1.0],
                labels=['低風險', '中風險', '高風險']
            ).value_counts()
            
            fig_pie = px.pie(
                values=risk_levels.values,
                names=risk_levels.index,
                title="風險等級分佈",
                color_discrete_map={
                    '低風險': '#2ca02c',
                    '中風險': '#ff7f0e',
                    '高風險': '#d62728'
                }
            )
            
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
            
    def render_technology_showcase(self):
        """渲染技術展示"""
        st.markdown("## 🔬 技術架構")
        
        # 技術架構圖
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            ### 🎯 MediaPipe 姿態檢測
            - **33個關鍵點檢測**
            - **實時3D姿態估計**
            - **多人同時檢測**
            - **跨平台兼容性**
            """)
            
            # 模擬姿態檢測結果
            pose_confidence = 0.95 if st.session_state.detection_active else 0
            st.progress(pose_confidence, text=f"姿態檢測置信度: {pose_confidence:.2f}")
            
        with col2:
            st.markdown("""
            ### 🚀 Qualcomm AI Hub 加速
            - **硬件加速推理**
            - **功耗優化**
            - **邊緣AI部署**
            - **模型量化優化**
            """)
            
            # 模擬加速效果
            acceleration_factor = 3.2 if st.session_state.detection_active else 1.0
            st.progress(acceleration_factor/5, text=f"AI加速係數: {acceleration_factor:.1f}x")
            
    def render_demo_controls(self):
        """渲染演示控制"""
        st.markdown("## 🎪 演示控制")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎬 模擬正常活動", use_container_width=True):
                st.success("正在模擬正常活動場景...")
                
        with col2:
            if st.button("⚠️ 模擬跌倒事件", use_container_width=True):
                st.error("警告：檢測到跌倒事件！")
                
        with col3:
            if st.button("📊 生成報告", use_container_width=True):
                st.info("正在生成檢測報告...")
                
    def render_alert_system(self):
        """渲染警報系統"""
        # 檢查是否有高風險
        current_risk = self.performance_df['fall_risk'].iloc[-1] if not self.performance_df.empty else 0
        
        if current_risk > 0.7:
            st.markdown("""
            <div class="alert-danger">
                <h3>🚨 高風險警報</h3>
                <p>檢測到高跌倒風險，建議立即注意！</p>
                <p><strong>風險等級:</strong> {:.2f}</p>
                <p><strong>檢測時間:</strong> {}</p>
            </div>
            """.format(current_risk, datetime.now().strftime("%H:%M:%S")), unsafe_allow_html=True)
        elif st.session_state.detection_active:
            st.markdown("""
            <div class="alert-success">
                <h3>✅ 系統正常</h3>
                <p>檢測系統運行正常，未發現異常情況。</p>
            </div>
            """, unsafe_allow_html=True)
            
    def run(self):
        """運行演示應用"""
        # 渲染頁面組件
        self.render_header()
        
        # 側邊欄配置
        config = self.render_sidebar()
        
        # 主內容區域
        self.render_alert_system()
        self.render_real_time_metrics()
        self.render_performance_charts()
        self.render_fall_risk_analysis()
        self.render_technology_showcase()
        self.render_demo_controls()
        
        # 頁腳信息
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; margin-top: 2rem;">
            <p>🏆 <strong>黑客松跌倒檢測系統</strong> | MediaPipe + Qualcomm AI Hub | 實時AI邊緣計算</p>
            <p>💡 展示了AI技術在醫療健康領域的創新應用</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """主函數"""
    try:
        # 創建並運行演示應用
        app = HackathonDemoApp()
        app.run()
        
    except Exception as e:
        st.error(f"應用運行錯誤: {e}")
        st.exception(e)

if __name__ == "__main__":
    main()
