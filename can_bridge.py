#!/usr/bin/env python3
"""
CAN Bridge - OCPP mesajlarını CAN frame'lerine dönüştürür
Büşra Gül - 180541037
"""

import can
from datetime import datetime

CAN_ID_BOOT = 0x100
CAN_ID_STATUS = 0x101
CAN_ID_START_TX = 0x102
CAN_ID_STOP_TX = 0x103
CAN_ID_HEARTBEAT = 0x104

LOG_FILE = "logs/can_logs.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

class CANBridge:
    
    def __init__(self, channel='vcan0'):
        try:
            self.bus = can.interface.Bus(channel=channel, bustype='socketcan')
            log(f"[CAN] Connected to {channel}")
        except Exception as e:
            log(f"[CAN] Connection failed, running in simulation mode")
            self.bus = None
    
    def send_can_message(self, arbitration_id, data, description=""):
        try:
            if self.bus:
                msg = can.Message(
                    arbitration_id=arbitration_id,
                    data=data,
                    is_extended_id=False
                )
                self.bus.send(msg)
                log(f"[CAN TX] ID: {hex(arbitration_id)}, Data: {[hex(b) for b in data]} - {description}")
            else:
                log(f"[CAN SIM] ID: {hex(arbitration_id)}, Data: {[hex(b) for b in data]} - {description}")
        except Exception as e:
            log(f"[CAN] Error: {e}")
    
    def send_boot_notification(self):
        data = [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.send_can_message(CAN_ID_BOOT, data, "Boot Notification")
    
    def send_status_notification(self, connector_id, status):
        status_map = {
            'Available': 0x01,
            'Preparing': 0x02,
            'Charging': 0x03,
            'Finishing': 0x04,
            'Unavailable': 0x05,
            'Faulted': 0xFF
        }
        status_code = status_map.get(status, 0x00)
        data = [connector_id, status_code, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.send_can_message(CAN_ID_STATUS, data, f"Status: {status}")
    
    def send_start_transaction(self, connector_id, id_tag):
        tag_hash = sum(ord(c) for c in id_tag) % 256
        data = [connector_id, 0x01, tag_hash, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.send_can_message(CAN_ID_START_TX, data, f"Start: {id_tag}")
    
    def send_stop_transaction(self, transaction_id):
        tx_bytes = transaction_id.to_bytes(4, byteorder='little')
        data = [0x00, tx_bytes[0], tx_bytes[1], tx_bytes[2], tx_bytes[3], 0x00, 0x00, 0x00]
        self.send_can_message(CAN_ID_STOP_TX, data, f"Stop: {transaction_id}")
    
    def send_heartbeat(self):
        data = [0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        self.send_can_message(CAN_ID_HEARTBEAT, data, "Heartbeat")
    
    def close(self):
        if self.bus:
            self.bus.shutdown()

if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    bridge = CANBridge()
    bridge.send_boot_notification()
    bridge.send_status_notification(1, 'Available')
    bridge.send_start_transaction(1, 'USER001')
    bridge.send_heartbeat()
    bridge.send_stop_transaction(12345)
    bridge.close()