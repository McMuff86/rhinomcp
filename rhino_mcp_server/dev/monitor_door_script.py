"""
Monitor all prompts when running Rahmentuer_UD5.gh to see what Rhino asks.
This will help us understand all the prompts we need to handle.
"""

import asyncio
import json
import os
import websockets
from datetime import datetime

# Relativer Pfad zur .gh Datei
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
GH_FILE = os.path.join(PROJECT_ROOT, "..", "Rahmentuer_UD5.gh")
GH_FILE = os.path.abspath(GH_FILE)


async def cancel_current_command(ws):
    """Cancel any current command."""
    print("\n[Cancel] Sending cancel command...")
    await ws.send(json.dumps({"command": "cancel"}))
    await asyncio.sleep(1.0)
    # Clear any pending messages
    try:
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
            event = json.loads(msg)
            if event.get("type") == "Prompt" and "command" in event.get("text", "").lower():
                print(f"[Cancel] Back at Command prompt: {event.get('text')}")
                break
    except asyncio.TimeoutError:
        pass


async def monitor_script_execution():
    """Run the script and monitor all prompts."""
    print("=" * 70)
    print("MONITORING RAHMENTUER_UD5.GH EXECUTION")
    print("=" * 70)
    print(f"GH File: {GH_FILE}")
    print("\nThis will run the script and show ALL prompts Rhino asks.")
    print("Press Ctrl+C to stop.\n")
    
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        # Read welcome message
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"[CONNECTED] Current prompt: {data.get('current_prompt')}\n")
        
        # Cancel any existing command first
        await cancel_current_command(ws)
        
        print("\n" + "-" * 70)
        print("STARTING GRASSHOPPER PLAYER")
        print("-" * 70)
        
        # Start GrasshopperPlayer
        await ws.send(json.dumps({
            "command": "run_script",
            "script": f'_-GrasshopperPlayer "{GH_FILE}"'
        }))
        
        prompts = []
        event_count = 0
        
        print("\nMonitoring all events...\n")
        
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                if evt_type == "Heartbeat":
                    continue  # Skip heartbeats
                
                event_count += 1
                
                if evt_type == "Prompt":
                    prompt_text = text.strip()
                    prompts.append({
                        "number": len(prompts) + 1,
                        "text": prompt_text,
                        "timestamp": ts
                    })
                    print(f"\n[{len(prompts)}] {ts} *** PROMPT ***")
                    print(f"    '{prompt_text}'")
                    print()
                    
                    # Check if we're back at Command prompt
                    if prompt_text.lower() == "command":
                        print("\n" + "=" * 70)
                        print("SCRIPT COMPLETED - BACK AT COMMAND PROMPT")
                        print("=" * 70)
                        break
                        
                elif evt_type == "ScriptCompleted":
                    success = event.get("success", False)
                    print(f"\n[{event_count}] {ts} ScriptCompleted: success={success}")
                    
                elif evt_type == "History":
                    print(f"[{event_count}] {ts} History: {text[:80]}")
                else:
                    print(f"[{event_count}] {ts} {evt_type}: {text[:80]}")
                    
            except asyncio.TimeoutError:
                print("(waiting for events...)")
            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                break
        
        # Summary
        print("\n" + "=" * 70)
        print("PROMPT SUMMARY")
        print("=" * 70)
        print(f"Total prompts captured: {len(prompts)}\n")
        
        for i, prompt in enumerate(prompts, 1):
            print(f"{i}. '{prompt['text']}'")
        
        print("\n" + "=" * 70)
        print("Use these prompts to update the create_7_doors.py script!")
        print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(monitor_script_execution())
    except KeyboardInterrupt:
        print("\n\nStopped.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
