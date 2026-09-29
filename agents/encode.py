# agents/encode.py
# Day 8 — EncodeAgent: Text to Vibration Sequence
# Translates final_text character-by-character into 5-bit Braille pinning commands

import logging
import sys
import os

# Ensure braille_map can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from braille_map import encode_text

logger = logging.getLogger(__name__)

def _safe_preview(text: str) -> str:
    """Return a console-safe preview for Windows terminals."""
    try:
        text.encode(sys.stdout.encoding or "utf-8")
        return text
    except Exception:
        return text.encode("ascii", errors="replace").decode("ascii")

def run(state: dict) -> dict:
    """
    EncodeAgent entry point.
    Converts state['final_text'] into a list of vibration pin commands.
    
    Args:
        state: BrailleState dict containing final_text and lang.
        
    Returns:
        Updated state with vibration_seq set to a list of dicts.
    """
    final_text = state.get("final_text", "")
    
    # We map 'tamil'/'eng' to 'ta'/'en' for encode_text
    lang_val = state.get("lang", "en").lower()
    if lang_val in ("tamil", "ta"):
        lang_code = "ta"
    else:
        lang_code = "en"

    if not final_text:
        state["vibration_seq"] = []
        return state

    print(f"[ENCODE] Encoding text ({lang_code}): {_safe_preview(final_text[:50])}...")
    
    # encode_text handles spaces (700ms gap) and unknown chars ([1,0,1,0,1] double buzz)
    seq = encode_text(final_text, lang=lang_code)
    
    state["vibration_seq"] = seq
    print(f"[ENCODE] Generated {len(seq)} vibration commands.")
    
    return state
