import os
import sys

def patch_qai_hub_system():
    """Patch dragon_x_fall_detection_system.py file to use environment variables"""
    
    # File path
    file_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py"
    
    try:
        # Read original file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find import qai_hub as hub line
        import_line = "import qai_hub as hub"
        
        # Create new code snippet to use environment variables
        new_code = """import qai_hub as hub
import os

# Set QAI Hub environment variables
os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_VERSION"] = "v1"

# Output environment variable status
print("QAI Hub environment variables have been set")
"""
        
        # Replace code
        modified_content = content.replace(import_line, new_code)
        
        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("Successfully patched dragon_x_fall_detection_system.py file to use environment variables.")
        return True
        
    except Exception as e:
        print(f"Patching failed: {str(e)}")
        
        # Try different encodings
        try:
            encodings = ["latin1", "cp1252", "iso-8859-1"]
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    
                    # Replace code
                    modified_content = content.replace(import_line, new_code)
                    
                    # Write back to file
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(modified_content)
                    
                    print(f"Successfully patched file using {encoding} encoding.")
                    return True
                except Exception as inner_e:
                    print(f"{encoding} encoding attempt failed: {str(inner_e)}")
        except Exception as outer_e:
            print(f"All encoding attempts failed: {str(outer_e)}")
        
        return False

if __name__ == "__main__":
    success = patch_qai_hub_system()
    
    if success:
        print("Patching successful! Now you can run the original Dragon X system using real QAI Hub.")
    else:
        print("Patching failed. Please try other methods.")
    
    print("Press any key to exit...")
    input()
