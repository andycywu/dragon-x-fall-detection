import os
import sys
import re

def fix_original_system_simple():
    """Fix the original dragon_x_fall_detection_system.py to use environment variables with minimal changes"""
    
    # File path
    file_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py"
    backup_path = "C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system_backup2.py"
    
    try:
        # First make a backup of the original file
        print(f"Creating backup of original file to {backup_path}...")
        with open(file_path, "r", encoding="utf-8") as original:
            original_content = original.read()
            
        with open(backup_path, "w", encoding="utf-8") as backup:
            backup.write(original_content)
        
        print("Backup created successfully.")
        
        # Now modify the original file - Just add environment variables at the top
        import_qai_hub_line = "import qai_hub as hub"
        
        env_vars_code = """import qai_hub as hub
import os

# Set QAI Hub environment variables to ensure API access
os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
os.environ["QAI_API_VERSION"] = "v1"

print("QAI Hub environment variables have been set")
"""
        
        # Replace the import line with our new code
        modified_content = original_content.replace(import_qai_hub_line, env_vars_code)
        
        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("Successfully modified dragon_x_fall_detection_system.py with environment variables!")
        return True
        
    except Exception as e:
        print(f"Error modifying file: {str(e)}")
        return False

# Create a runner batch file for the original system
def create_original_runner():
    """Create a batch file to run the original system with environment variables"""
    
    runner_path = "C:\\dragon-x-fall-detection\\run_original_system.bat"
    
    try:
        # Create batch file content
        batch_content = """@echo off
REM Set environment variables for QAI Hub
SET QAI_API_KEY=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
SET QAI_API_TOKEN=pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
SET QAI_HOST=https://api.aihub.qualcomm.com
SET QAI_API_URL=https://api.aihub.qualcomm.com
SET QAI_API_VERSION=v1

echo QAI Hub environment variables have been set.
echo.

REM Run dragon_x_fall_detection_system.py with Python 3.10
echo Running original Dragon X Fall Detection System with Python 3.10...
"C:\\Users\\HCKTest\\AppData\\Local\\Programs\\Python\\Python310\\python.exe" C:\\dragon-x-fall-detection\\dragon_x_fall_detection_system.py

echo.
echo Press any key to exit...
pause > nul
"""
        
        # Write batch file
        with open(runner_path, "w") as f:
            f.write(batch_content)
        
        print(f"Successfully created runner batch file at {runner_path}")
        return True
        
    except Exception as e:
        print(f"Error creating runner batch file: {str(e)}")
        return False

if __name__ == "__main__":
    print("Dragon X Fall Detection System - Simple Original Fixer")
    print("==============================================")
    
    # Fix the original system
    print("Fixing the original dragon_x_fall_detection_system.py...")
    fix_success = fix_original_system_simple()
    
    # Create a runner batch file
    print("Creating runner batch file...")
    runner_success = create_original_runner()
    
    if fix_success and runner_success:
        print("==============================================")
        print("Success! Original system has been fixed and is ready to run.")
        print("You can run it with: run_original_system.bat")
    else:
        print("==============================================")
        print("Some operations failed. Please check the error messages above.")
    
    print("Press any key to exit...")
    input()
