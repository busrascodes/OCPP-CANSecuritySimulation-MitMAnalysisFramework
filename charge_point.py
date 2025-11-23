#!/usr/bin/env python3
"""
Charge Point - Şarj istasyonu simülasyonu
Büşra Gül - 180541037
"""

import asyncio
import websockets
from datetime import datetime
from ocpp.v16 import ChargePoint as cp
from ocpp.v16 import call
from ocpp.v16.enums import ChargePointStatus
from can_bridge import CANBridge
import os

LOG_FILE = "logs/ocpp_logs.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

class ChargePoint(cp):
    
    def __init__(self, charge_point_id, connection, can_bridge):
        super().__init__(charge_point_id, connection)
        self.can_bridge = can_bridge
    
    async def send_boot_notification(self):
        log(f"[CP] Sending BootNotification")
        request = call.BootNotificationPayload(
            charge_point_model="VirtualCP-v1",
            charge_point_vendor="SimVendor"
        )
        response = await self.call(request)
        self.can_bridge.send_boot_notification()
        return response
    
    async def send_heartbeat(self):
        request = call.HeartbeatPayload()
        response = await self.call(request)
        log(f"[CP] Heartbeat sent")
        return response
    
    async def send_status_notification(self, connector_id, status):
        log(f"[CP] Status: {status}")
        request = call.StatusNotificationPayload(
            connector_id=connector_id,
            error_code="NoError",
            status=status
        )
        response = await self.call(request)
        self.can_bridge.send_status_notification(connector_id, status)
        return response
    
    async def start_transaction(self, connector_id, id_tag):
        log(f"[CP] Starting transaction for {id_tag}")
        request = call.StartTransactionPayload(
            connector_id=connector_id,
            id_tag=id_tag,
            meter_start=0,
            timestamp=datetime.utcnow().isoformat()
        )
        response = await self.call(request)
        self.can_bridge.send_start_transaction(connector_id, id_tag)
        return response
    
    async def stop_transaction(self, transaction_id, meter_stop):
        log(f"[CP] Stopping transaction {transaction_id}")
        request = call.StopTransactionPayload(
            meter_stop=meter_stop,
            timestamp=datetime.utcnow().isoformat(),
            transaction_id=transaction_id
        )
        response = await self.call(request)
        self.can_bridge.send_stop_transaction(transaction_id)
        return response

async def main():
    os.makedirs("logs", exist_ok=True)
    charge_point_id = "CP001"
    can_bridge = CANBridge()
    
    log(f"[CP] Connecting to CSMS...")
    
    async with websockets.connect(
        'ws://localhost:9000/CP001',
        subprotocols=['ocpp1.6']
    ) as ws:
        
        cp_instance = ChargePoint(charge_point_id, ws, can_bridge)
        
        await cp_instance.send_boot_notification()
        await asyncio.sleep(2)
        
        await cp_instance.send_status_notification(1, ChargePointStatus.available)
        await asyncio.sleep(2)
        
        transaction = await cp_instance.start_transaction(1, "USER001")
        await asyncio.sleep(5)
        
        await cp_instance.send_heartbeat()
        await asyncio.sleep(2)
        
        await cp_instance.stop_transaction(transaction.transaction_id, 1500)
        await asyncio.sleep(2)
        
        await cp_instance.send_status_notification(1, ChargePointStatus.available)
        
        log(f"[CP] All operations completed")

if __name__ == '__main__':
    asyncio.run(main())