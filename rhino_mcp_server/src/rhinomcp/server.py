# rhino_mcp_server.py
from mcp.server.fastmcp import FastMCP, Context, Image
import socket
import json
import asyncio
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RhinoMCPServer")

# Global debug flag
_debug_mode = True

def set_debug_mode(enable: bool):
    """Enable or disable debug mode"""
    global _debug_mode
    _debug_mode = enable
    logger.info(f"Debug mode {'enabled' if enable else 'disabled'}")

@dataclass
class RhinoConnection:
    host: str
    port: int
    sock: socket.socket | None = None
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def connect(self) -> bool:
        """Connect to the Rhino addon socket server"""
        if self.sock:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Rhino at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Rhino: {str(e)}")
            self.sock = None
            return False
    
    def is_connected(self) -> bool:
        """Check if the connection to Rhino is active"""
        if self.sock is None:
            return False
        try:
            self.sock.setblocking(False)
            try:
                data = self.sock.recv(1, socket.MSG_PEEK)
                if data == b'':
                    return False
            except BlockingIOError:
                pass
            except ConnectionError:
                return False
            finally:
                self.sock.setblocking(True)
            return True
        except Exception:
            return False
    
    def reconnect(self, max_retries: int | None = None, retry_delay: float | None = None) -> bool:
        """
        Attempt to reconnect to Rhino with configurable retries.
        
        Args:
            max_retries: Number of retry attempts (default: self.max_retries = 3)
            retry_delay: Delay between retries in seconds (default: self.retry_delay = 1.0)
        
        Returns:
            True if reconnection successful, False otherwise
        """
        retries = max_retries if max_retries is not None else self.max_retries
        delay = retry_delay if retry_delay is not None else self.retry_delay
        
        self.disconnect()
        
        for attempt in range(1, retries + 1):
            logger.info(f"Reconnection attempt {attempt}/{retries}...")
            if self.connect():
                logger.info(f"Reconnected to Rhino on attempt {attempt}")
                return True
            if attempt < retries:
                logger.info(f"Waiting {delay}s before next attempt...")
                import time
                time.sleep(delay)
        
        logger.error(f"Failed to reconnect after {retries} attempts")
        return False
    
    def disconnect(self):
        """Disconnect from the Rhino addon"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Rhino: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        # Use a consistent timeout value that matches the addon's timeout
        sock.settimeout(15.0)  # Match the addon's timeout
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        # If we get an empty chunk, the connection might be closed
                        if not chunks:  # If we haven't received anything yet, this is an error
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        # If we get here, it parsed successfully
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    # If we hit a timeout during receiving, break the loop and try to use what we have
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise  # Re-raise to be handled by the caller
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
            
        # If we get here, we either timed out or broke out of the loop
        # Try to use what we have
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                # Try to parse what we have
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                # If we can't parse it, it's incomplete
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def _execute_command(self, command_type: str, params: Dict[str, Any], timeout: float = 15.0) -> Dict[str, Any]:
        """Internal method to execute a command (no retry logic)"""
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        if _debug_mode:
            logger.debug(f"Sending command: {command_type} with params: {json.dumps(params, indent=2)}")
        else:
            logger.info(f"Sending command: {command_type} with params: {params}")

        if self.sock is None:
            raise ConnectionError("Socket is not connected")

        command_json = json.dumps(command)
        self.sock.sendall(command_json.encode('utf-8'))
        if _debug_mode:
            logger.debug(f"Command JSON sent: {command_json}")

        self.sock.settimeout(timeout)
        response_data = self.receive_full_response(self.sock)
        if _debug_mode:
            logger.debug(f"Received raw response: {response_data.decode('utf-8')}")

        response = json.loads(response_data.decode('utf-8'))
        if _debug_mode:
            logger.debug(f"Response parsed: {json.dumps(response, indent=2)}")
        else:
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")

        if response.get("status") == "error":
            logger.error(f"Rhino error: {response.get('message')}")
            raise Exception(response.get("message", "Unknown error from Rhino"))

        return response.get("result", {})

    def send_command(self, command_type: str, params: Dict[str, Any] = {}, timeout: float = 15.0) -> Dict[str, Any]:
        """
        Send a command to Rhino with automatic reconnection on failure.
        
        Args:
            command_type: The command to execute
            params: Command parameters
            timeout: Response timeout in seconds (default: 15.0, max: 120.0)
        """
        timeout = min(max(timeout, 1.0), 120.0)
        
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Rhino")
        
        try:
            return self._execute_command(command_type, params, timeout=timeout)
        except (socket.timeout, ConnectionError, BrokenPipeError, ConnectionResetError, OSError) as e:
            logger.warning(f"Connection error: {str(e)}. Attempting to reconnect...")
            self.sock = None
            
            if self.reconnect():
                logger.info("Reconnected successfully, retrying command...")
                try:
                    return self._execute_command(command_type, params, timeout=timeout)
                except Exception as retry_error:
                    logger.error(f"Command failed after reconnect: {str(retry_error)}")
                    self.sock = None
                    raise Exception(f"Command failed after reconnect: {str(retry_error)}")
            else:
                raise ConnectionError("Failed to reconnect to Rhino. Make sure the Rhino plugin is running.")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Rhino: {str(e)}")
            raise Exception(f"Invalid response from Rhino: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Rhino: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with Rhino: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools
    
    try:
        # Just log that we're starting up
        logger.info("RhinoMCP server starting up")
        
        # Try to connect to Rhino on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            rhino = get_rhino_connection()
            logger.info("Successfully connected to Rhino on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Rhino on startup: {str(e)}")
            logger.warning("Make sure the Rhino addon is running before using Rhino resources or tools")
        
        # Return an empty context - we're using the global connection
        yield {}
    finally:
        # Clean up the global connection on shutdown
        global _rhino_connection
        if _rhino_connection:
            logger.info("Disconnecting from Rhino on shutdown")
            _rhino_connection.disconnect()
            _rhino_connection = None
        logger.info("RhinoMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "RhinoMCP",
    lifespan=server_lifespan
)

# Resource endpoints

# Global connection for resources (since resources can't access context)
_rhino_connection = None

def get_rhino_connection():
    """Get or create a persistent Rhino connection"""
    global _rhino_connection
    
    # Create a new connection if needed
    if _rhino_connection is None:
        _rhino_connection = RhinoConnection(host="127.0.0.1", port=1999)
        if not _rhino_connection.connect():
            logger.error("Failed to connect to Rhino")
            _rhino_connection = None
            raise Exception("Could not connect to Rhino. Make sure the Rhino addon is running.")
        logger.info("Created new persistent connection to Rhino")
    
    return _rhino_connection

# Main execution
def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()