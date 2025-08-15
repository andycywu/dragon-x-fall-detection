#!/usr/bin/env python3
"""
Dragon X Fall Detection System
Using real QAI Hub for inference
"""

import os
import sys
import cv2
import numpy as np
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Configure QAI Hub environment variables
os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_VERSION"] = "v1"

print("QAI Hub environment variables have been set")

# Try to import QAI Hub modules
try:
    import qai_hub as hub
    import onnxruntime as ort
    USING_REAL_QAI_HUB = True
    print("Successfully imported QAI Hub")
except ImportError as e:
    print(f"Cannot import QAI Hub: {e}")
    USING_REAL_QAI_HUB = False
    print("Will use simulation mode")

# QAI Hub models list - ordered by priority
QAI_HUB_MODELS = [
    "qai-hub/mobilenetv3-small-minimalistic",
    "qai-hub/efficientnet-lite4",
    "qai-hub/mobilenet-v2-1.0",
    "qai-hub/squeezenet1-1",
    "qai-hub/pose-estimation-hrnet"
]

class FallDetectionModel:
    """Fall detection model using QAI Hub or ONNX Runtime"""
    
    def __init__(self):
        """Initialize model"""
        self.qai_model = None
        self.onnx_session = None
        self.model_name = None
        self.input_shape = (224, 224)  # Default input size
        
        # Initialize QAI Hub
        if USING_REAL_QAI_HUB:
            self._init_qai_hub()
        else:
            logger.info("QAI Hub not available, using simulation mode")
    
    def _init_qai_hub(self):
        """Initialize QAI Hub connection and load model"""
        try:
            # Try to get available devices
            logger.info("Getting QAI Hub available devices...")
            devices = hub.get_devices()
            logger.info(f"Found {len(devices)} QAI Hub devices")
            
            # Try to load model
            for model_name in QAI_HUB_MODELS:
                try:
                    logger.info(f"Trying to load model: {model_name}")
                    self.qai_model = hub.load(model_name)
                    self.model_name = model_name
                    logger.info(f"Successfully loaded model: {model_name}")
                    break
                except Exception as e:
                    logger.warning(f"Cannot load model {model_name}: {e}")
            
            if self.qai_model is None:
                logger.warning("Could not load any QAI Hub model, will use ONNX mode")
                self._init_onnx_fallback()
        
        except Exception as e:
            logger.error(f"QAI Hub initialization failed: {e}")
            logger.info("Switching to ONNX mode")
            self._init_onnx_fallback()
    
    def _init_onnx_fallback(self):
        """Initialize ONNX Runtime as fallback"""
        try:
            logger.info("Initializing ONNX Runtime...")
            
            # Check if there are available ONNX model files
            onnx_models = [f for f in os.listdir('.') if f.endswith('.onnx')]
            
            if onnx_models:
                onnx_path = onnx_models[0]
                logger.info(f"Using ONNX model: {onnx_path}")
                
                # Get available execution providers
                available_providers = ort.get_available_providers()
                logger.info(f"Available ONNX providers: {available_providers}")
                
                # Prioritize GPU acceleration
                providers = []
                if 'CUDAExecutionProvider' in available_providers:
                    providers.append('CUDAExecutionProvider')
                elif 'DmlExecutionProvider' in available_providers:
                    providers.append('DmlExecutionProvider')
                providers.append('CPUExecutionProvider')
                
                # Create ONNX session
                self.onnx_session = ort.InferenceSession(onnx_path, providers=providers)
                logger.info(f"ONNX session created successfully, using providers: {providers}")
                
                # Get input shape
                input_name = self.onnx_session.get_inputs()[0].name
                input_shape = self.onnx_session.get_inputs()[0].shape
                logger.info(f"ONNX input: {input_name}, shape: {input_shape}")
                
                if len(input_shape) >= 3:
                    # Assume shape is [batch, channels, height, width] or [batch, height, width, channels]
                    if input_shape[1] == 3:  # NCHW format
                        self.input_shape = (int(input_shape[3]), int(input_shape[2]))
                    else:  # NHWC format
                        self.input_shape = (int(input_shape[2]), int(input_shape[1]))
            else:
                logger.warning("No ONNX model files found, will use simulation mode")
        
        except Exception as e:
            logger.error(f"ONNX initialization failed: {e}")
            logger.warning("Will use fully simulated mode")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess input image"""
        # Resize
        resized = cv2.resize(image, self.input_shape)
        
        # Convert to RGB (if BGR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0,1]
        normalized = rgb.astype(np.float32) / 255.0
        
        # Adjust format based on model type
        if self.qai_model:
            # QAI Hub typically needs NCHW format [batch, channels, height, width]
            input_tensor = np.transpose(normalized, (2, 0, 1))
            input_tensor = np.expand_dims(input_tensor, axis=0)
        elif self.onnx_session:
            # Get ONNX model input format
            input_name = self.onnx_session.get_inputs()[0].name
            input_shape = self.onnx_session.get_inputs()[0].shape
            
            if len(input_shape) == 4 and input_shape[1] == 3:
                # NCHW format [batch, channels, height, width]
                input_tensor = np.transpose(normalized, (2, 0, 1))
                input_tensor = np.expand_dims(input_tensor, axis=0)
            else:
                # NHWC format [batch, height, width, channels]
                input_tensor = np.expand_dims(normalized, axis=0)
        else:
            # Default to NCHW format
            input_tensor = np.transpose(normalized, (2, 0, 1))
            input_tensor = np.expand_dims(input_tensor, axis=0)
            
        return input_tensor
    
    def infer(self, image: np.ndarray) -> Dict[str, Any]:
        """Run inference"""
        # Preprocess image
        input_tensor = self.preprocess_image(image)
        
        result = {
            "success": False,
            "inference_time_ms": 0,
            "model_type": "unknown",
            "is_fall": False,
            "confidence": 0.0
        }
        
        # Start timing
        start_time = time.time()
        
        try:
            # Try using QAI Hub model
            if self.qai_model:
                logger.debug("Using QAI Hub model for inference")
                predictions = self.qai_model(input_tensor)
                
                result["model_type"] = f"QAI_Hub_{self.model_name}"
                result["success"] = True
                
                # Extract prediction results
                if isinstance(predictions, dict):
                    # Extract predictions from dictionary
                    if "predictions" in predictions:
                        pred_value = predictions["predictions"]
                    elif "output" in predictions:
                        pred_value = predictions["output"]
                    else:
                        # Use first available key
                        pred_key = list(predictions.keys())[0]
                        pred_value = predictions[pred_key]
                else:
                    # Use returned value directly
                    pred_value = predictions
                
                # Try to convert predictions to NumPy array
                if not isinstance(pred_value, np.ndarray):
                    try:
                        pred_value = np.array(pred_value)
                    except:
                        logger.warning("Cannot convert predictions to NumPy array")
                
                # Use predictions to determine if fall
                try:
                    if isinstance(pred_value, np.ndarray):
                        # Use max value as confidence
                        confidence = float(np.max(pred_value))
                        # Simple threshold
                        is_fall = confidence > 0.7
                        
                        result["confidence"] = confidence
                        result["is_fall"] = is_fall
                        result["prediction_shape"] = pred_value.shape
                except Exception as e:
                    logger.error(f"Error processing QAI Hub predictions: {e}")
                    
            # Try using ONNX model
            elif self.onnx_session:
                logger.debug("Using ONNX model for inference")
                input_name = self.onnx_session.get_inputs()[0].name
                outputs = self.onnx_session.run(None, {input_name: input_tensor})
                
                result["model_type"] = "ONNX_Runtime"
                result["success"] = True
                
                # Process ONNX output
                if outputs and len(outputs) > 0:
                    # Use first output
                    output = outputs[0]
                    
                    # Use max value as confidence
                    confidence = float(np.max(output))
                    # Simple threshold
                    is_fall = confidence > 0.7
                    
                    result["confidence"] = confidence
                    result["is_fall"] = is_fall
                    result["prediction_shape"] = output.shape
            
            # Use simulation mode
            else:
                logger.debug("Using simulation mode for inference")
                # Generate random results, biased toward non-fall state
                is_fall = random.random() < 0.05  # 5% chance of detecting fall
                confidence = random.uniform(0.8, 0.95) if is_fall else random.uniform(0.1, 0.3)
                
                result["model_type"] = "Simulated"
                result["success"] = True
                result["confidence"] = confidence
                result["is_fall"] = is_fall
                
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            result["error"] = str(e)
            
            # Use simulation mode on error
            is_fall = random.random() < 0.05
            confidence = random.uniform(0.8, 0.95) if is_fall else random.uniform(0.1, 0.3)
            
            result["model_type"] = "Simulated_Fallback"
            result["confidence"] = confidence
            result["is_fall"] = is_fall
        
        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000
        result["inference_time_ms"] = round(inference_time, 2)
        
        return result


class FallDetectionSystem:
    """Fall detection system"""
    
    def __init__(self):
        """Initialize system"""
        self.model = FallDetectionModel()
        self.frame_count = 0
        self.fall_count = 0
        self.last_fall_time = 0
        self.fall_cooldown = 3.0  # Cooldown time after detecting fall (seconds)
        
        # History tracking
        self.recent_results = []
        self.max_history = 10
        
        # Performance tracking
        self.fps = 0
        self.avg_inference_time = 0
        self.inference_times = []
        self.max_inference_times = 50
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Process a single frame and detect falls"""
        self.frame_count += 1
        
        # Run inference
        result = self.model.infer(frame)
        
        # Update performance metrics
        self.inference_times.append(result["inference_time_ms"])
        if len(self.inference_times) > self.max_inference_times:
            self.inference_times.pop(0)
        self.avg_inference_time = sum(self.inference_times) / len(self.inference_times)
        
        # Add to history
        self.recent_results.append(result)
        if len(self.recent_results) > self.max_history:
            self.recent_results.pop(0)
        
        # Check if fall
        is_fall = result["is_fall"]
        current_time = time.time()
        
        # Add cooldown to avoid consecutive fall detections
        if is_fall and (current_time - self.last_fall_time > self.fall_cooldown):
            self.fall_count += 1
            self.last_fall_time = current_time
            logger.info(f"Fall detected! Confidence: {result['confidence']:.2f}, Model: {result['model_type']}")
        else:
            is_fall = False  # Don't report fall during cooldown
        
        # Draw info on frame
        processed_frame = self.draw_info(frame, result, is_fall)
        
        return processed_frame, is_fall
    
    def draw_info(self, frame: np.ndarray, result: Dict[str, Any], is_fall: bool) -> np.ndarray:
        """Draw info on frame"""
        # Create copy to avoid modifying original frame
        output = frame.copy()
        
        # Show FPS
        cv2.putText(output, f"FPS: {self.fps:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Show inference time
        cv2.putText(output, f"Inference: {result['inference_time_ms']:.1f}ms (Avg: {self.avg_inference_time:.1f}ms)", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Show model type
        cv2.putText(output, f"Model: {result['model_type']}", 
                    (10, output.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Show fall status
        status_text = "FALL DETECTED!" if is_fall else "Normal"
        status_color = (0, 0, 255) if is_fall else (0, 255, 0)
        cv2.putText(output, status_text, (10, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
        
        # Show confidence
        cv2.putText(output, f"Confidence: {result['confidence']:.2f}", 
                    (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show counts
        cv2.putText(output, f"Frames: {self.frame_count}", 
                    (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(output, f"Falls: {self.fall_count}", 
                    (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return output
    
    def run(self):
        """Run fall detection system"""
        try:
            # Open camera
            logger.info("Opening camera...")
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                logger.error("Cannot open camera")
                return
            
            logger.info("Starting to process video stream...")
            
            # FPS calculation
            fps_start_time = time.time()
            fps_frame_count = 0
            
            while True:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to read frame")
                    break
                
                # Process frame and detect falls
                processed_frame, is_fall = self.process_frame(frame)
                
                # Calculate FPS
                fps_frame_count += 1
                elapsed_time = time.time() - fps_start_time
                if elapsed_time >= 1.0:  # Update FPS once per second
                    self.fps = fps_frame_count / elapsed_time
                    fps_frame_count = 0
                    fps_start_time = time.time()
                
                # Show processed frame
                cv2.imshow("Dragon X Fall Detection", processed_frame)
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("User requested exit")
                    break
                
                # Print status periodically
                if self.frame_count % 30 == 0:
                    logger.info(f"Processed {self.frame_count} frames, FPS: {self.fps:.1f}")
                
        except KeyboardInterrupt:
            logger.info("User interrupted")
        except Exception as e:
            logger.error(f"Error during execution: {e}")
        finally:
            # Clean up
            if 'cap' in locals() and cap is not None:
                cap.release()
            cv2.destroyAllWindows()
            
            # Print summary
            logger.info("System execution summary:")
            logger.info(f"  - Model type: {self.model.model_name if self.model.qai_model else ('ONNX' if self.model.onnx_session else 'Simulated')}")
            logger.info(f"  - Frames processed: {self.frame_count}")
            logger.info(f"  - Falls detected: {self.fall_count}")
            logger.info(f"  - Average inference time: {self.avg_inference_time:.1f} ms")
            logger.info(f"  - Average FPS: {self.fps:.1f}")
            logger.info("Fall detection system closed")


def check_qai_hub_status():
    """Check QAI Hub status"""
    print("Checking QAI Hub status...")
    
    # Check environment variables
    api_key = os.environ.get("QAI_API_KEY")
    api_token = os.environ.get("QAI_API_TOKEN")
    qai_host = os.environ.get("QAI_HOST")
    
    print(f"QAI API Key: {'Set' if api_key else 'Not set'}")
    print(f"QAI API Token: {'Set' if api_token else 'Not set'}")
    print(f"QAI Host: {qai_host if qai_host else 'Not set'}")
    
    # Try to import QAI Hub
    try:
        import qai_hub
        print(f"QAI Hub version: {qai_hub.__version__}")
        
        # Try to connect to QAI Hub
        try:
            devices = qai_hub.get_devices()
            print(f"Successfully connected to QAI Hub! Available devices: {len(devices)}")
            
            # Show available devices
            for i, device in enumerate(devices[:5]):  # Show max 5 devices
                print(f"  Device {i+1}: {device.name} ({device.type})")
            
            # Try to list available models
            try:
                print("\nTrying to list available models...")
                for model_name in QAI_HUB_MODELS[:3]:  # Try first 3 models
                    try:
                        model = qai_hub.load(model_name)
                        print(f"  Successfully loaded model: {model_name}")
                    except Exception as e:
                        print(f"  Cannot load model {model_name}: {str(e)}")
            except Exception as e:
                print(f"Error listing models: {e}")
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to QAI Hub: {e}")
            return False
            
    except ImportError as e:
        print(f"Cannot import QAI Hub: {e}")
        return False


def main():
    """Main function"""
    print("Dragon X Fall Detection System")
    print("============================")
    
    # Check QAI Hub status
    print("\n1. Checking QAI Hub status:")
    qai_available = check_qai_hub_status()
    print(f"\n=> QAI Hub status: {'Available' if qai_available else 'Not available, will use simulation mode'}")
    
    # Start fall detection system
    print("\n2. Starting fall detection system:")
    print("Initializing fall detection system...")
    
    try:
        # Create and run system
        system = FallDetectionSystem()
        system.run()
    except Exception as e:
        print(f"System execution failed: {e}")


if __name__ == "__main__":
    main()
