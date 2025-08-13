import os
import sys

def patch_dragon_system():
    # File path
    system_file = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py"
    
    try:
        # Read the original file with UTF-8 encoding
        with open(system_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Define the mock QAI Hub class
        mock_code = """
# Mock QAI Hub implementation
import numpy as np

class MockDevice:
    def __init__(self, name="Mock Device", os="Mock OS"):
        self.name = name
        self.os = os
        self.id = "mock-device-001"
        self.attributes = ["chipset:mock-chipset"]
        
    def __str__(self):
        return f"Device({self.name}, {self.os})"

class MockHub:
    def get_devices(self, name="", os="", attributes=[]):
        return [
            MockDevice("Snapdragon X Elite", "Windows 11"),
            MockDevice("Snapdragon 8 Gen 3", "Android 14")
        ]

try:
    import qai_hub as real_hub
    hub = real_hub
    print("Using real QAI Hub")
except Exception:
    hub = MockHub()
    print("Using mock QAI Hub")

"""
        
        # Replace the import statement
        modified_content = content.replace(
            "import qai_hub as hub", 
            mock_code
        )
        
        # Write the modified content back with UTF-8 encoding
        with open(system_file, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("Successfully patched dragon_x_fall_detection_system.py to handle QAI Hub issues")
    except UnicodeDecodeError:
        print("Encountered encoding issue. Trying with different encodings...")
        
        # Try with different encodings
        encodings = ["latin1", "cp1252", "iso-8859-1"]
        success = False
        
        for encoding in encodings:
            try:
                with open(system_file, "r", encoding=encoding) as f:
                    content = f.read()
                
                # Replace the import statement
                modified_content = content.replace(
                    "import qai_hub as hub", 
                    mock_code
                )
                
                # Write the modified content back with UTF-8 encoding
                with open(system_file, "w", encoding="utf-8") as f:
                    f.write(modified_content)
                
                print(f"Successfully patched using {encoding} encoding")
                success = True
                break
            except Exception as e:
                print(f"Failed with {encoding} encoding: {str(e)}")
        
        if not success:
            print("Failed to patch the file with all attempted encodings")

if __name__ == "__main__":
    patch_dragon_system()
    print("Press Enter to exit...")
    input()
