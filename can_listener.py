#!/usr/bin/env python3
"""
CAN Listener - CAN bus mesajlarını dinler
Büşra Gül - 180541037
"""

import can
from datetime import datetime
import sys
import os

LOG_FILE = "logs/can_logs.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(log_entry.strip())
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

def decode_message(msg):
    aid = msg.arbitration_id
    data = msg.data
    
    if aid == 0x100:
        return "BOOT NOTIFICATION"
    elif aid == 0x101:
        connector = data[0]
        status_map = {0x01: 'Available', 0x02: 'Preparing', 0x03: 'Charging', 
                     0x04: 'Finishing', 0x05: 'Unavailable', 0xFF: 'Faulted'}
        status = status_map.get(data[1], 'Unknown')
        return f"STATUS - Connector {connector}: {status}"
    elif aid == 0x102:
        connector = data[0]
        user_hash = data[2]
        return f"START TRANSACTION - Connector {connector}, User: {user_hash}"
    elif aid == 0x103:
        tx_id = int.from_bytes(data[1:5], byteorder='little')
        return f"STOP TRANSACTION - ID: {tx_id}"
    elif aid == 0x104:
        return "HEARTBEAT"
    else:
        return "UNKNOWN"

def main():
    os.makedirs("logs", exist_ok=True)
    channel = 'vcan0'
    
    log(f"[CAN Listener] Starting on {channel}")
    
    try:
        bus = can.interface.Bus(channel=channel, bustype='socketcan')
        log(f"[CAN Listener] Connected, waiting for messages...")
        
        count = 0
        while True:
            msg = bus.recv(timeout=1.0)
            if msg:
                count += 1
                decoded = decode_message(msg)
                data_hex = [f"{b:02X}" for b in msg.data]
                log(f"[CAN RX #{count}] ID: {hex(msg.arbitration_id)} | Data: [{', '.join(data_hex)}]")
                log(f"  → {decoded}")
    
    except KeyboardInterrupt:
        log(f"[CAN Listener] Stopped. Total messages: {count}")
    except Exception as e:
        log(f"[CAN Listener] Error: {e}")

if __name__ == '__main__':
    main()