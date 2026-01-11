"""Check current Rhino prompt via WebSocket."""

import asyncio
import json

import websockets


async def check_prompt():
    print("Connecting to Rhino WebSocket...")
    
    try:
        async with websockets.connect("ws://127.0.0.1:2000") as ws:
            # Receive welcome message
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"Current Prompt: {data.get('current_prompt', '')}")
            
            # Get state
            await ws.send(json.dumps({"command": "get_state"}))
            state = await ws.recv()
            state_data = json.loads(state)
            print(f"State: {state_data.get('current_prompt', '')}")
            
            # Listen for a few seconds to see any events
            print("\nListening for 3 seconds...")
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    event = json.loads(msg)
                    print(f"  Event: {event.get('type')} - {event.get('text', event.get('current_prompt', ''))}")
            except asyncio.TimeoutError:
                print("Done listening.")
                
    except ConnectionRefusedError:
        print("[ERROR] Connection refused - is Rhino running with mcpstart?")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    asyncio.run(check_prompt())
