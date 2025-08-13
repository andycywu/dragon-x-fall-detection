#!/usr/bin/env python3
"""
Dragon X Fall Detection System
Using real QAI Hub for inference (complete ASCII version)
"""

import os
import sys
import argparse
import cv2
import numpy as np
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple
import random
import subprocess
try:
    from importlib import metadata as importlib_metadata  # Python 3.8+
except Exception:  # pragma: no cover
    import importlib_metadata  # type: ignore

# Configure logging to use ASCII only
class AsciiFormatter(logging.Formatter):
    def format(self, record):
        # Get the original message
        msg = super().format(record)
        # Replace any non-ASCII characters with '?'
        return msg.encode('ascii', 'replace').decode('ascii')

# Configure ASCII-only logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(AsciiFormatter('%(levelname)s:%(name)s:%(message)s'))
logger.handlers = [handler]

# Do not force override of user's QAI Hub config; rely on ~/.qai_hub/client.ini when present.
# If user provides QAI_HUB_API_TOKEN / QAI_HUB_API_URL via environment, SDK will also respect it.

# Try to import QAI Hub modules
try:
    import qai_hub as hub
    USING_REAL_QAI_HUB = True
    print("Successfully imported QAI Hub")
except ImportError as e:
    print(f"Cannot import QAI Hub: {str(e).encode('ascii', 'replace').decode('ascii')}")
    USING_REAL_QAI_HUB = False
    print("Will use simulation mode")

try:
    import onnxruntime as ort
    USING_ONNX = True
    print("Successfully imported ONNX Runtime")
except ImportError:
    USING_ONNX = False
    print("ONNX Runtime not available")

# QAI Hub models list - ordered by priority
QAI_HUB_MODELS = [
    "qai-hub/mobilenetv3-small-minimalistic",
    "qai-hub/efficientnet-lite4",
    "qai-hub/mobilenet-v2-1.0",
    "qai-hub/squeezenet1-1",
    "qai-hub/pose-estimation-hrnet"
]

def get_qai_hub_model_loader():
    """Return a callable to load models from QAI Hub SDK across versions, or None."""
    # Try top-level hub.load
    try:
        if hasattr(hub, 'load') and callable(getattr(hub, 'load')):
            return hub.load
    except Exception:
        pass
    # Try qai_hub.models.load
    try:
        import qai_hub.models as hub_models  # type: ignore
        if hasattr(hub_models, 'load') and callable(getattr(hub_models, 'load')):
            return hub_models.load
    except Exception:
        pass
    # Try external package (if present)
    try:
        import qai_hub_models as qhm  # type: ignore
        if hasattr(qhm, 'load') and callable(getattr(qhm, 'load')):
            return qhm.load
    except Exception:
        pass
    return None

