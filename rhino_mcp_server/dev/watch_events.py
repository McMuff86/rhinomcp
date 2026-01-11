"""
Watch all WebSocket events in real-time.
Run this while manually creating a door in Rhino.
"""

import asyncio
import json
from datetime import datetime
import websockets


async def main():
    print("=" * 70)
    print("WEBSOCKET EVENT WATCHER")
    print("=" * 70)
    print("Connecting to ws://127.0.0.1:2000...")
    print("Now manually run GrasshopperPlayer in Rhino and create a door.")
    print("Press Ctrl+C to stop.\n")
    
    async with websockets.connect("ws://127.0.0.1:2000") as ws:
        welcome = await ws.recv()
        data = json.loads(welcome)
        print(f"[CONNECTED] Current prompt: {data.get('current_prompt')}\n")
        print("-" * 70)
        
        count = 0
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60.0)
                event = json.loads(msg)
                evt_type = event.get("type")
                text = event.get("text", "")
                ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                if evt_type == "Heartbeat":
                    continue  # Skip heartbeats
                
                count += 1
                
                if evt_type == "Prompt":
                    print(f"\n[{count}] {ts} *** PROMPT ***")
                    print(f"    '{text}'")
                    print()
                elif evt_type == "History":
                    print(f"[{count}] {ts} History: {text}")
                else:
                    print(f"[{count}] {ts} {evt_type}: {text[:100]}")
                    
            except asyncio.TimeoutError:
                print("(waiting for events...)")
            except KeyboardInterrupt:
                print("\nStopped.")
                break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
