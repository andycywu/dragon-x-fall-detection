#!/usr/bin/env python3
"""
🎯 QAI Hub 一般Web Demo
HTML/JavaScript實時老人行為檢測系統
"""

import cv2
import numpy as np
import os
import time
import json
import base64
from datetime import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QAIHubWebDemo:
    def __init__(self):
        """初始化Web Demo系統"""
        self.detector = None
        self.predictor = None
        self.camera = None
        self.is_streaming = False
        self.load_systems()
    
    def load_systems(self):
        """載入檢測系統"""
        try:
            from official_qai_hub_detector import OfficialQAIHubDetector
            from elderly_behavior_predictor import ElderlyBehaviorPredictor
            
            self.detector = OfficialQAIHubDetector()
            self.predictor = ElderlyBehaviorPredictor()
            
            logger.info("✅ QAI Hub檢測系統載入成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 檢測系統載入失敗: {e}")
            return False
    
    def process_image(self, image_data):
        """處理圖像數據"""
        try:
            # 解碼base64圖像
            if 'data:image' in image_data:
                image_data = image_data.split(',')[1]
            
            img_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {'error': '無法解碼圖像'}
            
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 執行檢測
            unified_result = self.detector.unified_detection(rgb_image)
            
            # 行為分析
            user_id = f"web_user_{int(time.time())}"
            interaction_result = self.predictor.process_user_interaction(user_id, image)
            
            # 生成標註圖像
            annotated_images = {}
            
            # 人臉檢測結果
            face_result = self.detector.detect_faces(rgb_image, raw_output=False)
            if face_result.get('success') and 'annotated_image' in face_result:
                annotated_images['face'] = self.image_to_base64(face_result['annotated_image'])
            
            # 姿態檢測結果
            pose_result = self.detector.detect_pose(rgb_image, raw_output=False)
            if pose_result.get('success') and 'annotated_image' in pose_result:
                annotated_images['pose'] = self.image_to_base64(pose_result['annotated_image'])
            
            # 手部檢測結果
            hand_result = self.detector.detect_hands(rgb_image, raw_output=False)
            if hand_result.get('success') and 'annotated_image' in hand_result:
                annotated_images['hand'] = self.image_to_base64(hand_result['annotated_image'])
            
            return {
                'success': True,
                'unified_result': unified_result,
                'interaction_result': interaction_result,
                'annotated_images': annotated_images,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"處理圖像錯誤: {e}")
            return {'error': str(e)}
    
    def image_to_base64(self, image):
        """將圖像轉換為base64格式"""
        try:
            if isinstance(image, np.ndarray):
                if len(image.shape) == 3 and image.shape[2] == 3:
                    # RGB to BGR for OpenCV
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                _, buffer = cv2.imencode('.jpg', image)
                img_str = base64.b64encode(buffer).decode('utf-8')
                return f"data:image/jpeg;base64,{img_str}"
            return None
        except Exception as e:
            logger.error(f"圖像編碼錯誤: {e}")
            return None
    
    def start_camera_stream(self):
        """啟動攝影機串流"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return False
            
            self.is_streaming = True
            return True
        except Exception as e:
            logger.error(f"攝影機啟動失敗: {e}")
            return False
    
    def stop_camera_stream(self):
        """停止攝影機串流"""
        self.is_streaming = False
        if self.camera:
            self.camera.release()
    
    def get_camera_frame(self):
        """獲取攝影機幀"""
        if not self.camera or not self.is_streaming:
            return None
        
        ret, frame = self.camera.read()
        if not ret:
            return None
        
        # 處理幀
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 執行檢測
        unified_result = self.detector.unified_detection(rgb_frame)
        
        # 行為分析
        user_id = f"camera_user_{int(time.time())}"
        interaction_result = self.predictor.process_user_interaction(user_id, frame)
        
        return {
            'frame': self.image_to_base64(rgb_frame),
            'unified_result': unified_result,
            'interaction_result': interaction_result
        }

class DemoRequestHandler(BaseHTTPRequestHandler):
    """HTTP請求處理器"""
    
    def __init__(self, *args, demo_instance=None, **kwargs):
        self.demo = demo_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """處理GET請求"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_html()
        elif self.path == '/style.css':
            self.serve_css()
        elif self.path == '/script.js':
            self.serve_js()
        elif self.path == '/api/camera/start':
            self.handle_camera_start()
        elif self.path == '/api/camera/stop':
            self.handle_camera_stop()
        elif self.path == '/api/camera/frame':
            self.handle_camera_frame()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """處理POST請求"""
        if self.path == '/api/process_image':
            self.handle_process_image()
        else:
            self.send_error(404)
    
    def serve_html(self):
        """提供HTML頁面"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QAI Hub 老人行為檢測系統</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 QAI Hub 老人行為檢測系統</h1>
            <p>基於Qualcomm AI Hub的實時老人行為監測與風險評估</p>
        </header>
        
        <div class="demo-tabs">
            <button class="tab-button active" onclick="showTab('upload')">📷 圖像上傳</button>
            <button class="tab-button" onclick="showTab('camera')">📹 網路攝影機</button>
            <button class="tab-button" onclick="showTab('samples')">🖼️ 示例圖像</button>
        </div>
        
        <!-- 圖像上傳標籤 -->
        <div id="upload-tab" class="tab-content active">
            <h2>📷 圖像上傳檢測</h2>
            <div class="upload-area">
                <input type="file" id="image-upload" accept="image/*" onchange="handleImageUpload(event)">
                <div class="upload-preview">
                    <img id="preview-image" style="display: none;">
                </div>
            </div>
        </div>
        
        <!-- 攝影機標籤 -->
        <div id="camera-tab" class="tab-content">
            <h2>📹 網路攝影機實時檢測</h2>
            <div class="camera-controls">
                <button id="start-camera" onclick="startCamera()">🎥 啟動攝影機</button>
                <button id="stop-camera" onclick="stopCamera()" disabled>⏹️ 停止攝影機</button>
            </div>
            <div class="camera-view">
                <video id="camera-video" style="display: none;" autoplay></video>
                <canvas id="camera-canvas" style="display: none;"></canvas>
            </div>
        </div>
        
        <!-- 示例圖像標籤 -->
        <div id="samples-tab" class="tab-content">
            <h2>🖼️ 示例圖像檢測</h2>
            <div class="samples-grid">
                <div class="sample-item" onclick="loadSample('andy.jpg')">
                    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="Andy">
                    <p>Andy 測試圖像</p>
                </div>
            </div>
        </div>
        
        <!-- 結果顯示區域 -->
        <div id="results-section" class="results-section" style="display: none;">
            <h2>🔍 檢測結果</h2>
            
            <!-- 統計指標 -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>👤 人臉檢測</h3>
                    <span id="face-count">0</span>個
                </div>
                <div class="metric-card">
                    <h3>🚶 姿態檢測</h3>
                    <span id="pose-count">0</span>個
                </div>
                <div class="metric-card">
                    <h3>✋ 手部檢測</h3>
                    <span id="hand-count">0</span>個
                </div>
            </div>
            
            <!-- 行為分析 -->
            <div class="analysis-section">
                <h3>🧠 行為分析</h3>
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <h4>⚖️ 平衡評分</h4>
                        <span id="balance-score">--</span>
                    </div>
                    <div class="analysis-item">
                        <h4>🎯 穩定性評分</h4>
                        <span id="stability-score">--</span>
                    </div>
                    <div class="analysis-item">
                        <h4>📐 姿態偏差</h4>
                        <span id="posture-deviation">--</span>
                    </div>
                </div>
            </div>
            
            <!-- 風險評估 -->
            <div class="risk-section">
                <h3>🚨 風險評估</h3>
                <div id="risk-alert" class="risk-alert">
                    <div id="risk-level">--</div>
                    <div id="risk-score">評分: --</div>
                </div>
            </div>
            
            <!-- 視覺化結果 -->
            <div class="visualization-section">
                <h3>🖼️ 檢測結果視覺化</h3>
                <div class="images-grid">
                    <div class="image-result">
                        <h4>👤 人臉檢測</h4>
                        <img id="face-result" style="display: none;">
                    </div>
                    <div class="image-result">
                        <h4>🚶 姿態檢測</h4>
                        <img id="pose-result" style="display: none;">
                    </div>
                    <div class="image-result">
                        <h4>✋ 手部檢測</h4>
                        <img id="hand-result" style="display: none;">
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 載入指示器 -->
        <div id="loading" class="loading" style="display: none;">
            <div class="spinner"></div>
            <p>🔍 正在執行QAI Hub檢測...</p>
        </div>
    </div>
    
    <script src="/script.js"></script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_css(self):
        """提供CSS樣式"""
        css_content = """
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
    color: white;
}