class FallDetectionModel:
    """Fall detection model using QAI Hub or simulation"""
    
    def __init__(self, onnx_model_path: Optional[str] = None):
        """Initialize model"""
        self.qai_model = None
        self.onnx_session = None
        self.model_name = None
        self.input_shape = (224, 224)  # Default input size
        self.onnx_model_path = onnx_model_path
        
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
            loader = get_qai_hub_model_loader()
            if loader is None:
                logger.warning("QAI Hub SDK does not expose a 'load' API in this version; skipping cloud model load")
            else:
                for model_name in QAI_HUB_MODELS:
                    try:
                        logger.info(f"Trying to load model: {model_name}")
                        self.qai_model = loader(model_name)
                        self.model_name = model_name
                        logger.info(f"Successfully loaded model: {model_name}")
                        break
                    except Exception as e:
                        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                        logger.warning(f"Cannot load model {model_name}: {error_msg}")
            
            if self.qai_model is None:
                logger.warning("Could not load any QAI Hub model, will use ONNX mode")
                self._init_onnx_fallback()
        
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            logger.error(f"QAI Hub initialization failed: {error_msg}")
            logger.info("Switching to ONNX mode")
            self._init_onnx_fallback()
    
    def _init_onnx_fallback(self):
        """Initialize ONNX Runtime as fallback"""
        if not USING_ONNX:
            logger.warning("ONNX Runtime not available, will use simulation mode")
            return
            
        try:
            logger.info("Initializing ONNX Runtime...")
            
            # Check if there are available ONNX model files
            onnx_path = None
            if self.onnx_model_path and os.path.exists(self.onnx_model_path):
                onnx_path = self.onnx_model_path
            else:
                onnx_models = [f for f in os.listdir('.') if f.endswith('.onnx')]
                if onnx_models:
                    onnx_path = onnx_models[0]
            
            if onnx_path:
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
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            logger.error(f"ONNX initialization failed: {error_msg}")
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
                    error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                    logger.error(f"Error processing QAI Hub predictions: {error_msg}")
                    
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
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            logger.error(f"Inference failed: {error_msg}")
            result["error"] = error_msg
            
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
    
    def __init__(self, camera_index: int = 0, onnx_model_path: Optional[str] = None, video_path: Optional[str] = None, export_log: bool = True):
        """Initialize system"""
        self.model = FallDetectionModel(onnx_model_path=onnx_model_path)
        self.camera_index = camera_index
        self.video_path = video_path
        self.export_log = export_log
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
            # Open source: video file preferred if provided, else camera with fallbacks
            if self.video_path and os.path.exists(self.video_path):
                logger.info(f"Opening video file: {self.video_path}")
                cap = cv2.VideoCapture(self.video_path)
            else:
                logger.info(f"Opening camera index {self.camera_index}...")
                cap = cv2.VideoCapture(self.camera_index)
                if not cap.isOpened():
                    # Try DirectShow on Windows to avoid MSMF issues
                    if hasattr(cv2, 'CAP_DSHOW'):
                        logger.info("Primary open failed; retrying with DirectShow backend (CAP_DSHOW)")
                        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
                if not cap.isOpened() and self.camera_index != 0:
                    logger.info("Camera index not available; falling back to index 0")
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened() and hasattr(cv2, 'CAP_DSHOW'):
                        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not cap.isOpened():
                logger.warning("Cannot open camera; using synthetic frames for a short demo run")
                for i in range(120):  # ~4 seconds at 30 FPS
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    x = (i * 5) % 600
                    cv2.rectangle(frame, (x, 200), (x+30, 260), (0, 255, 0), -1)
                    processed_frame, is_fall = self.process_frame(frame)
                    if i % 30 == 0:
                        logger.info(f"Synthetic frames processed: {i}")
                return
            
            logger.info("Starting to process video stream...")
            
            # FPS calculation
            fps_start_time = time.time()
            fps_frame_count = 0
            
            while True:
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to read frame; switching to synthetic frames for a short demo run")
                    for i in range(120):
                        frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        x = (i * 5) % 600
                        cv2.rectangle(frame, (x, 200), (x+30, 260), (0, 255, 0), -1)
                        processed_frame, is_fall = self.process_frame(frame)
                        if i % 30 == 0:
                            logger.info(f"Synthetic frames processed: {i}")
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
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            logger.error(f"Error during execution: {error_msg}")
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
            
            # Export session log
            if self.export_log:
                try:
                    out_dir = os.path.join(os.getcwd(), "logs")
                    os.makedirs(out_dir, exist_ok=True)
                    ts = int(time.time())
                    out_path = os.path.join(out_dir, f"session_{ts}.json")
                    summary = {
                        "timestamp": ts,
                        "camera_index": self.camera_index,
                        "video_path": self.video_path,
                        "model_type": (self.model.model_name if self.model.qai_model else ("ONNX" if self.model.onnx_session else "Simulated")),
                        "frames": self.frame_count,
                        "falls": self.fall_count,
                        "avg_inference_ms": round(self.avg_inference_time, 2),
                        "avg_fps": round(self.fps, 2),
                    }
                    with open(out_path, 'w') as f:
                        json.dump(summary, f)
                    logger.info(f"Session log exported: {out_path}")
                except Exception as e:
                    logger.warning(f"Failed to export session log: {safe_str(e)}")


def safe_str(obj):
    """Convert any string to ASCII-safe string"""
    if obj is None:
        return "None"
    try:
        return str(obj).encode('ascii', 'replace').decode('ascii')
    except:
        return "<<non-ASCII text>>"


