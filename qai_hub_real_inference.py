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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Try to import QAI Hub, but don't fail if it doesn't work
try:
    import qai_hub as hub
    import qai_hub.models as models
    print("Successfully imported QAI Hub and QAI Hub Models")
    USING_REAL_QAI_HUB = True
except Exception as e:
    print(f"Error importing QAI Hub: {str(e)}")
    print("Falling back to simulation mode")
    USING_REAL_QAI_HUB = False

# Try to get QAI Hub models - we'll try several popular models
QAI_HUB_MODELS = [
    "qai-hub/yolov8n",
    "qai-hub/yolov8s",
    "qai-hub/pose-estimation-hrnet",
    "qai-hub/efficientnet-lite4",
    "qai-hub/squeezenet1-1",
    "qai-hub/mobilenet-v2-1.0",
    "qai-hub/mobilenetv3-small-minimalistic"
]

def get_qai_hub_model():
    """Try to get a working QAI Hub model for inference"""
    if not USING_REAL_QAI_HUB:
        logger.info("QAI Hub not available, using simulated model")
        return None
    
    # Try each model until one works
    for model_name in QAI_HUB_MODELS:
        try:
            logger.info(f"Trying to load QAI Hub model: {model_name}")
            model = hub.load(model_name)
            logger.info(f"Successfully loaded model: {model_name}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {str(e)}")
    
    logger.error("Could not load any QAI Hub model, using simulated model")
    return None

def get_qai_hub_devices():
    """Try to get available QAI Hub devices"""
    if not USING_REAL_QAI_HUB:
        logger.info("QAI Hub not available, using simulated devices")
        return None
    
    try:
        logger.info("Getting available QAI Hub devices...")
        devices = hub.get_devices()
        logger.info(f"Found {len(devices)} devices")
        for i, device in enumerate(devices):
            logger.info(f"Device {i+1}: {device.name} ({device.type})")
        return devices
    except Exception as e:
        logger.error(f"Failed to get QAI Hub devices: {str(e)}")
        return None

class FallDetectionSystem:
    """Fall Detection System using QAI Hub"""
    
    def __init__(self):
        self.frame_count = 0
        self.fall_count = 0
        self.last_fall_time = 0
        
        # Try to get QAI Hub devices
        self.devices = get_qai_hub_devices()
        
        # Try to get a QAI Hub model
        self.model = get_qai_hub_model()
        self.using_real_model = self.model is not None
        
        if self.using_real_model:
            logger.info("Using real QAI Hub model for inference")
        else:
            logger.info("Using simulated model for inference")
    
    def preprocess_image(self, image):
        """Preprocess image for QAI Hub model inference"""
        if not self.using_real_model:
            return image
        
        try:
            # Default preprocessing for many models
            resized = cv2.resize(image, (224, 224))
            # Convert to RGB (from BGR)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            # Normalize to [0,1]
            normalized = rgb.astype(np.float32) / 255.0
            # Add batch dimension
            batched = np.expand_dims(normalized, axis=0)
            return batched
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return image
    
    def detect_fall_real(self, image):
        """Use real QAI Hub model to detect falls"""
        if not self.using_real_model:
            return False
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Run inference with QAI Hub model
            result = self.model(processed_image)
            
            # Log the result structure for debugging
            if self.frame_count % 100 == 0:
                logger.info(f"QAI Hub model result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
                if isinstance(result, dict) and 'predictions' in result:
                    logger.info(f"Predictions shape: {result['predictions'].shape}")
            
            # For demonstration purposes, we'll use a simple heuristic based on the model output
            # This should be adapted based on the specific model being used
            if isinstance(result, dict) and 'predictions' in result:
                predictions = result['predictions']
                # Just a simple heuristic - in a real system, this would be more sophisticated
                max_val = np.max(predictions)
                # If the maximum activation is above 0.8, consider it a fall
                if max_val > 0.8:
                    self.fall_count += 1
                    logger.info(f"Fall detected by QAI Hub model! Max activation: {max_val:.4f}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error during real inference: {str(e)}")
            return False
    
    def detect_fall_simulated(self):
        """Simulate fall detection when QAI Hub model is not available"""
        # Simple simulation - detect a fall randomly with 1% probability
        # but not more frequently than every 3 seconds
        current_time = time.time()
        if current_time - self.last_fall_time > 3.0:
            is_fall = (random.random() < 0.01)
            if is_fall:
                self.fall_count += 1
                self.last_fall_time = current_time
                logger.info(f"Fall detected (simulated)! (#{self.fall_count})")
                return True
        return False
    
    def process_frame(self, frame):
        """Process a video frame to detect falls"""
        self.frame_count += 1
        
        # Try to use real QAI Hub model first
        if self.using_real_model:
            is_fall = self.detect_fall_real(frame)
        else:
            # Fall back to simulation
            is_fall = self.detect_fall_simulated()
        
        return frame, is_fall
    
    def run(self):
        """Run the fall detection system on webcam video"""
        try:
            # Open webcam
            logger.info("Opening camera...")
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                logger.error("Cannot open camera")
                return
            
            logger.info("Starting to process video stream...")
            
            # For FPS calculation
            fps_start_time = time.time()
            fps_frame_count = 0
            fps = 0
            
            while True:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to read image")
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
                
                # Draw model type
                model_text = "Real QAI Hub Model" if self.using_real_model else "Simulated Model"
                cv2.putText(processed_frame, model_text, (10, processed_frame.shape[0] - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
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
                cv2.imshow("Fall Detection System with QAI Hub", processed_frame)
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("User requested exit")
                    break
                
                # Print status every 30 frames
                if self.frame_count % 30 == 0:
                    logger.info(f"Processed {self.frame_count} frames, FPS: {fps:.1f}")
                
        except KeyboardInterrupt:
            logger.info("User interrupted")
        except Exception as e:
            logger.error(f"Error during execution: {str(e)}")
        finally:
            # Clean up
            if 'cap' in locals() and cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            
            # Print summary
            logger.info("System execution summary:")
            logger.info(f"  - Using real QAI Hub model: {self.using_real_model}")
            logger.info(f"  - Total frames processed: {self.frame_count}")
            logger.info(f"  - Falls detected: {self.fall_count}")
            logger.info("Fall Detection System closed")

def main():
    """Main function to run the Fall Detection System"""
    print("Fall Detection System with QAI Hub")
    print("============================================")
    print("Attempting to use real QAI Hub model for inference")
    print("")
    
    try:
        # Initialize the system
        system = FallDetectionSystem()
        
        # Run the system
        system.run()
        
    except Exception as e:
        print(f"System execution failed: {str(e)}")
        
if __name__ == "__main__":
    main()
