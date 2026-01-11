"""
Create doors using WebSocket-based Grasshopper automation.

This example demonstrates the clean WebSocket-based approach for
running interactive Grasshopper scripts that require user input.

The workflow:
1. Connect to WebSocket stream
2. Start GrasshopperPlayer script asynchronously
3. Wait for prompts and send appropriate inputs
4. Monitor for completion

Usage:
    cd rhino_mcp_server
    uv run python dev/create_doors_websocket_v2.py

Requirements:
    - Rhino running with mcpstart command executed
    - Rahmentuer_UD3.gh file in project root
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import websockets


# Configuration
WS_URL = "ws://127.0.0.1:2000"
GH_FILE = str(Path(__file__).parent.parent.parent / "Rahmentuer_UD3.gh")

# Door configurations
DOORS = [
    {"height": 2200, "width": 910, "origin": "0,0,0"},
    {"height": 2200, "width": 910, "origin": "2000,0,0"},
    {"height": 2200, "width": 910, "origin": "4000,0,0"},
]


async def send_input(ws: websockets.WebSocketClientProtocol, value: str) -> bool:
    """Send input to Rhino command line via WebSocket."""
    print(f"  >> SEND: {repr(value)}")
    message = json.dumps({
        "command": "send_input",
        "input": value,
    })
    await ws.send(message)
    
    # Wait for response
    try:
        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        response = json.loads(msg)
        if response.get("type") == "InputResult":
            return response.get("success", False)
    except asyncio.TimeoutError:
        print("  [WARN] No response for input")
    return False


async def run_script(ws: websockets.WebSocketClientProtocol, script: str) -> bool:
    """Start a script asynchronously via WebSocket."""
    print(f"  >> SCRIPT: {script}")
    message = json.dumps({
        "command": "run_script",
        "script": script,
    })
    await ws.send(message)
    
    # Wait for acknowledgment
    try:
        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        response = json.loads(msg)
        return response.get("type") == "ScriptStarted"
    except asyncio.TimeoutError:
        print("  [WARN] No acknowledgment for script")
    return False


async def wait_for_prompt(
    ws: websockets.WebSocketClientProtocol,
    pattern: str,
    timeout: float = 10.0
) -> Optional[str]:
    """Wait for a prompt containing the pattern."""
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            event = json.loads(msg)
            
            if event.get("type") == "Prompt":
                text = event.get("text", "")
                print(f"  << PROMPT: {text}")
                if pattern.lower() in text.lower():
                    return text
            elif event.get("type") == "ScriptCompleted":
                print(f"  << SCRIPT DONE: success={event.get('success')}")
                return None
            elif event.get("type") == "History":
                text = event.get("text", "")
                if "[ASYNC]" in text:
                    print(f"  << {text}")
                    
        except asyncio.TimeoutError:
            continue
            
    return None


async def create_door(
    ws: websockets.WebSocketClientProtocol,
    height: int,
    width: int, 
    origin: str,
    door_number: int
) -> bool:
    """
    Create a single door using the Rahmentuer_UD3.gh script.
    
    The script expects:
    1. Lichthoehe (height in mm)
    2. Lichtbreite (width in mm)
    3. GetPlane - plane selection (WorldXY, WorldYZ, WorldZX)
    4. GetPlane - origin point
    5. GetPlane - confirmation (possibly)
    """
    print(f"\n{'='*50}")
    print(f"DOOR {door_number}: {height}x{width}mm at {origin}")
    print(f"{'='*50}")
    
    # Start GrasshopperPlayer
    script = f'_-GrasshopperPlayer "{GH_FILE}"'
    if not await run_script(ws, script):
        print("[ERROR] Failed to start script")
        return False
    
    # Wait for and respond to prompts
    
    # 1. Height
    prompt = await wait_for_prompt(ws, "lichthoehe", timeout=10.0)
    if not prompt:
        print("[ERROR] Timeout waiting for height prompt")
        return False
    await asyncio.sleep(0.1)
    await send_input(ws, str(height))
    
    # 2. Width
    prompt = await wait_for_prompt(ws, "lichtbreite", timeout=5.0)
    if not prompt:
        print("[ERROR] Timeout waiting for width prompt")
        return False
    await asyncio.sleep(0.1)
    await send_input(ws, str(width))
    
    # 3. GetPlane Step 1: Select plane type
    prompt = await wait_for_prompt(ws, "getplane", timeout=5.0)
    if not prompt:
        print("[ERROR] Timeout waiting for GetPlane step 1")
        return False
    
    if "worldxy" in prompt.lower():
        await asyncio.sleep(0.1)
        await send_input(ws, "WorldXY")
    
    # 4. GetPlane Step 2: Enter origin
    prompt = await wait_for_prompt(ws, "getplane", timeout=5.0)
    if not prompt:
        # Might already be done
        print("[INFO] No more GetPlane prompts")
        return True
        
    if "parallelgrid" in prompt.lower():
        await asyncio.sleep(0.1)
        await send_input(ws, origin)
    
    # 5. GetPlane Step 3: Confirmation (if any)
    prompt = await wait_for_prompt(ws, "", timeout=3.0)
    if prompt and "getplane" in prompt.lower():
        print(f"[DEBUG] Step 3 prompt: {prompt}")
        await asyncio.sleep(0.1)
        
        # Try different inputs for step 3
        # This is the problematic step that needs debugging
        await send_input(ws, "_Enter")  # Rhino command to confirm plane
        
    # Wait for completion
    await asyncio.sleep(2.0)
    print(f"[OK] Door {door_number} inputs sent")
    return True


async def main():
    """Create multiple doors using WebSocket automation."""
    print("="*50)
    print("WEBSOCKET DOOR CREATION")
    print("="*50)
    print(f"GH File: {GH_FILE}")
    print(f"WebSocket: {WS_URL}")
    print(f"Doors to create: {len(DOORS)}")
    
    # Check if GH file exists
    if not Path(GH_FILE).exists():
        print(f"[ERROR] GH file not found: {GH_FILE}")
        sys.exit(1)
    
    # Connect to WebSocket
    print(f"\n[WS] Connecting to {WS_URL}...")
    
    try:
        async with websockets.connect(WS_URL) as ws:
            # Get welcome message
            welcome = await ws.recv()
            data = json.loads(welcome)
            print(f"[WS] Connected! Prompt: {data.get('current_prompt', '')}")
            
            success_count = 0
            
            for i, door in enumerate(DOORS, 1):
                # Drain events between doors
                if i > 1:
                    print("\n[WAIT] Pausing before next door...")
                    await asyncio.sleep(2.0)
                    while True:
                        try:
                            await asyncio.wait_for(ws.recv(), timeout=0.2)
                        except asyncio.TimeoutError:
                            break
                
                success = await create_door(
                    ws=ws,
                    height=door["height"],
                    width=door["width"],
                    origin=door["origin"],
                    door_number=i
                )
                
                if success:
                    success_count += 1
            
            # Summary
            print("\n" + "="*50)
            print(f"RESULT: {success_count}/{len(DOORS)} doors")
            print("="*50)
            print("\n[NOTE] Check Rhino to verify door creation.")
            print("[NOTE] If doors weren't created, run debug_getplane.py")
            
    except ConnectionRefusedError:
        print("[ERROR] Cannot connect to WebSocket.")
        print("        Make sure Rhino is running with 'mcpstart' executed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
