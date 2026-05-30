"""Pytest configuration: put the project root on sys.path so `import matb_analysis` works."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