header h1 {
    font-size: 3rem;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

header p {
    font-size: 1.2rem;
    opacity: 0.9;
}

.demo-tabs {
    display: flex;
    justify-content: center;
    margin-bottom: 30px;
    gap: 10px;
}

.tab-button {
    padding: 12px 24px;
    border: none;
    border-radius: 25px;
    background: rgba(255,255,255,0.2);
    color: white;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.tab-button:hover {
    background: rgba(255,255,255,0.3);
    transform: translateY(-2px);
}

.tab-button.active {
    background: white;
    color: #667eea;
    font-weight: bold;
}

.tab-content {
    display: none;
    background: white;
    border-radius: 15px;
    padding: 30px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.tab-content.active {
    display: block;
}

.upload-area {
    border: 2px dashed #ddd;
    border-radius: 10px;
    padding: 40px;
    text-align: center;
    margin-bottom: 20px;
}

.upload-area:hover {
    border-color: #667eea;
    background: #f8f9ff;
}

#image-upload {
    margin-bottom: 20px;
}

.upload-preview img {
    max-width: 100%;
    max-height: 400px;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.camera-controls {
    text-align: center;
    margin-bottom: 20px;
}

.camera-controls button {
    padding: 12px 24px;
    margin: 0 10px;
    border: none;
    border-radius: 25px;
    background: #667eea;
    color: white;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
}

.camera-controls button:hover {
    background: #5a6fd8;
    transform: translateY(-2px);
}

.camera-controls button:disabled {
    background: #ccc;
    cursor: not-allowed;
    transform: none;
}

.camera-view {
    text-align: center;
}

.samples-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
}

.sample-item {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}

.sample-item:hover {
    border-color: #667eea;
    background: #f8f9ff;
    transform: translateY(-2px);
}

.results-section {
    background: white;
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background: #f8f9ff;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    border-left: 4px solid #667eea;
}

.metric-card h3 {
    margin-bottom: 10px;
    color: #667eea;
}

.metric-card span {
    font-size: 2rem;
    font-weight: bold;
    color: #333;
}

.analysis-section, .risk-section, .visualization-section {
    margin-bottom: 30px;
}

.analysis-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
}

.analysis-item {
    background: #f8f9ff;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}

.analysis-item h4 {
    margin-bottom: 8px;
    color: #667eea;
    font-size: 0.9rem;
}

.analysis-item span {
    font-size: 1.5rem;
    font-weight: bold;
}

.risk-alert {
    background: #f0fff4;
    border: 1px solid #38a169;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}

.risk-alert.high {
    background: #fee;
    border-color: #c53030;
    color: #c53030;
}

.risk-alert.medium {
    background: #fffbf0;
    border-color: #d69e2e;
    color: #d69e2e;
}

.risk-alert.low {
    background: #f0fff4;
    border-color: #38a169;
    color: #38a169;
}

.images-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.image-result {
    text-align: center;
}

.image-result h4 {
    margin-bottom: 10px;
    color: #667eea;
}

.image-result img {
    max-width: 100%;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.loading {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.8);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    z-index: 1000;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 5px solid #667eea;
    border-top: 5px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    header h1 {
        font-size: 2rem;
    }
    
    .demo-tabs {
        flex-direction: column;
    }
    
    .tab-content {
        padding: 20px;
    }
    
    .metrics-grid,
    .images-grid {
        grid-template-columns: 1fr;
    }
}
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/css')
        self.end_headers()
        self.wfile.write(css_content.encode('utf-8'))
    
    def serve_js(self):
        """提供JavaScript代碼"""
        js_content = """
// 全局變量
let currentStream = null;
let isProcessing = false;

// 標籤切換
function showTab(tabName) {
    // 隱藏所有標籤內容
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // 移除所有按鈕的active類
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // 顯示選中的標籤
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

// 處理圖像上傳
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('preview-image');
        preview.src = e.target.result;
        preview.style.display = 'block';
        
        // 處理圖像
        processImage(e.target.result);
    };
    reader.readAsDataURL(file);
}

// 處理圖像
async function processImage(imageData) {
    if (isProcessing) return;
    isProcessing = true;
    
    showLoading(true);
    
    try {
        const response = await fetch('/api/process_image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            alert('處理失敗: ' + (result.error || '未知錯誤'));
        }
    } catch (error) {
        console.error('處理圖像錯誤:', error);
        alert('處理圖像時發生錯誤: ' + error.message);
    } finally {
        showLoading(false);
        isProcessing = false;
    }
}

// 顯示結果
function displayResults(result) {
    const resultsSection = document.getElementById('results-section');
    resultsSection.style.display = 'block';
    
    // 更新統計
    const unified = result.unified_result || {};
    const totals = unified.total_detections || {};
    
    document.getElementById('face-count').textContent = totals.faces || 0;
    document.getElementById('pose-count').textContent = totals.poses || 0;
    document.getElementById('hand-count').textContent = totals.hands || 0;
    
    // 更新行為分析
    const interaction = result.interaction_result || {};
    const poseAnalysis = interaction.pose_analysis || {};
    
    if (poseAnalysis && !poseAnalysis.error) {
        document.getElementById('balance-score').textContent = 
            (poseAnalysis.balance_score || 0).toFixed(2);
        document.getElementById('stability-score').textContent = 
            (poseAnalysis.stability_score || 0).toFixed(2);
        document.getElementById('posture-deviation').textContent = 
            (poseAnalysis.posture_deviation || 0).toFixed(2);
    }
    
    // 更新風險評估
    const riskAssessment = interaction.risk_assessment || {};
    if (riskAssessment.level) {
        const riskAlert = document.getElementById('risk-alert');
        const riskLevel = document.getElementById('risk-level');
        const riskScore = document.getElementById('risk-score');
        
        riskLevel.textContent = getRiskIcon(riskAssessment.level) + ' ' + 
                               riskAssessment.level.toUpperCase();
        riskScore.textContent = '評分: ' + (riskAssessment.score || 0).toFixed(2);
        
        // 設置風險等級樣式
        riskAlert.className = 'risk-alert ' + riskAssessment.level;
    }
    
    // 顯示標註圖像
    const annotated = result.annotated_images || {};
    
    if (annotated.face) {
        const faceImg = document.getElementById('face-result');
        faceImg.src = annotated.face;
        faceImg.style.display = 'block';
    }
    
    if (annotated.pose) {
        const poseImg = document.getElementById('pose-result');
        poseImg.src = annotated.pose;
        poseImg.style.display = 'block';
    }
    
    if (annotated.hand) {
        const handImg = document.getElementById('hand-result');
        handImg.src = annotated.hand;
        handImg.style.display = 'block';
    }
    
    // 滾動到結果區域
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// 獲取風險等級圖標
function getRiskIcon(level) {
    switch(level) {
        case 'high': return '🔴';
        case 'medium': return '🟡';
        case 'low': return '🟢';
        default: return '⚪';
    }
}

// 啟動攝影機
async function startCamera() {
    try {
        const response = await fetch('/api/camera/start');
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('start-camera').disabled = true;
            document.getElementById('stop-camera').disabled = false;
            
            // 啟動本地攝影機預覽
            const video = document.getElementById('camera-video');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.style.display = 'block';
            currentStream = stream;
            
            // 開始處理幀
            startFrameProcessing();
        } else {
            alert('啟動攝影機失敗: ' + (result.error || '未知錯誤'));
        }
    } catch (error) {
        console.error('攝影機錯誤:', error);
        alert('攝影機錯誤: ' + error.message);
    }
}

// 停止攝影機
async function stopCamera() {
    try {
        await fetch('/api/camera/stop');
        
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
        }
        
        document.getElementById('camera-video').style.display = 'none';
        document.getElementById('start-camera').disabled = false;
        document.getElementById('stop-camera').disabled = true;
    } catch (error) {
        console.error('停止攝影機錯誤:', error);
    }
}

// 開始幀處理
function startFrameProcessing() {
    if (!currentStream) return;
    
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    const ctx = canvas.getContext('2d');
    
    function processFrame() {
        if (!currentStream) return;
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        
        // 每2秒處理一次幀
        const imageData = canvas.toDataURL('image/jpeg', 0.8);
        processImage(imageData);
        
        setTimeout(processFrame, 2000);
    }
    
    // 等待視頻載入
    video.addEventListener('loadedmetadata', () => {
        setTimeout(processFrame, 1000);
    });
}

// 載入示例圖像
function loadSample(imageName) {
    // 這裡可以實現載入示例圖像的邏輯
    alert('載入示例圖像: ' + imageName);
}

// 顯示/隱藏載入指示器
function showLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'flex' : 'none';
}

// 頁面載入完成時的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('QAI Hub Web Demo 已載入');
});
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.end_headers()
        self.wfile.write(js_content.encode('utf-8'))
    
    def handle_process_image(self):
        """處理圖像處理請求"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            image_data = data.get('image')
            if not image_data:
                self.send_json_response({'error': '沒有圖像數據'})
                return
            
            result = self.demo.process_image(image_data)
            self.send_json_response(result)
            
        except Exception as e:
            logger.error(f"處理圖像請求錯誤: {e}")
            self.send_json_response({'error': str(e)})
    
    def handle_camera_start(self):
        """處理攝影機啟動請求"""
        success = self.demo.start_camera_stream()
        self.send_json_response({'success': success})
    
    def handle_camera_stop(self):
        """處理攝影機停止請求"""
        self.demo.stop_camera_stream()
        self.send_json_response({'success': True})
    
    def handle_camera_frame(self):
        """處理攝影機幀請求"""
        frame_data = self.demo.get_camera_frame()
        if frame_data:
            self.send_json_response({'success': True, 'data': frame_data})
        else:
            self.send_json_response({'success': False, 'error': '無法獲取攝影機幀'})
    
    def send_json_response(self, data):
        """發送JSON響應"""
        response = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

def create_handler(demo_instance):
    """創建請求處理器"""
    def handler(*args, **kwargs):
        return DemoRequestHandler(*args, demo_instance=demo_instance, **kwargs)
    return handler

def main():
    """主函數"""
    print("🚀 啟動QAI Hub Web Demo...")
    
    # 初始化Demo系統
    demo = QAIHubWebDemo()
    
    # 創建HTTP服務器
    port = 8080
    server = HTTPServer(('localhost', port), create_handler(demo))
    
    print(f"✅ Web服務器已啟動")
    print(f"🌐 請訪問: http://localhost:{port}")
    print("按 Ctrl+C 停止服務器")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 停止服務器...")
        demo.stop_camera_stream()
        server.shutdown()

if __name__ == "__main__":
    main()
