# ble_client.py
# Handles Bluetooth Low Energy communication with the Braille display device

import asyncio
from bleak import BleakClient

DEVICE_ADDRESS = ""  # Set target BLE device MAC address in config.py
CHARACTERISTIC_UUID = ""  # Set characteristic UUID in config.py


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
