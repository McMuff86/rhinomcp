"""
Debug GetPlane behavior in GrasshopperPlayer.

This script systematically tests different inputs for the GetPlane command
to understand what Rhino expects after the origin point is entered.

GetPlane appears to have 3 steps:
1. Plane type selection: WorldXY, WorldYZ, WorldZX
2. Origin point or mode selection: ParallelGrid, ParallelXY, etc.
3. Confirmation or rotation point

Hypothesis: Step 3 might expect:
- A second point for rotation (X-axis direction)
- Enter/empty string to confirm
- _Enter or _Accept command
- The plane is already set and no input is needed
"""

import asyncio
import json
import socket
import time
from typing import Optional, List, Tuple

import websockets


# Configuration
WS_URL = "ws://127.0.0.1:2000"
TCP_HOST = "127.0.0.1"
TCP_PORT = 1999
GH_FILE = r"C:\Users\Adi.Muff\repos\rhinomcp\Rahmentuer_UD3.gh"


def send_tcp_command(command: str, params: dict, timeout: float = 5.0) -> dict:
    """Send TCP command and wait for response."""
    message = json.dumps({"type": command, "params": params})
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((TCP_HOST, TCP_PORT))
            sock.sendall((message + "\n").encode('utf-8'))
            response = sock.recv(8192).decode('utf-8')
            return json.loads(response)
    except Exception as e:
        print(f"[TCP ERROR] {e}")
        return {"error": str(e)}


def send_input(value: str) -> bool:
    """Send input to Rhino command line."""
    print(f"  >> SEND: '{value}'")
    result = send_tcp_command("send_command_input", {"input": value})
    return result.get("status") == "success"


def start_script(script: str) -> bool:
    """Start a script asynchronously."""
    print(f"  >> START: {script}")
    result = send_tcp_command("start_script_async", {"script": script})
    return result.get("status") == "success"


def get_current_prompt() -> str:
    """Get the current Rhino prompt."""
    result = send_tcp_command("get_current_prompt", {})
    return result.get("result", {}).get("prompt", "")


