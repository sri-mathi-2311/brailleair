# agents/refine.py
# Day 11 — RefineAgent (LLM-based)
# Uses Gemini to fix OCR typos and perform high-quality translation

import logging
import warnings
import config

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEYS = {
    "",
    "YOUR_GEMINI_API_KEY_HERE",
    None,
}

def _llm_is_configured() -> bool:
    """Only enable the online refine step when it is explicitly configured."""
    return bool(
        config.USE_LLM
        and getattr(config, "GEMINI_API_KEY", None) not in _PLACEHOLDER_KEYS
    )

def _load_genai():
    """Import Gemini lazily so local offline runs do not warn or fail at import time."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import google.generativeai as genai
        return genai
    except Exception:
        return None

def run(state: dict) -> dict:
    """
    LLM RefineAgent:
    - Checks if USE_LLM is enabled.
    - If disabled (USE_LLM = False): skips and returns state as-is
    - If enabled: Sends raw OCR text to Gemini for typo correction ONLY
    - DOES NOT TRANSLATE - keeps original language
    - Updates state['final_text'].
    """
    if not _llm_is_configured():
        logger.info("[REFINE] LLM not configured. Skipping to local translate.")
        return state

    raw_text = state.get("raw_text", "").strip()
    if not raw_text:
        return state

    try:
        genai = _load_genai()
        if genai is None:
            logger.info("[REFINE] Gemini SDK unavailable. Skipping to local translate.")
            return state

        # Initialize Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = (
            f"You are part of an assistive project called BrailleAir. "
            f"Below is raw OCR text from a camera. It may contain noise or typos. "
            f"\n\n"
            f"CRITICAL INSTRUCTIONS:\n"
            f"1. FIX ONLY SPELLING ERRORS IN THE ORIGINAL LANGUAGE\n"
            f"2. NEVER TRANSLATE - Keep English as English, Keep Tamil as Tamil\n"
            f"3. Return ONLY the corrected text with no explanation\n"
            f"\n"
            f"Examples:\n"
            f"- Input: 'The quikc brown fox' → Output: 'The quick brown fox' (fix typo, NO translation)\n"
            f"- Input: 'வணக்கம் உலகா' → Output: 'வணக்கம் உலகம்' (fix typo, NO translation to English)\n"
            f"\n"
            f"Input Text: {raw_text}"
        )

        print("[REFINE] Sending to Gemini for Smart Refinement...")
        response = model.generate_content(prompt)
        
        if response and response.text:
            corrected = response.text.strip()
            state["final_text"] = corrected
            
            # Detect language of corrected text
            from langdetect import detect
            try:
                lang_code = detect(corrected)
                state["lang"] = "ta" if lang_code in ("ta", "tam") else "en"
            except:
                state["lang"] = "en"

            print(f"[REFINE] LLM Result: {corrected[:50]}...")
            logger.info("[REFINE] LLM successful.")
            
            # Set a flag to skip local translation
            state["llm_processed"] = True
        else:
            logger.warning("[REFINE] LLM returned empty response.")

    except Exception as e:
        print(f"[REFINE] AI Error or No Internet: {e}")
        logger.error(f"[REFINE] Error: {e}")
        # If LLM fails, we fall back to offline automatically if state['final_text'] stays empty
    
    return state
