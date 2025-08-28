import json
import os
from typing import Dict


CONFIG_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'config'))
DEFAULT_PATH = os.path.join(CONFIG_DIR, 'ui_defaults.json')


def load_ui_defaults() -> Dict:
    try:
        if os.path.isfile(DEFAULT_PATH):
            with open(DEFAULT_PATH, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
    except Exception:
        try:
            # attempt to read from older config location
            p = os.path.join(os.getcwd(), 'config', 'ui_defaults.json')
            if os.path.isfile(p):
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f) or {}
        except Exception:
            pass
    return {}


def save_ui_defaults(d: Dict) -> bool:
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(DEFAULT_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        try:
            # fallback write to cwd config
            p = os.path.join(os.getcwd(), 'config')
            os.makedirs(p, exist_ok=True)
            with open(os.path.join(p, 'ui_defaults.json'), 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
