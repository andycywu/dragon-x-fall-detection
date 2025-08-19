"""
QAI Hub Mock Module - For Dragon X Fall Detection System
"""

import numpy as np

class Device:
    def __init__(self, name="Mock Device", os="Mock OS"):
        self.name = name
        self.os = os
        self.id = "mock-device-001"
        self.attributes = ["chipset:mock-chipset"]
        
    def __str__(self):
        return f"Device({self.name}, {self.os})"
        
class CompileJob:
    def __init__(self, job_id="mock-job-001"):
        self.job_id = job_id
        
    def get_target_model(self):
        return None

def get_devices(name="", os="", attributes=[]):
    return [
        Device("Snapdragon X Elite", "Windows 11"),
        Device("Snapdragon 8 Gen 3", "Android 14")
    ]

def upload_model(model, name=None):
    print(f"[Mock] Uploading model: {name if name else 'unnamed'}")
    return model
