import os
import sys

def setup_device_cloud():
    """Setup device cloud environment and fix configuration issues"""
    
    print("Setting up device cloud environment...")
    
    # Create directory if it doesn't exist
    qai_hub_dir = os.path.expanduser("~/.qai_hub")
    os.makedirs(qai_hub_dir, exist_ok=True)
    
    # Create client.ini file
    client_ini_path = os.path.join(qai_hub_dir, "client.ini")
    
    # Configuration content
    config_content = """[DEFAULT]
api_key = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
api_token = pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d
host = https://api.aihub.qualcomm.com
api_url = https://api.aihub.qualcomm.com
api_version = v1
"""
    
    try:
        # Write configuration file
        with open(client_ini_path, "w") as f:
            f.write(config_content)
        
        print(f"Created configuration file at: {client_ini_path}")
        print("Configuration content:")
        print(config_content)
        
        # Verify file was created
        if os.path.exists(client_ini_path):
            print(f"Verified: Configuration file exists at {client_ini_path}")
            # Read and print file content to verify
            with open(client_ini_path, "r") as f:
                read_content = f.read()
            print("Verified file content:")
            print(read_content)
        else:
            print(f"ERROR: Failed to create configuration file at {client_ini_path}")
        
        # Set environment variables
        os.environ["QAI_API_KEY"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
        os.environ["QAI_API_TOKEN"] = "pcu8nz63e4j3nzqgy7tjzvr2dmpc01cocltahr0d"
        os.environ["QAI_HOST"] = "https://api.aihub.qualcomm.com"
        os.environ["QAI_API_URL"] = "https://api.aihub.qualcomm.com"
        os.environ["QAI_API_VERSION"] = "v1"
        
        print("Environment variables set:")
        print(f"QAI_API_KEY = {os.environ.get('QAI_API_KEY')}")
        print(f"QAI_API_TOKEN = {os.environ.get('QAI_API_TOKEN')}")
        print(f"QAI_HOST = {os.environ.get('QAI_HOST')}")
        print(f"QAI_API_URL = {os.environ.get('QAI_API_URL')}")
        print(f"QAI_API_VERSION = {os.environ.get('QAI_API_VERSION')}")
        
        return True
        
    except Exception as e:
        print(f"Setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = setup_device_cloud()
    
    if success:
        print("Device cloud setup complete!")
        print("You can now run the Dragon X Fall Detection System.")
    else:
        print("Device cloud setup failed. Please check the error message.")
    
    print("Press any key to exit...")
    input()
