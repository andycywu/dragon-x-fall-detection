import os
import sys
import configparser
from pathlib import Path

def create_config():
    # Get user home directory
    home_dir = os.path.expanduser("~")
    
    # Create .qai_hub directory if it doesn't exist
    qai_hub_dir = os.path.join(home_dir, ".qai_hub")
    os.makedirs(qai_hub_dir, exist_ok=True)
    
    # Create client.ini file
    config_file = os.path.join(qai_hub_dir, "client.ini")
    
    # API key
    api_key = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
    
    # Create the config
    config = configparser.ConfigParser()
    config['default'] = {
        'api_key': api_key,
        'host': 'https://api.aihub.qualcomm.com',
        'api_version': 'v1',
        'api_url': 'https://app.aihub.qualcomm.com',
        'api_token': api_key,
        'user_info': ''
    }
    
    # Write the config to file
    with open(config_file, 'w') as f:
        config.write(f)
    
    print(f"Created QAI Hub config file at: {config_file}")
    print("Configuration completed successfully!")

if __name__ == "__main__":
    create_config()
    print("Press Enter to exit...")
    input()
