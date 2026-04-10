# agents/vibrate.py
# Day 9 — VibrateAgent (Terminal Sim)
# Iterates through the vibration sequence and sends pattern to ble_client

import logging
import sys
import os

# Ensure ble_client can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import ble_client

logger = logging.getLogger(__name__)

def run(state: dict) -> dict:
    """
    VibrateAgent terminal simulation loop.
    Extracts the sequence from state and invokes ble_client sequentially.
    """
    seq = state.get("vibration_seq", [])
    
    if not seq:
        print("[VIBRATE] No vibration sequence found to send.")
        return state

    print(f"\n[VIBRATE] Starting terminal simulation for {len(seq)} commands...\n")
    
    for item in seq:
        dots = item.get("dots", [0, 0, 0, 0, 0])
        on_ms = item.get("on_ms", 0)
        off_ms = item.get("off_ms", 0)
        char = item.get("char", "")
        
        # Log character intent
        print(f"Char: '{char}' ", end="")
        
        # Delegate to ble_client sim
        ble_client.send_pattern(dots, on_ms, off_ms)
        
    print("\n[VIBRATE] Simulation complete.\n")
    return state
