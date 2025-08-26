"""
Helper to upload quantized models to QAI Hub using existing `qaihub_client` wrapper.
This script does NOT auto-upload; it prepares a function and shows usage. User must provide credentials / enable upload.
"""
from pathlib import Path
import json

ROOT = Path(__file__).parents[1]
ZIP_FILE = ROOT / 'quantized_models_bundle.zip'
META_FILE = ROOT / 'quantized_package_metadata.json'


def print_metadata():
    if not META_FILE.exists():
        print('metadata not found:', META_FILE)
        return
    print(META_FILE.read_text())


def load_client():
    try:
        from ..modules.qaihub_client import QAIHubClient
        client = QAIHubClient()
        return client
    except Exception as e:
        print('Could not import QAIHubClient:', e)
        return None


def upload_all():
    client = load_client()
    if client is None:
        print('QAI Hub client not available. Fill credentials and ensure SDK installed in environment.')
        return
    meta = json.loads(META_FILE.read_text())
    for entry in meta.get('models', []):
        path = Path(entry['path'])
        if not path.exists():
            print('missing', path)
            continue
        print('Uploading', path.name)
        # Example: client.upload_model(path)  # implement in QAIHubClient


if __name__ == '__main__':
    print('This helper does not auto-upload. Use upload_all() after configuring credentials.')