async def wait_for_prompt_containing(
    ws: websockets.WebSocketClientProtocol,
    pattern: str,
    timeout: float = 10.0
) -> Optional[str]:
    """Wait for a prompt containing the given pattern."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
            event = json.loads(msg)
            if event.get("type") == "Prompt":
                text = event.get("text", "")
                print(f"  << PROMPT: {text}")
                if pattern.lower() in text.lower():
                    return text
        except asyncio.TimeoutError:
            continue
        except websockets.ConnectionClosed:
            print("  [WS] Connection closed")
            return None
    return None


async def drain_events(ws: websockets.WebSocketClientProtocol, seconds: float = 0.5):
    """Drain pending WebSocket events."""
    end_time = time.time() + seconds
    while time.time() < end_time:
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.1)
            event = json.loads(msg)
            if event.get("type") not in ["Heartbeat"]:
                text = event.get("text", "")[:60]
                print(f"  [drain] {event.get('type')}: {text}")
        except asyncio.TimeoutError:
            break


async def test_getplane_sequence(
    ws: websockets.WebSocketClientProtocol,
    height: int,
    width: int,
    origin: str,
    step3_input: str,
    test_name: str
) -> Tuple[bool, str]:
    """
    Test a specific GetPlane input sequence.
    
    Returns: (success, description)
    """
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"  Height: {height}, Width: {width}, Origin: {origin}")
    print(f"  Step 3 Input: '{step3_input}' (repr: {repr(step3_input)})")
    print(f"{'='*60}")
    
    # Drain any pending events
    await drain_events(ws, 0.3)
    
    # Start GrasshopperPlayer
    script = f'_-GrasshopperPlayer "{GH_FILE}"'
    if not start_script(script):
        return False, "Failed to start script"
    
    # Wait for Lichthoehe prompt
    prompt = await wait_for_prompt_containing(ws, "lichthoehe", timeout=10.0)
    if not prompt:
        return False, "Timeout waiting for Lichthoehe prompt"
    
    await asyncio.sleep(0.1)
    send_input(str(height))
    
    # Wait for Lichtbreite prompt
    prompt = await wait_for_prompt_containing(ws, "lichtbreite", timeout=5.0)
    if not prompt:
        return False, "Timeout waiting for Lichtbreite prompt"
    
    await asyncio.sleep(0.1)
    send_input(str(width))
    
    # Wait for GetPlane Step 1 (WorldXY/WorldYZ/WorldZX)
    prompt = await wait_for_prompt_containing(ws, "getplane", timeout=5.0)
    if not prompt:
        return False, "Timeout waiting for GetPlane step 1"
    
    if "worldxy" in prompt.lower():
        await asyncio.sleep(0.1)
        send_input("WorldXY")
    else:
        return False, f"Unexpected GetPlane prompt: {prompt}"
    
    # Wait for GetPlane Step 2 (Origin/ParallelGrid)
    prompt = await wait_for_prompt_containing(ws, "getplane", timeout=5.0)
    if not prompt:
        return False, "Timeout waiting for GetPlane step 2"
    
    if "parallelgrid" in prompt.lower() or "parallelxy" in prompt.lower():
        await asyncio.sleep(0.1)
        send_input(origin)
    else:
        return False, f"Unexpected GetPlane step 2 prompt: {prompt}"
    
    # Wait for GetPlane Step 3 (just Undo, or back to Command)
    prompt = await wait_for_prompt_containing(ws, "", timeout=3.0)
    if not prompt:
        # Maybe already done?
        current = get_current_prompt()
        print(f"  [CHECK] Current prompt after step 2: {current}")
        if "command" in current.lower():
            return True, "Completed after step 2 (no step 3 needed)"
        return False, "Timeout waiting for any prompt after step 2"
    
    # Check if we're back at Command prompt (done!)
    if "command" in prompt.lower() and "getplane" not in prompt.lower():
        return True, "Completed after step 2"
    
    # GetPlane step 3 - try the specified input
    if "getplane" in prompt.lower():
        print(f"  [STEP 3] Sending: {repr(step3_input)}")
        await asyncio.sleep(0.1)
        send_input(step3_input)
        
        # Wait for completion or next prompt
        for _ in range(10):
            prompt = await wait_for_prompt_containing(ws, "", timeout=2.0)
            if prompt:
                if "command" in prompt.lower() and "getplane" not in prompt.lower():
                    return True, f"Completed with step 3 input: {repr(step3_input)}"
                elif "getplane" in prompt.lower():
                    print(f"  [WARN] Still in GetPlane: {prompt}")
                    continue
            else:
                current = get_current_prompt()
                if "command" in current.lower():
                    return True, f"Completed (prompt check)"
                break
        
        return False, "GetPlane did not complete after step 3"
    
    return False, f"Unexpected state: {prompt}"


async def cancel_current_command(ws: websockets.WebSocketClientProtocol):
    """Try to cancel the current command."""
    print("\n  [CANCEL] Attempting to cancel...")
    send_input("_Cancel")
    await asyncio.sleep(0.5)
    send_input("_Cancel")
    await asyncio.sleep(0.5)
    await drain_events(ws, 0.5)


async def main():
    """Run GetPlane debug tests."""
    print("="*60)
    print("GETPLANE DEBUG SESSION")
    print("="*60)
    print(f"GH File: {GH_FILE}")
    print(f"WebSocket: {WS_URL}")
    print(f"TCP: {TCP_HOST}:{TCP_PORT}")
    
    # Test configurations for step 3
    step3_tests = [
        ("", "Empty string (Enter)"),
        ("_Enter", "_Enter command"),
        ("Enter", "Enter word"),
        ("_Accept", "_Accept command"),
        ("0,0,1", "Second point for rotation"),
        ("1,0,0", "X-axis direction point"),
    ]
    
    # Connect to WebSocket
    print(f"\n[WS] Connecting to {WS_URL}...")
    
    try:
        async with websockets.connect(WS_URL) as ws:
            # Get welcome message
            welcome = await ws.recv()
            data = json.loads(welcome)
            print(f"[WS] Connected! Current prompt: {data.get('current_prompt', '')}")
            
            # Check if Rhino is ready
            current = get_current_prompt()
            if "command" not in current.lower():
                print(f"[WARN] Rhino not at Command prompt: {current}")
                print("[INFO] Attempting to cancel any running command...")
                await cancel_current_command(ws)
            
            results = []
            
            # Run each test
            for step3_input, test_name in step3_tests:
                try:
                    success, description = await test_getplane_sequence(
                        ws=ws,
                        height=2200,
                        width=910,
                        origin="0,0,0",
                        step3_input=step3_input,
                        test_name=test_name
                    )
                    results.append((test_name, success, description))
                    
                    if success:
                        print(f"\n  *** SUCCESS: {test_name} ***")
                        print(f"  Description: {description}")
                        # Found a working solution!
                        break
                    else:
                        print(f"\n  [FAILED] {test_name}: {description}")
                        # Cancel and try next
                        await cancel_current_command(ws)
                        await asyncio.sleep(1.0)
                        
                except Exception as e:
                    print(f"\n  [ERROR] {test_name}: {e}")
                    results.append((test_name, False, str(e)))
                    await cancel_current_command(ws)
                    await asyncio.sleep(1.0)
            
            # Print summary
            print("\n" + "="*60)
            print("RESULTS SUMMARY")
            print("="*60)
            for name, success, desc in results:
                status = "SUCCESS" if success else "FAILED"
                print(f"  [{status}] {name}: {desc}")
                
    except Exception as e:
        print(f"[ERROR] WebSocket connection failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
