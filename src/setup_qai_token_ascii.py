#!/usr/bin/env python3
"""
QAI Hub API Token Setup Tool
Setup QAI Hub API token for Windows and Linux environments
"""

import os
import sys
from pathlib import Path

def setup_qai_hub_token():
    """Setup QAI Hub API token"""
    print("Setting up QAI Hub API token...")
    
    # API token
    api_token = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
    
    # Create .qai_hub directory
    home_dir = Path.home()
    qai_config_dir = home_dir / ".qai_hub"
    qai_config_dir.mkdir(exist_ok=True)
    print(f"Created config directory: {qai_config_dir}")
    
    # Create config file
    config_file = qai_config_dir / "client.ini"
    config_content = f"""[default]
api_token = {api_token}
api_url = https://app.aihub.qualcomm.com
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"Config file created: {config_file}")
    
    # Set environment variable
    os.environ['QAI_HUB_API_TOKEN'] = api_token
    print("Environment variable set")
    
    # Verify setup
    if config_file.exists():
        print("Verification successful: API token is set")
    else:
        print("Verification failed: Config file creation failed")
    
    return True

def main():
    """Main function"""
    print("=" * 50)
    print("QAI Hub API Token Setup Tool")
    print("=" * 50)
    
    # Detect operating system
    import platform
    system_name = platform.system()
    print(f"Detected operating system: {system_name}")
    
    # Setup API token
    success = setup_qai_hub_token()
    
    # Show results
    print("\n" + "=" * 50)
    if success:
        print("QAI Hub API token setup successful!")
    else:
        print("QAI Hub API token setup failed!")
    print("=" * 50)
    
    print("\nNext steps:")
    print("1. Run unified_ai_detector.py to test QAI Hub integration")
    print("2. Run fixed_final_demo.py to test fall detection")
    print("3. See windows_guide.md for more instructions")

if __name__ == "__main__":
    main()
