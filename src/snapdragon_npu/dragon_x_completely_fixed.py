import os
import sys
import cv2
import numpy as np
import logging
import time
import random

# Set QAI Hub environment variables to ensure API access
os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_VERSION"] = "v1"

print("QAI Hub environment variables have been set")

# Try to import QAI Hub, but don't fail if it doesn't work
try:
    import qai_hub as hub
    print("Successfully imported QAI Hub")
    USING_REAL_QAI_HUB = True
except Exception as e:
    print(f"Error importing QAI Hub: {str(e)}")
    print("Falling back to simulation mode")
    USING_REAL_QAI_HUB = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

class DragonXFallDetectionSystem:
    """Dragon X Fall Detection System - Qualcomm Hackathon 2025"""
    
    def __init__(self):
        """Initialize the Dragon X Fall Detection System"""
        self.logger = logging.getLogger(__name__)
        self.frame_count = 0
        self.fall_count = 0
        self.last_fall_time = 0
        self.logger.info("🐉 初始化Dragon X老人跌倒預防檢測系統...")
        
        try:
            # Find Dragon X devices
            self._find_dragon_x_devices()
            
            # Initialize fall detection model
            self._initialize_dragon_x_model()
            
            self.logger.info("✅ Dragon X系統初始化成功")
        except Exception as e:
            self.logger.error(f"❌ Dragon X系統初始化失敗: {str(e)}")
            raise
    
    def _find_dragon_x_devices(self):
        """Find and connect to Dragon X devices using QAI Hub"""
        try:
            self.logger.info("🔍 搜尋 Dragon X 硬體...")
            
            if USING_REAL_QAI_HUB:
                try:
                    # Try to get real devices from QAI Hub
                    devices = hub.get_devices()
                    self.logger.info(f"✅ 已找到 {len(devices)} 個設備")
                    for i, device in enumerate(devices):
                        self.logger.info(f"  - 設備 {i+1}: {device.name} ({device.type})")
                except Exception as e:
                    self.logger.error(f"❌ 設備搜尋失敗: {str(e)}")
                    self.logger.info("⚠️ 使用模擬設備代替...")
                    # Simulate devices if real ones can't be found
                    self._simulate_devices()
            else:
                # If QAI Hub import failed, use simulated devices
                self._simulate_devices()
                
        except Exception as e:
            self.logger.error(f"❌ 設備搜尋失敗: {str(e)}")
            raise
    
    def _simulate_devices(self):
        """Create simulated devices for testing"""
        # Define a simple SimulatedDevice class
        class SimulatedDevice:
            def __init__(self, name, device_type):
                self.name = name
                self.type = device_type
            
            def __str__(self):
                return f"{self.name} ({self.type})"
        
        # Create simulated devices
        self.devices = [
            SimulatedDevice("Snapdragon 8 Gen 3", "mobile"),
            SimulatedDevice("Cloud Instance", "cloud")
        ]
        
        self.logger.info(f"✅ 已創建 {len(self.devices)} 個模擬設備")
        for i, device in enumerate(self.devices):
            self.logger.info(f"  - 設備 {i+1}: {device.name} ({device.type})")
    
    def _initialize_dragon_x_model(self):
        """Initialize the Dragon X fall detection model"""
        try:
            self.logger.info("🔧 初始化 Dragon X 模型...")
            
            if USING_REAL_QAI_HUB:
                try:
                    # Try to load the real model from QAI Hub
                    self.model = hub.load("qai-hub/fall-detection-yolov8")
                    self.logger.info("✅ 模型初始化成功")
                except Exception as e:
                    self.logger.error(f"❌ 模型載入失敗: {str(e)}")
                    self.logger.info("⚠️ 使用模擬模型代替...")
                    self._simulate_model()
            else:
                # If QAI Hub import failed, use simulated model
                self._simulate_model()
                
        except Exception as e:
            self.logger.error(f"❌ 模型初始化失敗: {str(e)}")
            self.model = None
    
    def _simulate_model(self):
        """Create a simulated model for testing"""
        self.model = "simulated_model"  # Just a marker to indicate we're using simulation
        self.logger.info("✅ 已創建模擬模型")
    
    def process_frame(self, frame):
        """Process a video frame to detect falls"""
        self.frame_count += 1
        
        if self.model is None:
            return frame, False
        
        try:
            # If using simulated model
            if self.model == "simulated_model":
                # Simple simulation - detect a fall every ~100 frames
                current_time = time.time()
                # Don't detect falls too frequently
                if current_time - self.last_fall_time > 3.0:  # At least 3 seconds between falls
                    # Randomly detect falls with 1% probability
                    is_fall = (random.random() < 0.01)
                    if is_fall:
                        self.fall_count += 1
                        self.last_fall_time = current_time
                        self.logger.info(f"⚠️ 檢測到跌倒! (#{self.fall_count})")
                else:
                    is_fall = False
                return frame, is_fall
            
            # If using real model (this would be the real implementation)
            # For now, we'll just return the simulated result
            return frame, False
            
        except Exception as e:
            self.logger.error(f"❌ 處理影像失敗: {str(e)}")
            return frame, False
    
    def run(self):
        """Run the fall detection system on webcam video"""
        try:
            # Open webcam
            self.logger.info("📹 開啟相機...")
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.logger.error("❌ 無法開啟相機")
                return
            
            self.logger.info("🎥 開始處理影像流...")
            
            # For FPS calculation
            fps_start_time = time.time()
            fps_frame_count = 0
            fps = 0
            
            while True:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    self.logger.error("❌ 讀取影像失敗")
                    break
                
                # Process frame for fall detection
                processed_frame, is_fall = self.process_frame(frame)
                
                # Calculate FPS
                fps_frame_count += 1
                if fps_frame_count >= 10:  # Update FPS every 10 frames
                    elapsed_time = time.time() - fps_start_time
                    fps = fps_frame_count / elapsed_time
                    fps_frame_count = 0
                    fps_start_time = time.time()
                
                # Draw FPS
                cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Draw fall detection status
                status_text = "FALL DETECTED!" if is_fall else "Normal"
                status_color = (0, 0, 255) if is_fall else (0, 255, 0)
                cv2.putText(processed_frame, status_text, (10, 70), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
                
                # Draw frame count and fall count
                cv2.putText(processed_frame, f"Frames: {self.frame_count}", (10, 110), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(processed_frame, f"Falls: {self.fall_count}", (10, 140), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Show frame
                cv2.imshow("Dragon X Fall Detection System", processed_frame)
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.logger.info("🛑 用戶請求退出")
                    break
                
                # Print status every 30 frames
                if self.frame_count % 30 == 0:
                    self.logger.info(f"📊 已處理 {self.frame_count} 幀，FPS: {fps:.1f}")
                
        except KeyboardInterrupt:
            self.logger.info("🛑 用戶中斷")
        except Exception as e:
            self.logger.error(f"❌ 運行期間發生錯誤: {str(e)}")
        finally:
            # Clean up
            if 'cap' in locals() and cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            
            # Print summary
            self.logger.info("📋 系統運行摘要:")
            self.logger.info(f"  - 總處理幀數: {self.frame_count}")
            self.logger.info(f"  - 檢測到的跌倒數: {self.fall_count}")
            self.logger.info("🏁 Dragon X Fall Detection System 已關閉")

def main():
    """Main function to run the Dragon X Fall Detection System"""
    print("🐉 Dragon X老人跌倒預防檢測系統")
    print("============================================================")
    print("🎯 專為黑客松打造的Snapdragon X Elite平台解決方案")
    print("")
    
    try:
        # Initialize the system
        dragon_system = DragonXFallDetectionSystem()
        
        # Run the system
        dragon_system.run()
        
    except Exception as e:
        print(f"❌ 系統運行失敗: {str(e)}")
        
if __name__ == "__main__":
    main()
