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
    TRANSLATE_INIT_ERROR = ""
except Exception as e:
    HAS_GOOGLETRANS = False
    TRANSLATE_INIT_ERROR = str(e)

logger = logging.getLogger(__name__)

def _safe_preview(text: str) -> str:
    """Return a console-safe version of text for Windows cp1252 terminals."""
    try:
        text.encode(sys.stdout.encoding or "utf-8")
        return text
    except Exception:
        return text.encode("ascii", errors="replace").decode("ascii")

def run(state: dict) -> dict:
    """
    TranslateAgent entry point.
    Language Detection ONLY - NO TRANSLATION.
    
    For English: Keep as English, convert to Braille
    For Tamil: Keep as Tamil, convert to Braille
    
    Args:
        state: BrailleState dict containing raw_text.
    Returns:
        Updated state with lang and final_text set (NO translation).
    """
    if state.get("llm_processed"):
        logger.info("[TRANSLATE] LLM already processed. Skipping local logic.")
        return state

    raw_text = state.get("raw_text", "")
    
    if not raw_text.strip():
        state["final_text"] = ""
        state["lang"] = ""
        return state

    # 1. Language detection ONLY - DO NOT TRANSLATE
    try:
        lang_code = detect(raw_text)
    except Exception as e:
        logger.warning(f"[TRANSLATE] langdetect failed: {e}")
        lang_code = "en" # default to english if detection fails

    # Set language and keep original text - NO TRANSLATION
    if lang_code in ("ta", "tam"):
        state["lang"] = "ta"
        print("[TRANSLATE] Detected Tamil -> Keep as Tamil (NO translation)")
    else:
        state["lang"] = "en"
        print(f"[TRANSLATE] Detected {lang_code.upper()} -> Keep as {lang_code.upper()} (NO translation)")
    
    # Keep original text - DO NOT TRANSLATE
    state["final_text"] = raw_text
    
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
