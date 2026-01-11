#!/usr/bin/env python3
"""Simple MCP client to test the grasshopper tool."""

import socket
import json
import time

def send_mcp_request(method, params=None):
    """Send MCP request and return response."""
    # MCP JSON-RPC format
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }

    if params:
        request["params"] = params

    # Convert to JSON
    request_json = json.dumps(request)

    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 1999))
        sock.settimeout(30)

        # Send request
        sock.send((request_json + '\n').encode('utf-8'))

        # Receive response
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if b'\n' in response_data:
                break

        sock.close()

        # Parse response
        response_str = response_data.decode('utf-8').strip()
        if response_str:
            return json.loads(response_str)
        else:
            return None

    except Exception as e:
        print(f"Socket error: {e}")
        return None

def test_list_tools():
    """Test listing available tools."""
    print("Testing tool listing...")
    response = send_mcp_request("tools/list")

    if response and 'result' in response:
        tools = response['result']
        print(f"Available tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.get('name', 'unknown')}")
        return True
    else:
        print(f"Failed to list tools: {response}")
        return False

def test_grasshopper_tool():
    """Test the grasshopper tool."""
    print("\nTesting grasshopper tool...")

    gh_path = r"c:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"

    response = send_mcp_request("tools/call", {
        "name": "run_grasshopper",
        "arguments": {
            "file_path": gh_path
        }
    })

    print(f"Response: {json.dumps(response, indent=2)}")
    return response

if __name__ == "__main__":
    # First list available tools
    if test_list_tools():
        # Then test grasshopper tool
        test_grasshopper_tool()
    else:
        print("Cannot test grasshopper tool - tool listing failed")