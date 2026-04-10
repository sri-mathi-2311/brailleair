# ble_client.py
# Handles Bluetooth Low Energy communication with the Braille display device
# Day 9 — Terminal Sim Mode added

import asyncio
import time
from bleak import BleakClient

# ---------------------------------------------------------------------------
# Day 9: SIM MODE (Terminal Print)
# ---------------------------------------------------------------------------
def send_pattern(dots: list, on_ms: int, off_ms: int):
    """
    Simulates sending a 5-bit pattern to the BLE device by printing
    it to the console and sleeping for the specified durations.
    """
    labels = ['D1', 'D2', 'D3', 'D4', 'D5']
    out = ' '.join(f'{l}:{"ON" if d else "off"}' for l, d in zip(labels, dots))
    print(f'[{out}] -> {on_ms}ms')
    
    # Simulate hardware timing
    if on_ms > 0:
        time.sleep(on_ms / 1000.0)
    if off_ms > 0:
        time.sleep(off_ms / 1000.0)

# ---------------------------------------------------------------------------
# Future: Real BLE Mode (Stubbed for now)
# ---------------------------------------------------------------------------
async def send_braille(address: str, uuid: str, data: str):
    """
    Connects to a BLE Braille device and writes encoded Braille data.
    """
    async with BleakClient(address) as client:
        await client.write_gatt_char(uuid, data.encode("utf-8"))
        print(f"[BLE] Sent {len(data)} chars to {address}")

def send(braille_text: str):
    from config import BLE_ADDRESS, BLE_UUID
    asyncio.run(send_braille(BLE_ADDRESS, BLE_UUID, braille_text))
