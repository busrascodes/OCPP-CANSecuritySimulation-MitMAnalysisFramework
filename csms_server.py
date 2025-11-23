#!/usr/bin/env python3
"""
CSMS Sunucusu - Şarj istasyonlarını yöneten merkezi sunucu
Büşra Gül - 180541037
"""

import asyncio
import websockets
from datetime import datetime
from ocpp.routing import on
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call_result
from ocpp.v16.enums import RegistrationStatus
import os

LOG_FILE = "logs/ocpp_logs.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

class ChargePoint(cp):
    
    @on('BootNotification')
    async def on_boot_notification(self, charge_point_vendor, charge_point_model, **kwargs):
        log(f"[CSMS] BootNotification from {self.id} - {charge_point_vendor} {charge_point_model}")
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=300,
            status=RegistrationStatus.accepted
        )
    
    @on('Heartbeat')
    async def on_heartbeat(self):
        log(f"[CSMS] Heartbeat from {self.id}")
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat()
        )
    
    @on('StatusNotification')
    async def on_status_notification(self, connector_id, error_code, status, **kwargs):
        log(f"[CSMS] Status: Connector {connector_id} -> {status}")
        return call_result.StatusNotificationPayload()
    
    @on('StartTransaction')
    async def on_start_transaction(self, connector_id, id_tag, meter_start, timestamp, **kwargs):
        log(f"[CSMS] StartTransaction: {id_tag} on connector {connector_id}")
        return call_result.StartTransactionPayload(
            transaction_id=12345,
            id_tag_info={'status': 'Accepted'}
        )
    
    @on('StopTransaction')
    async def on_stop_transaction(self, meter_stop, timestamp, transaction_id, **kwargs):
        log(f"[CSMS] StopTransaction: {transaction_id}")
        return call_result.StopTransactionPayload(
            id_tag_info={'status': 'Accepted'}
        )

async def on_connect(websocket, path):
    try:
        requested_protocols = websocket.request_headers.get('Sec-WebSocket-Protocol', '')
        if not requested_protocols:
            return await websocket.close()
        
        charge_point_id = path.strip('/')
        log(f"[CSMS] Connected: {charge_point_id}")
        
        cp_instance = ChargePoint(charge_point_id, websocket)
        await cp_instance.start()
        
    except Exception as e:
        log(f"[CSMS] Error: {e}")

async def main():
    os.makedirs("logs", exist_ok=True)
    log("[CSMS] Starting server on ws://localhost:9000")
    
    server = await websockets.serve(
        on_connect,
        '0.0.0.0',
        9000,
        subprotocols=['ocpp1.6']
    )
    
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())