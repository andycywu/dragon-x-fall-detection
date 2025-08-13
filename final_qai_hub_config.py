import os
import sys
import configparser
from pathlib import Path

def create_config():
    print("Creating QAI Hub configuration")
    
    # Get user home directory
    home_dir = os.path.expanduser("~")
    
    # Create .qai_hub directory if it doesn't exist
    qai_hub_dir = os.path.join(home_dir, ".qai_hub")
    os.makedirs(qai_hub_dir, exist_ok=True)
    
    # Create client.ini file
    config_file = os.path.join(qai_hub_dir, "client.ini")
    
    # Configuration content
    content = """[default]
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
base_api_url = https://api.aihub.qualcomm.com
web_url = https://app.aihub.qualcomm.com
api_url = https://api.aihub.qualcomm.com
api_version = v1
"""
    
    # Write to file
    with open(config_file, 'w') as f:
        f.write(content)
    
    print(f"Created configuration file: {config_file}")
    
    # Set environment variables
    os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
    os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
    os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
    os.environ["QAI_API_VERSION"] = "v1"
    
    print("Set environment variables")
    
    # Test configuration
    print("\nTesting QAI Hub configuration")
    try:
        import qai_hub as hub
        print("Successfully imported QAI Hub")
        
        try:
            devices = hub.get_devices()
            print(f"Success! Found {len(devices)} devices")
            for i, device in enumerate(devices[:3]):
                print(f"Device {i+1}: {device.name}")
            return True
        except Exception as e:
            print(f"Error getting devices: {str(e)}")
            return False
    except ImportError as e:
        print(f"Failed to import QAI Hub: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_config()
    if success:
        print("\nQAI Hub configuration was successful!")
    else:
        print("\nQAI Hub configuration encountered issues.")
    
    print("\nPress Enter to exit...")
    input()
