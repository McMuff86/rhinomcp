#!/usr/bin/env python3
"""Test grasshopper tool directly via MCP server."""

import sys
import os

# Add the server path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rhino_mcp_server', 'src'))

from rhinomcp.tools.run_grasshopper import run_grasshopper
from unittest.mock import MagicMock

def test_grasshopper_direct():
    """Test the grasshopper tool directly."""
    print("Testing grasshopper tool directly...")

    # Mock context
    mock_ctx = MagicMock()

    # Path to grasshopper file
    gh_path = r"c:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"

    print(f"File path: {gh_path}")
    print(f"File exists: {os.path.exists(gh_path)}")

    try:
        # Call the tool directly
        result = run_grasshopper(mock_ctx, gh_path)
        print(f"Tool result: {result}")
        return True
    except Exception as e:
        print(f"Error calling tool: {e}")
        return False

if __name__ == "__main__":
    test_grasshopper_direct()