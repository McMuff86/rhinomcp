#!/usr/bin/env python3
"""Test script to run Grasshopper definition via MCP."""

import requests
import json
import time
import os

def test_ping():
    """Test basic ping tool first."""
    # MCP server endpoint
    url = "http://127.0.0.1:1999/call_tool"

    # Request payload
    payload = {
        "tool_name": "ping",
        "arguments": {}
    }

    print("Testing ping tool...")

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_grasshopper():
    """Test running a Grasshopper definition."""
    # Path to the Grasshopper file
    gh_path = r"c:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"

    # MCP server endpoint
    url = "http://127.0.0.1:1999/call_tool"

    # Request payload
    payload = {
        "tool_name": "run_grasshopper",
        "arguments": {
            "file_path": gh_path
        }
    }

    print(f"Testing Grasshopper execution with file: {gh_path}")
    print(f"File exists: {os.path.exists(gh_path)}")

    try:
        response = requests.post(url, json=payload, timeout=60)  # Longer timeout for Grasshopper
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # First test basic connectivity
    if test_ping():
        print("\nPing successful, testing Grasshopper...")
        test_grasshopper()
    else:
        print("Ping failed - MCP server not responding. Make sure Rhino MCP plugin is started with 'mcpstart'.")