import streamlit as st
import cv2
import numpy as np
import time
import tempfile
import io
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from fall_detector_opencv import FallDetector
from whisper_simple import WhisperKeywordDetector
from fusion_trigger import FusionTrigger

# Page configuration
st.set_page_config(
    page_title="Fall Detection Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'fall_detector' not in st.session_state:
    st.session_state.fall_detector = FallDetector()
if 'whisper_detector' not in st.session_state:
    st.session_state.whisper_detector = WhisperKeywordDetector()
if 'fusion_trigger' not in st.session_state:
    st.session_state.fusion_trigger = FusionTrigger()
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []

def main():
    st.title("🚨 Fall Detection Dashboard")
    st.markdown("Real-time monitoring system using pose detection and voice analysis")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Controls")
    
    # Detection modes
    st.sidebar.subheader("Detection Modes")
    enable_pose = st.sidebar.checkbox("Enable Pose Detection", value=True)
    enable_audio = st.sidebar.checkbox("Enable Audio Detection", value=True)
    
    # Settings
    st.sidebar.subheader("Settings")
    angle_threshold = st.sidebar.slider("Fall Angle Threshold (degrees)", 60, 120, 80)
    cooldown_time = st.sidebar.slider("Alert Cooldown (seconds)", 1, 10, 3)
    
    # Update fusion trigger cooldown
    st.session_state.fusion_trigger.cooldown_seconds = cooldown_time
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📹 Live Detection")
        
        # Camera input
        camera_input = st.camera_input("Take a photo for pose analysis")
        
        if camera_input is not None:
            # Process image
            image_bytes = camera_input.read()
            image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            if enable_pose and image is not None:
                # Detect fall
                fall_detected, angle = st.session_state.fall_detector.detect_fall_from_frame(image)
                
                # Process image with pose landmarks
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = st.session_state.fall_detector.pose.process(rgb_image)
                
                if results.pose_landmarks:
                    # Draw pose landmarks
                    annotated_image = st.session_state.fall_detector.draw_pose_landmarks(
                        image.copy(), results.pose_landmarks
                    )
                    annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
                    
                    st.image(annotated_image, caption="Pose Detection Results", use_column_width=True)
                    
                    # Display results
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Fall Detected", "YES" if fall_detected else "NO", 
                                delta="⚠️" if fall_detected else "✅")
                    with col_b:
                        if angle is not None:
                            st.metric("Torso Angle", f"{angle:.1f}°", 
                                    delta="Critical" if fall_detected else "Normal")
                    with col_c:
                        st.metric("Threshold", f"{angle_threshold}°")
                    
                    # Check for alert
                    if st.session_state.fusion_trigger.should_trigger_alert(fall_detected, False):
                        st.error("🚨 FALL ALERT TRIGGERED!")
                        alert_event = st.session_state.fusion_trigger.alert_history[-1]
                        st.session_state.alert_history.append({
                            'timestamp': datetime.now(),
                            'type': 'Fall Detection',
                            'message': alert_event.message,
                            'confidence': alert_event.confidence
                        })
                else:
                    st.warning("No pose detected in image. Please ensure person is visible.")
            else:
                st.image(image, caption="Original Image", use_column_width=True, channels="BGR")
        
        # Audio testing section
        st.header("🎤 Audio Detection Testing")
        
        if enable_audio:
            audio_file = st.file_uploader("Upload audio file for testing", type=['wav', 'mp3', 'm4a'])
            
            if audio_file is not None:
                st.audio(audio_file)
                
                if st.button("🔍 Analyze Audio"):
                    with st.spinner("Processing audio..."):
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(audio_file.read())
                            tmp_file_path = tmp_file.name
                        
                        try:
                            # Try to use librosa if available
                            try:
                                import librosa
                                audio_data, sr = librosa.load(tmp_file_path, sr=16000)
                            except ImportError:
                                # Fallback: create dummy audio data for testing
                                st.warning("Librosa not available. Using dummy audio analysis.")
                                # Create test audio data based on file size
                                import os
                                file_size = os.path.getsize(tmp_file_path)
                                # Simulate audio analysis based on file properties
                                audio_data = np.random.normal(0, 0.5, 16000)  # 1 second of test audio
                                sr = 16000
                            
                            # Detect help keywords
                            help_detected = st.session_state.whisper_detector.detect_help_keyword(
                                audio_data, sr
                            )
                            
                            # Display results
                            if help_detected:
                                st.success("🔊 Help keyword detected!")
                                
                                # Check for alert
                                if st.session_state.fusion_trigger.should_trigger_alert(False, help_detected):
                                    st.error("🚨 HELP ALERT TRIGGERED!")
                                    alert_event = st.session_state.fusion_trigger.alert_history[-1]
                                    st.session_state.alert_history.append({
                                        'timestamp': datetime.now(),
                                        'type': 'Audio Detection',
                                        'message': alert_event.message,
                                        'confidence': alert_event.confidence
                                    })
                            else:
                                st.info("No help keywords detected in audio.")
                                
                        except ImportError:
                            st.error("Please install librosa: pip install librosa")
                        except Exception as e:
                            st.error(f"Error processing audio: {e}")
                            st.info("Note: This is a simplified audio detector for testing.")
    
    with col2:
        st.header("📊 System Status")
        
        # Current status
        status_placeholder = st.empty()
        with status_placeholder.container():
            st.subheader("Current Status")
            
            # System health
            health_metrics = {
                "Pose Detection": "🟢 Active" if enable_pose else "🔴 Disabled",
                "Audio Detection": "🟢 Active" if enable_audio else "🔴 Disabled",
                "Alert System": "🟢 Ready",
                "Last Check": datetime.now().strftime("%H:%M:%S")
            }
            
            for metric, value in health_metrics.items():
                st.text(f"{metric}: {value}")
        
        # Alert history
        st.subheader("🚨 Recent Alerts")
        
        if st.session_state.alert_history:
            # Display recent alerts
            df_alerts = pd.DataFrame(st.session_state.alert_history[-10:])  # Last 10 alerts
            
            for _, alert in df_alerts.iterrows():
                with st.expander(f"{alert['type']} - {alert['timestamp'].strftime('%H:%M:%S')}"):
                    st.write(f"**Message:** {alert['message']}")
                    st.write(f"**Confidence:** {alert['confidence']:.1%}")
                    st.write(f"**Time:** {alert['timestamp']}")
            
            # Clear history button
            if st.button("🗑️ Clear Alert History"):
                st.session_state.alert_history = []
                st.session_state.fusion_trigger.clear_history()
                st.success("Alert history cleared!")
        else:
            st.info("No alerts yet")
        
        # Statistics
        if st.session_state.alert_history:
            st.subheader("📈 Statistics")
            
            df_stats = pd.DataFrame(st.session_state.alert_history)
            
            # Alert count by type
            type_counts = df_stats['type'].value_counts()
            fig_pie = px.pie(values=type_counts.values, names=type_counts.index, 
                           title="Alerts by Type")
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Alert timeline
            df_stats['hour'] = df_stats['timestamp'].dt.hour
            hourly_counts = df_stats.groupby('hour').size()
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=hourly_counts.index, y=hourly_counts.values,
                                        mode='lines+markers', name='Alerts per Hour'))
            fig_line.update_layout(title="Alert Timeline", xaxis_title="Hour", yaxis_title="Count")
            st.plotly_chart(fig_line, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("### 📖 Instructions")
    
    instructions = """
    **Pose Detection:**
    - Take a photo using the camera input above
    - The system will analyze body posture and detect potential falls
    - Red alerts indicate detected falls
    
    **Audio Detection:**
    - Upload an audio file containing speech
    - The system will detect help keywords like "help" or "救命"
    - Supported formats: WAV, MP3, M4A
    
    **Real-time Monitoring:**
    - For real-time detection, run `python main.py` in terminal
    - This dashboard is for testing and monitoring purposes
    """
    
    st.markdown(instructions)
    
    # Auto-refresh option
    if st.checkbox("Auto-refresh (5 seconds)"):
        time.sleep(5)
        st.experimental_rerun()

if __name__ == "__main__":
    main()