def check_qai_hub_status():
    """Check QAI Hub status"""
    print("Checking QAI Hub status...")
    
    # Check environment variables
    legacy_key = os.environ.get("QAI_API_KEY")
    legacy_token = os.environ.get("QAI_API_TOKEN")
    legacy_host = os.environ.get("QAI_HOST")
    hub_token = os.environ.get("QAI_HUB_API_TOKEN")
    hub_url = os.environ.get("QAI_HUB_API_URL")
    
    print(f"Env QAI_HUB_API_TOKEN: {'Set' if hub_token else 'Not set'}")
    print(f"Env QAI_HUB_API_URL: {hub_url if hub_url else 'Not set'}")
    print(f"Env (legacy) QAI_API_TOKEN: {'Set' if legacy_token else 'Not set'}")
    print(f"Env (legacy) QAI_API_KEY: {'Set' if legacy_key else 'Not set'}")
    print(f"Env (legacy) QAI_HOST: {legacy_host if legacy_host else 'Not set'}")
    
    # Try to import QAI Hub
    try:
        import qai_hub
        print(f"QAI Hub version: {safe_str(qai_hub.__version__)}")
        
        # Try to connect to QAI Hub
        try:
            devices = qai_hub.get_devices()
            print(f"Successfully connected to QAI Hub! Available devices: {len(devices)}")
            
            # Show sample devices safely
            for i, device in enumerate(devices[:5]):  # Show max 5 devices
                name = getattr(device, 'name', None)
                dtype = getattr(device, 'type', None) or getattr(device, 'device_type', None)
                print(f"  Device {i+1}: {safe_str(name) if name else safe_str(device)}{(' - ' + safe_str(dtype)) if dtype else ''}")
            
            # Try to load models if API exists
            loader = None
            try:
                loader = get_qai_hub_model_loader()
            except Exception:
                loader = None
            if loader:
                try:
                    print("\nTrying to load a sample model...")
                    for model_name in QAI_HUB_MODELS[:3]:  # Try first 3 models
                        try:
                            _ = loader(model_name)
                            print(f"  Successfully loaded model: {model_name}")
                            break
                        except Exception as e:
                            print(f"  Cannot load model {model_name}: {safe_str(e)}")
                except Exception as e:
                    print(f"Error loading models: {safe_str(e)}")
            else:
                print("Model load API not available in this SDK version; skipping model load test")
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to QAI Hub: {safe_str(e)}")
            return False
            
    except ImportError as e:
        print(f"Cannot import QAI Hub: {safe_str(e)}")
        return False


def get_installed_version(pkg: str) -> Optional[str]:
    """Return installed package version using importlib.metadata."""
    try:
        return importlib_metadata.version(pkg)
    except Exception:
        return None


