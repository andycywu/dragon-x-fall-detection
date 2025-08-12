#!/usr/bin/env python3
"""
Fix QAI Hub Configuration for Windows
"""

import os
import sys
from pathlib import Path

def fix_qai_hub_config():
    """Fix QAI Hub configuration for Windows"""
    print("Fixing QAI Hub configuration...")
    
    # API token
    api_token = "h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2"
    
    # Create .qai_hub directory
    home_dir = Path.home()
    qai_config_dir = home_dir / ".qai_hub"
    qai_config_dir.mkdir(exist_ok=True)
    print(f"Config directory: {qai_config_dir}")
    
    # Create config file with proper format
    config_file = qai_config_dir / "client.ini"
    config_content = """[default]
api_token = h0eubh7un3kk64u6oxisg9rbt8bbgubs913bzls2
organization = 
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
profile = default
device_group = default
model_path = models
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"Updated config file: {config_file}")
    
    # Set environment variable (this is for the current session only)
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    print("Environment variable set")
    
    return True

def main():
    """Main function"""
    print("=" * 50)
    print("QAI Hub Configuration Fix for Windows")
    print("=" * 50)
    
    # Fix configuration
    success = fix_qai_hub_config()
    
    # Show result
    print("\n" + "=" * 50)
    if success:
        print("QAI Hub configuration fixed!")
        print("Now you should be able to run the fall detection demo")
        print("with QAI Hub integration.")
    else:
        print("Failed to fix QAI Hub configuration!")
    print("=" * 50)

if __name__ == "__main__":
    main()
