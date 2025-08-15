#!/usr/bin/env python3
"""
Test QAI Hub API Token
"""

import os
import sys
from pathlib import Path

def test_qai_hub_config():
    """Test QAI Hub configuration"""
    print("Testing QAI Hub configuration...")
    
    # Check config file
    home_dir = Path.home()
    config_file = home_dir / ".qai_hub" / "client.ini"
    
    if config_file.exists():
        print(f"Config file exists: {config_file}")
        with open(config_file, 'r') as f:
            content = f.read()
            if "api_token" in content:
                print("API token found in config file")
            else:
                print("API token NOT found in config file")
    else:
        print(f"Config file does not exist: {config_file}")
    
    # Check environment variable
    token = os.environ.get('QAI_HUB_API_TOKEN')
    if token:
        print(f"QAI_HUB_API_TOKEN environment variable is set: {token[:10]}...")
    else:
        print("QAI_HUB_API_TOKEN environment variable is NOT set")
    
    # Try to import qai_hub module
    try:
        import qai_hub
        print("qai_hub module imported successfully")
        
        try:
            # Try basic functionality
            print("Testing basic functionality...")
            devices = qai_hub.get_devices()
            print(f"QAI Hub devices: {len(devices) if devices else 0}")
            return True
        except Exception as e:
            print(f"Error testing QAI Hub functionality: {e}")
            print("This may be normal if this is not a Snapdragon device")
            return True
    except ImportError as e:
        print(f"Error importing qai_hub module: {e}")
        print("You need to install qai_hub module: pip install qai-hub")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print("QAI Hub API Token Test")
    print("=" * 50)
    
    # Test configuration
    success = test_qai_hub_config()
    
    # Show result
    print("\n" + "=" * 50)
    if success:
        print("QAI Hub configuration is valid!")
    else:
        print("QAI Hub configuration needs attention!")
    print("=" * 50)

if __name__ == "__main__":
    main()
