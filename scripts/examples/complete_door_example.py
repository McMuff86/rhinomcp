#!/usr/bin/env python3
"""
Example: Complete door creation with Rahmentuer_UD5.gh

This example demonstrates:
- WebSocket-based interactive Grasshopper script execution
- Handling multiple prompts in sequence
- Intelligent prompt analysis and response
- Error handling and timeout management

Usage:
    python scripts/examples/complete_door_example.py
"""

import asyncio
import json
import socket
import websockets
from pathlib import Path

# Get project root for relative paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
GH_FILE = PROJECT_ROOT / "Rahmentuer_UD5.gh"


def send_tcp(command: str, params: dict) -> dict:
    """Send command via TCP."""
    msg = json.dumps({"type": command, "params": params})
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect(("127.0.0.1", 1999))
        s.sendall((msg + "\n").encode())
        return json.loads(s.recv(8192).decode())


async def create_door_example(height: int = 2200, width: int = 1200, point: str = "0,0,0"):
    """
    Example function to create a door using Rahmentuer_UD5.gh
    
    Args:
        height: Door height in mm
        width: Door width in mm
        point: Door position as "x,y,z"
    """
    print("=" * 70)
    print("EXAMPLE: Complete Door Creation with Rahmentuer_UD5.gh")
    print("=" * 70)
    print(f"Parameters: height={height}mm, width={width}mm, point={point}")

    # Get initial object count
    doc_before = send_tcp("get_document_info", {})
    obj_before = doc_before.get("result", {}).get("total_objects", 0)
    print(f"Objects before: {obj_before}")

    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"Connected. Current prompt: {data.get('current_prompt')}")

        # Start GrasshopperPlayer
        print(f"\n>>> Starting GrasshopperPlayer: {GH_FILE}")
        await ws.send(json.dumps({
            "command": "run_script",
            "script": f'_-GrasshopperPlayer "{GH_FILE}"'
        }))

        # Expected input sequence
        inputs = [
            (str(height), "Lichthoehe (height)"),
            (str(width), "Lichtbreite (width)"),
            (point, "Get Point (position)"),
            ("_Enter", "Bandseite (hinge side - accept default)")
        ]

        sent_count = 0
        timeout_seconds = 60
        start_time = asyncio.get_event_loop().time()

        print("\nSending inputs...")
        print("-" * 50)

        for iteration in range(100):
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                print(f"\n[ERROR] Timeout exceeded ({timeout_seconds}s)")
                break

            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")

                if evt_type == "Prompt":
                    print(f"\n[{iteration:2d}] PROMPT: '{text}'")

                    await asyncio.sleep(0.5)
                    text_lower = text.lower()

                    # Match prompts and send inputs
                    if "lichthoe" in text_lower and sent_count == 0:
                        value, desc = inputs[0]
                        print(f"  >>> {desc}: {value}")
                        await ws.send(json.dumps({"command": "send_input", "input": value}))
                        sent_count += 1

                    elif "lichtbreite" in text_lower and sent_count == 1:
                        value, desc = inputs[1]
                        print(f"  >>> {desc}: {value}")
                        await ws.send(json.dumps({"command": "send_input", "input": value}))
                        sent_count += 1

                    elif ("get point" in text_lower or "point" in text_lower) and sent_count == 2:
                        value, desc = inputs[2]
                        print(f"  >>> {desc}: {value}")
                        await ws.send(json.dumps({"command": "send_input", "input": value}))
                        sent_count += 1

                    elif "bandseite" in text_lower and sent_count == 3:
                        value, desc = inputs[3]
                        print(f"  >>> {desc}: [Enter for default]")
                        await ws.send(json.dumps({"command": "send_input", "input": value}))
                        sent_count += 1

                    elif text_lower.strip() == "command":
                        print("\n*** Script completed successfully! ***")
                        break

                elif evt_type == "ScriptCompleted":
                    success = event.get("success", False)
                    print(f"\n[{iteration:2d}] ScriptCompleted: success={success}")
                    break

                elif evt_type == "History":
                    if any(kw in text.lower() for kw in ["added", "polysurface", "created"]):
                        print(f"[{iteration:2d}] History: {text}")

            except asyncio.TimeoutError:
                if sent_count >= 4:
                    print(f"[{iteration:2d}] All inputs sent, waiting for completion...")
                    await asyncio.sleep(2.0)
                    break

        # Final check
        await asyncio.sleep(2.0)
        doc_after = send_tcp("get_document_info", {})
        obj_after = doc_after.get("result", {}).get("total_objects", 0)
        new_objects = obj_after - obj_before

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Inputs sent: {sent_count}/4")
        print(f"Objects before: {obj_before}")
        print(f"Objects after:  {obj_after}")
        print(f"New objects:    {new_objects}")

        if new_objects > 0:
            print("\n[SUCCESS] Door created!")
        else:
            print("\n[WARNING] No new objects created")

        return new_objects > 0


if __name__ == "__main__":
    print("This is an example script.")
    print("It demonstrates the pattern for automating Grasshopper scripts.")
    print("See: docs/learnings/grasshopper-automation.md for more details.\n")
    
    # Uncomment to run:
    # asyncio.run(create_door_example())
