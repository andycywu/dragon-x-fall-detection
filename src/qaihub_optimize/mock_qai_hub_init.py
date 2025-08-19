"""
模擬 QAI Hub 模組 - 為黑客松展示準備
這個模組提供了與 qai_hub 相同的 API 接口，但使用模擬數據
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class Device:
    """模擬 QAI Hub 設備"""
    
    def __init__(self, name: str, device_id: str, status: str = "online"):
        self.name = name
        self.id = device_id
        self.status = status
    
    def __repr__(self):
        return f"Device(name='{self.name}', id='{self.id}', status='{self.status}')"

class CompileJob:
    """模擬 QAI Hub 編譯作業"""
    
    def __init__(self, job_id: str, model_name: str, device: Device):
        self.job_id = job_id
        self.model_name = model_name
        self.device = device
        self.status = "queued"
        self.created_at = time.time()
    
    def wait(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """等待編譯作業完成"""
        # 模擬等待過程
        time.sleep(min(0.5, timeout or 0.5))
        self.status = "completed"
        return {"status": self.status, "job_id": self.job_id}
    
    def __repr__(self):
        return f"CompileJob(job_id='{self.job_id}', status='{self.status}')"

# 預定義的模擬設備
_MOCK_DEVICES = [
    Device("Snapdragon X Elite Dev Kit", "sdx-elite-001", "online"),
    Device("Snapdragon 8 Gen 3", "sd8g3-002", "online"),
    Device("Cloud AI 100", "cai100-003", "online")
]

def get_devices() -> List[Device]:
    """獲取可用的 QAI Hub 設備列表"""
    return _MOCK_DEVICES

def upload_model(model: Any) -> str:
    """將模型上傳到 QAI Hub"""
    # 生成唯一的模型 ID
    model_id = f"model-{int(time.time())}"
    logger.info(f"模擬上傳模型: {model_id}")
    return model_id

def submit_compile_job(
    model: Union[str, Any],
    input_specs: Dict[str, Tuple[Tuple[int, ...], str]],
    device: Device,
    **kwargs
) -> CompileJob:
    """提交模型編譯作業"""
    # 生成唯一的作業 ID
    job_id = f"job-{int(time.time())}"
    model_name = model if isinstance(model, str) else "uploaded_model"
    logger.info(f"模擬提交編譯作業: {job_id} 到設備 {device.name}")
    return CompileJob(job_id, model_name, device)

# 模擬 QAI Hub Models 模組
class MockModels:
    """模擬 QAI Hub Models 命名空間"""
    
    class models:
        """模擬模型命名空間"""
        
        class mediapipe_pose:
            """模擬 MediaPipe Pose 模型"""
            
            class Model:
                """MediaPipe Pose 模型類"""
                
                @classmethod
                def from_pretrained(cls, *args, **kwargs):
                    """從預訓練模型載入"""
                    instance = cls()
                    instance.pose_detector = MockPoseDetector()
                    return instance
        
        class mediapipe_face:
            """模擬 MediaPipe Face 模型"""
            
            class Model:
                """MediaPipe Face 模型類"""
                
                @classmethod
                def from_pretrained(cls, *args, **kwargs):
                    """從預訓練模型載入"""
                    instance = cls()
                    instance.face_detector = MockFaceDetector()
                    return instance
        
        class mediapipe_hand:
            """模擬 MediaPipe Hand 模型"""
            
            class Model:
                """MediaPipe Hand 模型類"""
                
                @classmethod
                def from_pretrained(cls, *args, **kwargs):
                    """從預訓練模型載入"""
                    instance = cls()
                    instance.hand_detector = MockHandDetector()
                    return instance

class MockDetector:
    """模擬檢測器基類"""
    
    def convert_to_torchscript(self):
        """轉換為 TorchScript 格式"""
        return "mock_torchscript_model"
    
    def __call__(self, image: np.ndarray) -> Dict[str, Any]:
        """執行推論"""
        return {"mock_results": True}

class MockPoseDetector(MockDetector):
    """模擬姿態檢測器"""
    
    def __call__(self, image: np.ndarray) -> Dict[str, Any]:
        """執行姿態檢測"""
        # 生成模擬的姿態關鍵點
        keypoints = []
        for i in range(17):  # 17 個關鍵點
            keypoints.append({
                "x": np.random.uniform(0.2, 0.8),
                "y": np.random.uniform(0.2, 0.8),
                "confidence": np.random.uniform(0.7, 1.0)
            })
        
        return {
            "keypoints": [{
                "keypoints": keypoints,
                "confidence": np.random.uniform(0.8, 1.0)
            }]
        }

class MockFaceDetector(MockDetector):
    """模擬人臉檢測器"""
    
    def __call__(self, image: np.ndarray) -> Dict[str, Any]:
        """執行人臉檢測"""
        # 生成模擬的人臉檢測結果
        faces = []
        num_faces = np.random.randint(0, 3)
        
        for i in range(num_faces):
            faces.append({
                "bbox": [
                    np.random.uniform(0.2, 0.4),  # x1
                    np.random.uniform(0.2, 0.4),  # y1
                    np.random.uniform(0.6, 0.8),  # x2
                    np.random.uniform(0.6, 0.8)   # y2
                ],
                "confidence": np.random.uniform(0.8, 1.0)
            })
        
        return {"faces": faces}

class MockHandDetector(MockDetector):
    """模擬手部檢測器"""
    
    def __call__(self, image: np.ndarray) -> Dict[str, Any]:
        """執行手部檢測"""
        # 生成模擬的手部檢測結果
        hands = []
        num_hands = np.random.randint(0, 3)
        
        for i in range(num_hands):
            landmarks = []
            for j in range(21):  # 21 個手部關鍵點
                landmarks.append({
                    "x": np.random.uniform(0.2, 0.8),
                    "y": np.random.uniform(0.2, 0.8),
                    "z": np.random.uniform(-0.1, 0.1)
                })
            
            hands.append({
                "landmarks": landmarks,
                "handedness": "Left" if np.random.random() > 0.5 else "Right",
                "confidence": np.random.uniform(0.8, 1.0)
            })
        
        return {"hands": hands}
