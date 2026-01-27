#!/usr/bin/env python3
"""
Direct TCP client for RhinoMCP plugin.
Bypasses the MCP server layer for direct Clawdbot integration.
"""

import socket
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

CONFIG = load_config()
CONNECTION = CONFIG.get("connection", {})

# Defaults from config
DEFAULT_HOST = CONNECTION.get("host", "172.31.96.1")
DEFAULT_PORT = CONNECTION.get("port", 1999)
DEFAULT_TIMEOUT = CONNECTION.get("timeout", 15.0)
DEFAULT_RETRIES = CONNECTION.get("max_retries", 3)
DEFAULT_RETRY_DELAY = CONNECTION.get("retry_delay", 1.0)


class RhinoClient:
    """TCP client for communicating with RhinoMCP plugin."""
    
    def __init__(self, host: str = None, port: int = None, timeout: float = None):
        self.host = host or DEFAULT_HOST
        self.port = port or DEFAULT_PORT
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.sock: Optional[socket.socket] = None
    
    def connect(self) -> bool:
        """Connect to Rhino plugin."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Connection failed: {e}", file=sys.stderr)
            self.sock = None
            return False
    
    def disconnect(self):
        """Close the connection."""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
    
    def send_command(self, cmd_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command and receive the response."""
        if not self.sock:
            raise ConnectionError("Not connected to Rhino")
        
        command = {
            "type": cmd_type,
            "params": params or {}
        }
        
        # Send command
        cmd_json = json.dumps(command)
        self.sock.sendall(cmd_json.encode('utf-8'))
        
        # Receive response (handle chunked data)
        chunks = []
        while True:
            try:
                chunk = self.sock.recv(8192)
                if not chunk:
                    break
                chunks.append(chunk)
                
                # Try to parse as complete JSON
                try:
                    data = b''.join(chunks)
                    return json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    continue  # Incomplete, keep receiving
                    
            except socket.timeout:
                break
        
        if chunks:
            data = b''.join(chunks)
            try:
                return json.loads(data.decode('utf-8'))
            except json.JSONDecodeError:
                raise Exception(f"Invalid JSON response: {data[:200]}")
        
        raise Exception("No response received")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, *args):
        self.disconnect()


def get_client() -> RhinoClient:
    """Get a connected RhinoClient instance."""
    client = RhinoClient()
    if not client.connect():
        raise ConnectionError(f"Could not connect to Rhino at {client.host}:{client.port}")
    return client


# CLI interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='RhinoMCP Client')
    parser.add_argument('command', help='Command: ping, info, or raw command type')
    parser.add_argument('--params', '-p', type=str, help='JSON params', default='{}')
    parser.add_argument('--host', default=None, help=f'Host (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=None, help=f'Port (default: {DEFAULT_PORT})')
    
    args = parser.parse_args()
    
    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON params: {e}", file=sys.stderr)
        sys.exit(1)
    
    # All commands use the same client with host/port from args or config
    with RhinoClient(args.host, args.port) as client:
        if args.command == 'ping':
            result = client.send_command("ping")
        elif args.command == 'info':
            result = client.send_command("get_document_info")
        else:
            result = client.send_command(args.command, params)
    
    print(json.dumps(result, indent=2))
