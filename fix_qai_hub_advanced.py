import os
import sys
import re

def patch_qai_hub_system():
    """Patch dragon_x_fall_detection_system.py file to use environment variables and fix encoding issues"""
    
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
        
        # Fix Unicode printing issues
        # Replace Dragon X with emoji
        pattern = r'print\("\\U0001f409 Dragon X.*?"\)'
        replacement = 'print("Dragon X Fall Detection System")'
        modified_content = re.sub(pattern, replacement, modified_content)
        
        # Replace other Unicode print statements
        pattern = r'print\(f?"[^"]*?\\u[0-9a-fA-F]{4}[^"]*?"\)'
        for match in re.finditer(pattern, modified_content):
            modified_content = modified_content.replace(match.group(0), 'print("Processing...")')
        
        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("Successfully patched dragon_x_fall_detection_system.py file to use environment variables and fix encoding issues.")
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
                    
                    # Apply same modifications
                    modified_content = content.replace(import_line, new_code)
                    
                    # Fix Unicode printing issues
                    pattern = r'print\("\\U0001f409 Dragon X.*?"\)'
                    replacement = 'print("Dragon X Fall Detection System")'
                    modified_content = re.sub(pattern, replacement, modified_content)
                    
                    # Replace other Unicode print statements
                    pattern = r'print\(f?"[^"]*?\\u[0-9a-fA-F]{4}[^"]*?"\)'
                    for match in re.finditer(pattern, modified_content):
                        modified_content = modified_content.replace(match.group(0), 'print("Processing...")')
                    
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

def create_safe_copy():
    """Create a safe copy of the fall detection system with all Unicode removed"""
    src_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py"
    dst_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_english.py"
    
    try:
        # Read source file
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add environment variables
        env_vars = """import os

# Set QAI Hub environment variables
os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_VERSION"] = "v1"

print("QAI Hub environment variables have been set")

"""
        
        # Add at the beginning after the first import
        import_pattern = r'import [^\n]+'
        match = re.search(import_pattern, content)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + "\n" + env_vars + content[insert_pos:]
        
        # Replace all Unicode characters
        # Replace emojis and other Unicode
        content = re.sub(r'\\U[0-9a-fA-F]{8}', '', content)
        content = re.sub(r'\\u[0-9a-fA-F]{4}', '', content)
        
        # Replace print statements containing Unicode
        content = re.sub(r'print\(f?"[^"]*?(\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8})[^"]*?"\)', 'print("Processing...")', content)
        
        # Write to destination file
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Successfully created safe English version at {dst_path}")
        return True
    except Exception as e:
        print(f"Failed to create safe copy: {str(e)}")
        return False

if __name__ == "__main__":
    # First try to patch the original file
    patch_success = patch_qai_hub_system()
    
    # Also create a safe English version
    copy_success = create_safe_copy()
    
    if patch_success:
        print("Patching successful! Now you can run the original Dragon X system using real QAI Hub.")
    else:
        print("Patching original file failed.")
    
    if copy_success:
        print("Created a safe English version of the file without Unicode characters.")
        print("You can run it with: python dragon_x_fall_detection_english.py")
    
    print("Press any key to exit...")
    input()
