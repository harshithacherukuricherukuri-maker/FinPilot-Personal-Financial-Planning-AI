"""FinPilot Test Suite."""
import sys
from pathlib import Path

# Ensure backend directory is in sys.path when running pytest from root or any directory
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))