def upgrade_qai_hub_sdk(packages: Optional[List[str]] = None) -> bool:
    """Upgrade QAI Hub SDK packages using this interpreter's pip.
    Returns True on success.
    """
    if packages is None:
        # Prefer eager to ensure deps updated properly
        packages = [
            "qai-hub",
            "qai-hub-models",
        ]
    print("\nUpgrading QAI Hub SDK via this Python interpreter:")
    print(f"  Python: {safe_str(sys.executable)}")
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-U", "--upgrade-strategy", "eager"] + packages
        print("Running:", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.stdout:
            print(proc.stdout)
        if proc.returncode != 0:
            if proc.stderr:
                print(proc.stderr)
            print(f"Upgrade failed with exit code {proc.returncode}")
            return False
        # Show installed versions
        print("Installed versions after upgrade:")
        for pkg in packages:
            ver = get_installed_version(pkg) or "Unknown"
            print(f"  - {pkg}: {safe_str(ver)}")
        return True
    except Exception as e:
        print(f"Upgrade error: {safe_str(e)}")
        return False


def normalize_qai_env_from_client_ini():
    """Read ~/.qai_hub/client.ini if present and set QAI_HUB_* envs when missing.
    Supports old format with [auth]/[api] url/version.
    """
    try:
        cfg_path = os.path.expanduser("~/.qai_hub/client.ini")
        if not os.path.exists(cfg_path):
            return
        with open(cfg_path, 'r') as f:
            content = f.read()

        # If already new format, do nothing
        if '[api]' in content and 'api_token' in content and 'api_url' in content:
            return

        token = None
        url = None
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            low = line.lower()
            if (low.startswith('api_token') or low.startswith('api_key')) and '=' in line and not token:
                token = line.split('=', 1)[1].strip()
            if low.startswith('url') and '=' in line and not url:
                url = line.split('=', 1)[1].strip()

        # Map old api host to new app host if needed
        if url and 'api.aihub.qualcomm.com' in url:
            mapped_url = 'https://app.aihub.qualcomm.com'
        else:
            mapped_url = url or os.environ.get('QAI_HUB_API_URL') or 'https://app.aihub.qualcomm.com'

        if token and not os.environ.get('QAI_HUB_API_TOKEN'):
            os.environ['QAI_HUB_API_TOKEN'] = token
        if mapped_url and not os.environ.get('QAI_HUB_API_URL'):
            os.environ['QAI_HUB_API_URL'] = mapped_url
    except Exception as e:
        print(f"Warning: could not normalize env from client.ini: {safe_str(e)}")

def create_or_migrate_client_ini():
    """Ensure ~/.qai_hub/client.ini exists in the correct format.
    - If missing and QAI_HUB_API_TOKEN is set, create with the new [api] fields.
    - If exists but in old format ([auth]/url/version), back up and migrate to new format.
    """
    try:
        qai_dir = os.path.expanduser("~/.qai_hub")
        os.makedirs(qai_dir, exist_ok=True)
        client_ini_path = os.path.join(qai_dir, "client.ini")

        def write_new(token: str, api_url: str):
            content = (
                "[api]\n"
                f"api_token = {token}\n"
                f"api_url = {api_url}\n"
                f"web_url = {api_url}\n"
                "verbose = True\n"
            )
            with open(client_ini_path, 'w') as f:
                f.write(content)

        api_url_env = os.environ.get("QAI_HUB_API_URL", "https://app.aihub.qualcomm.com")

        if not os.path.exists(client_ini_path):
            token = os.environ.get("QAI_HUB_API_TOKEN") or os.environ.get("QAI_API_TOKEN") or os.environ.get("QAI_API_KEY")
            if not token:
                print("client.ini missing and no QAI_HUB_API_TOKEN found; skip creating")
                return False
            write_new(token, api_url_env)
            print(f"Created client.ini at {client_ini_path} (new format)")
            return True

        # Exists: check format
        with open(client_ini_path, 'r') as f:
            content = f.read()

        has_new = ('[api]' in content) and ('api_token' in content) and ('api_url' in content)
        if has_new:
            print(f"client.ini OK (new format) at {client_ini_path}")
            return True

        # Try to extract token from old format
        token = None
        for line in content.splitlines():
            line = line.strip()
            if line.lower().startswith('api_token') and '=' in line:
                token = line.split('=', 1)[1].strip()
                break
            if line.lower().startswith('api_key') and '=' in line and not token:
                token = line.split('=', 1)[1].strip()

        if not token:
            token = os.environ.get("QAI_HUB_API_TOKEN") or os.environ.get("QAI_API_TOKEN") or os.environ.get("QAI_API_KEY")

        if not token:
            print("client.ini exists but format is old and no token found; cannot migrate automatically")
            print("Please set QAI_HUB_API_TOKEN or re-save config via AI Hub CLI Account page.")
            return False

        # Backup and migrate
        backup_path = client_ini_path + ".bak"
        try:
            with open(backup_path, 'w') as bf:
                bf.write(content)
            write_new(token, api_url_env)
            print(f"Migrated client.ini to new format (backup at {backup_path})")
            return True
        except Exception as e:
            print(f"Failed to migrate client.ini: {safe_str(e)}")
            return False
    except Exception as e:
        print(f"Error ensuring client.ini: {safe_str(e)}")
        return False


def main():
    """Main function"""
    print("Dragon X Fall Detection System")
    print("============================")
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Dragon X Fall Detection")
    parser.add_argument("--camera-index", type=int, default=0, help="Camera index to use (default: 0)")
    parser.add_argument("--onnx-model", type=str, default=None, help="Path to ONNX model for local inference")
    parser.add_argument("--video", type=str, default=None, help="Path to a video file instead of camera")
    parser.add_argument("--no-export-log", action="store_true", help="Disable exporting session summary JSON")
    parser.add_argument("--upgrade-sdk", action="store_true", help="Upgrade QAI Hub SDK (qai-hub, qai-hub-models) using this Python and exit")
    args = parser.parse_args()
    
    # Optional: upgrade SDK and exit (avoid mixing old imports in a running process)
    if args.upgrade_sdk:
        ok = upgrade_qai_hub_sdk()
        print("\n=> SDK upgrade:", "Success" if ok else "Failed")
        print("Please re-run the program to use the upgraded SDK.")
        return 0

    # Normalize env from any existing client.ini (old format) then ensure config
    print("\n1. Setting up QAI Hub configuration (non-destructive):")
    normalize_qai_env_from_client_ini()
    client_ini_created = create_or_migrate_client_ini()
    print(f"=> QAI Hub client.ini setup: {'Ready' if client_ini_created else 'Skipped'}")
    
    # Check QAI Hub status
    print("\n2. Checking QAI Hub status:")
    qai_available = check_qai_hub_status()
    print(f"\n=> QAI Hub status: {'Available' if qai_available else 'Not available, will use simulation mode'}")
    
    # Start fall detection system
    print("\n3. Starting fall detection system:")
    print("Initializing fall detection system...")
    
    try:
        # Create and run system
        system = FallDetectionSystem(
            camera_index=args.camera_index,
            onnx_model_path=args.onnx_model,
            video_path=args.video,
            export_log=(not args.no_export_log),
        )
        system.run()
    except Exception as e:
        error_msg = safe_str(e)
        print(f"System execution failed: {error_msg}")


if __name__ == "__main__":
    main()
