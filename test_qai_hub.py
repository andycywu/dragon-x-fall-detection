import os
import sys

try:
    import qai_hub as hub
    print("Successfully imported QAI Hub module")
    
    try:
        print("Trying to get QAI Hub devices...")
        devices = hub.get_devices()
        print(f"Success! Found {len(devices)} devices")
        for i, device in enumerate(devices):
            print(f"Device {i+1}: {device.name} ({device.os})")
    except Exception as e:
        print(f"Error getting devices: {e}")
        
        # Try to print more detailed error information
        import traceback
        traceback.print_exc()
        
        # Check environment variables
        qai_env_vars = [var for var in os.environ if 'QAI' in var]
        if qai_env_vars:
            print("\nQAI Environment Variables:")
            for var in qai_env_vars:
                print(f"{var}={os.environ[var]}")
        
        # Try to access config directly
        try:
            from qai_hub.api_utils import load_default_api_config
            config = load_default_api_config()
            print("\nConfig loaded successfully:")
            print(config)
        except Exception as config_error:
            print(f"\nError loading config: {config_error}")
        
except ImportError as e:
    print(f"Failed to import QAI Hub: {e}")

print("\nPress Enter to exit...")
input()
