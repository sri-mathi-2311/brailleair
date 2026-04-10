# agents/translate.py
# Day 7 — TranslateAgent: Language detection + Translation + Offline Fallback

import logging
from langdetect import detect
import sys
import os

# Ensure fallback_dict and config can be imported when running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import fallback_dict

try:
    from googletrans import Translator
    HAS_GOOGLETRANS = True
except Exception as e:
    HAS_GOOGLETRANS = False
    print(f"[TRANSLATE-INIT] Warning: googletrans unavailable ({e})")

logger = logging.getLogger(__name__)

def run(state: dict) -> dict:
    """
    TranslateAgent entry point.
    Detects language -> if English, translates to Tamil -> if Tamil, skips translation.
    Args:
        state: BrailleState dict containing raw_text.
    Returns:
        Updated state with final_text translated to Tamil.
    """
    raw_text = state.get("raw_text", "")
    
    if not raw_text.strip():
        state["final_text"] = ""
        state["lang"] = ""
        return state

    # 1. Language detection
    try:
        lang_code = detect(raw_text)
    except Exception as e:
        logger.warning(f"[TRANSLATE] langdetect failed: {e}")
        lang_code = "en" # default to english if detection fails

    if lang_code == "ta":
        state["lang"] = "tamil"
        state["final_text"] = raw_text
        print("[TRANSLATE] Detected Tamil -> Skipping translation")
        return state

    state["lang"] = "english"
    print(f"[TRANSLATE] Detected {lang_code.upper()} -> Translating to Tamil...")

    # 2. Translation with offline fallback
    translated_text = ""
    success = False
    
    if HAS_GOOGLETRANS:
        try:
            translator = Translator()
            result = translator.translate(raw_text, dest='ta')
            translated_text = result.text
            success = True
            print("[TRANSLATE] Online translation successful.")
        except Exception as e:
            logger.warning(f"[TRANSLATE] Online translation failed: {e}")
            success = False
    
    if not success:
        # Fallback offline dictionary
        print("[TRANSLATE] Using offline fallback dictionary.")
        translated_text = fallback_dict.translate(raw_text)

    # 3. Output
    state["final_text"] = translated_text
    print(f"[TRANSLATE] Final Tamil: {translated_text}")

    return state

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("\n=== TranslateAgent Standalone Test ===\n")
    
    # English test
    state_en = {
        "raw_text": "The quick brown fox jumps over the lazy dog",
        "retry_count": 0,
        "error": ""
    }
    print("--- Input: English ---")
    res_en = run(state_en)
    print(f"Result: {res_en['final_text']}\n")

    # Tamil test
    state_ta = {
        "raw_text": "வணக்கம் உலகம்",
        "retry_count": 0,
        "error": ""
    }
    print("--- Input: Tamil ---")
    res_ta = run(state_ta)
    print(f"Result: {res_ta['final_text']}\n")
