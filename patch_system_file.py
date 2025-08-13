import os
import sys

def modify_system_file():
    # 文件路徑
    file_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py"
    mock_path = "C:\\dragon-x-fall-detection\\mock_qai_hub.py"
    
    # 讀取原始文件
    with open(file_path, "r") as f:
        content = f.read()
    
    # 修改 import qai_hub as hub 行
    modified_content = content.replace(
        "import qai_hub as hub", 
        """try:
    import qai_hub as hub
except ImportError:
    print("Using mock QAI Hub module")
    import mock_qai_hub as hub"""
    )
    
    # 寫入修改後的文件
    with open(file_path, "w") as f:
        f.write(modified_content)
    
    print("Successfully modified dragon_x_fall_detection_system.py to use mock QAI Hub module if needed")

if __name__ == "__main__":
    modify_system_file()
