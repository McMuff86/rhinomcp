"""Simple script to check if Rhino MCP server is running."""
import socket
import sys
import time

def check_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 1999))
        sock.close()

        if result == 0:
            print("[SUCCESS] Rhino MCP server is running and accessible!")
            return True
        else:
            print("[ERROR] Rhino MCP server is not running.")
            print("\nTo start the MCP server:")
            print("1. Make sure Rhino 8 is open")
            print("2. In Rhino command line, type: mcpstart")
            print("3. Wait for confirmation message")
            print("4. Run this script again")
            return False
    except Exception as e:
        print(f"[ERROR] Connection check failed: {e}")
        return False

if __name__ == "__main__":
    print("Checking Rhino MCP server connection...")
    if check_connection():
        print("\n*** Ready to test mesh operations! ***")
        print("Run: cd rhino_mcp_server && python dev/test_mesh_operations.py")
    else:
        sys.exit(1)