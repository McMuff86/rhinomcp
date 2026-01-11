"""
Create doors using WebSocket-based real-time monitoring.

This is the CORRECT way for an AI agent to interact with Rhino:
1. Connect to WebSocket for real-time event monitoring
2. Start script asynchronously (non-blocking)
3. Watch WebSocket for prompts
4. Respond to prompts via send_command_input

Requires the new C# handlers:
- start_script_async: Start script without blocking
- send_command_input: Send input to command line
- get_current_prompt: Get current prompt text
"""

import asyncio
import json
import socket
import threading
import time
from typing import Optional, Callable

import websockets


class RhinoWebSocketAgent:
    """
    AI Agent that controls Rhino using WebSocket for real-time monitoring.
    """
    
    def __init__(self, tcp_host="127.0.0.1", tcp_port=1999, ws_port=2000):
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.ws_url = f"ws://{tcp_host}:{ws_port}"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.events = []
        self.current_prompt = ""
        self._listening = False
        self._listen_task = None
        
    async def connect(self):
        """Connect to WebSocket for real-time monitoring."""
        print(f"[WS] Connecting to {self.ws_url}...")
        self.ws = await websockets.connect(self.ws_url)
        welcome = await self.ws.recv()
        data = json.loads(welcome)
        self.current_prompt = data.get("current_prompt", "")
        print(f"[WS] Connected! Initial prompt: {self.current_prompt}")
        return True
        
    async def disconnect(self):
        """Disconnect from WebSocket."""
        self._listening = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self.ws:
            await self.ws.close()
            self.ws = None
        print("[WS] Disconnected")
            
    async def start_listening(self):
        """Start background listening for WebSocket events."""
        self._listening = True
        self._listen_task = asyncio.create_task(self._listen_loop())
        
    async def _listen_loop(self):
        """Background loop to receive WebSocket events."""
        while self._listening and self.ws:
            try:
                msg = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                event = json.loads(msg)
                self.events.append(event)
                
                # Update current prompt if it's a Prompt event
                if event.get("type") == "Prompt":
                    self.current_prompt = event.get("text", "")
                    print(f"[WS] Prompt: {self.current_prompt}")
                elif event.get("type") == "History":
                    text = event.get("text", "")[:60]
                    print(f"[WS] History: {text}")
                    
            except asyncio.TimeoutError:
                pass
            except websockets.ConnectionClosed:
                print("[WS] Connection closed")
                break
            except Exception as e:
                print(f"[WS] Error: {e}")
                break
    
    def send_tcp_command(self, command: str, params: dict, timeout: float = 5.0) -> dict:
        """Send command to Rhino via TCP (blocking but with short timeout)."""
        # Use "type" key as expected by C# RhinoMCPServer
        message = json.dumps({"type": command, "params": params})
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((self.tcp_host, self.tcp_port))
            sock.sendall((message + "\n").encode('utf-8'))
            
            response = b""
            try:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if b"\n" in chunk:
                        break
            except socket.timeout:
                pass
                    
            if response:
                return json.loads(response.decode('utf-8'))
            return {"error": "No response"}
    
    def start_script_async(self, script: str) -> dict:
        """Start a Rhino script asynchronously (non-blocking)."""
        return self.send_tcp_command("start_script_async", {"script": script})
    
    def send_input(self, input_text: str) -> dict:
        """Send input to Rhino command line."""
        return self.send_tcp_command("send_command_input", {"input": input_text})
    
    def get_prompt(self) -> str:
        """Get current Rhino command prompt."""
        result = self.send_tcp_command("get_current_prompt", {})
        return result.get("prompt", "")
    
    async def wait_for_prompt(self, contains: str, timeout: float = 10.0) -> bool:
        """Wait for a specific prompt to appear."""
        start = time.time()
        while time.time() - start < timeout:
            # Check current events
            for event in reversed(self.events[-20:]):
                if event.get("type") == "Prompt":
                    text = event.get("text", "")
                    if contains.lower() in text.lower():
                        return True
            
            # Also check via TCP
            prompt = self.get_prompt()
            if contains.lower() in prompt.lower():
                return True
                
            await asyncio.sleep(0.2)
        return False
    
    async def create_door(
        self, 
        file_path: str, 
        height: int = 2200, 
        width: int = 910,
        origin_x: float = 0,
        origin_y: float = 0,
        origin_z: float = 0
    ) -> bool:
        """
        Create a door using GrasshopperPlayer with WebSocket monitoring.
        
        Flow:
        1. Start GrasshopperPlayer async (non-blocking)
        2. Monitor WebSocket for prompts
        3. Respond to height/width/plane prompts automatically
        """
        print(f"\n{'='*60}")
        print(f"Creating door: {height}x{width}mm at ({origin_x}, {origin_y}, {origin_z})")
        print(f"{'='*60}")
        
        # Clear old events
        self.events.clear()
        
        # Start the GrasshopperPlayer command asynchronously
        script = f'_-GrasshopperPlayer "{file_path}"'
        print(f"[CMD] Starting: {script}")
        
        result = self.start_script_async(script)
        print(f"[CMD] Result: {result}")
        
        # Wait a moment for script to start
        await asyncio.sleep(0.5)
        
        # Monitor and respond to prompts
        inputs_to_send = [
            (["lichthoehe", "height"], str(height)),
            (["lichtbreite", "width"], str(width)),
            (["getplane", "plane"], f"{origin_x},{origin_y},{origin_z}"),
        ]
        
        for prompt_keywords, input_value in inputs_to_send:
            # Check current prompt
            current = self.get_prompt()
            print(f"[PROMPT] Current: {current}")
            
            # Wait for one of the expected prompts
            found = False
            for _ in range(30):  # Max 3 seconds per prompt
                current = self.get_prompt()
                for keyword in prompt_keywords:
                    if keyword.lower() in current.lower():
                        found = True
                        break
                if found:
                    break
                await asyncio.sleep(0.1)
            
            if found:
                print(f"[INPUT] Sending: {input_value}")
                self.send_input(input_value)
                await asyncio.sleep(0.3)
            else:
                print(f"[WARN] Expected prompt containing {prompt_keywords}, got: {current}")
                # Try sending anyway
                print(f"[INPUT] Sending anyway: {input_value}")
                self.send_input(input_value)
                await asyncio.sleep(0.3)
        
        # Wait for completion
        await asyncio.sleep(1)
        
        # Check if we're back to normal prompt
        final_prompt = self.get_prompt()
        print(f"[DONE] Final prompt: {final_prompt}")
        
        return "command" in final_prompt.lower()


async def main():
    """Create 3 doors using WebSocket-based automation."""
    file_path = r"C:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"
    
    agent = RhinoWebSocketAgent()
    
    try:
        # Connect to WebSocket
        await agent.connect()
        
        # Start background listening
        await agent.start_listening()
        
        # Create 3 doors at different positions
        doors = [
            {"height": 2200, "width": 910, "origin_x": 0, "origin_y": 0, "origin_z": 0},
            {"height": 2200, "width": 910, "origin_x": 2000, "origin_y": 0, "origin_z": 0},
            {"height": 2200, "width": 910, "origin_x": 4000, "origin_y": 0, "origin_z": 0},
        ]
        
        for i, door in enumerate(doors, 1):
            print(f"\n\n{'#'*60}")
            print(f"# DOOR {i} of {len(doors)}")
            print(f"{'#'*60}")
            
            success = await agent.create_door(file_path, **door)
            
            if success:
                print(f"\n[SUCCESS] Door {i} created!")
            else:
                print(f"\n[FAILED] Door {i} may need manual input")
            
            # Wait between doors
            await asyncio.sleep(1)
        
        print("\n\n" + "=" * 60)
        print("ALL DOORS COMPLETED")
        print("=" * 60)
        
    finally:
        await agent.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
