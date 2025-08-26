import sys
from pathlib import Path

# Ensure repo src/ is on sys.path for tests
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
