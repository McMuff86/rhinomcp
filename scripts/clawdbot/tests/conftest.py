"""Shared test fixtures for RhinoMCP tests."""
import sys
from pathlib import Path

# Add parent dir to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
