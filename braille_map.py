# braille_map.py
# Full 5-bit Braille encoding for English + Tamil
# Each character maps to a 5-element list of 0/1 values
# representing 5 finger actuators (pins mapped to Braille dots 1,2,4,5,6)
#
# Day 2 — BarileAir project

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

import config

# ---------------------------------------------------------------------------
# Timing defaults (milliseconds)
# ---------------------------------------------------------------------------
DEFAULT_ON_MS = config.VIBRATE_ON_MS    # how long pins stay raised per character
DEFAULT_OFF_MS = config.VIBRATE_OFF_MS   # gap between characters
SPACE_GAP_MS = config.WORD_GAP_MS     # extended gap for space character

# ---------------------------------------------------------------------------
# 1. English a–z Braille dict
#    5-bit arrays: [finger1, finger2, finger3, finger4, finger5]
#    Dots 1,2,4,5,6 mapped to 5 fingers (dot 3 omitted for 5-actuator device)
#    a–j: first decade      k–t: second decade (add finger 3)
#    u–z: remaining patterns
# ---------------------------------------------------------------------------
ENGLISH_BRAILLE: Dict[str, List[int]] = {
    'a': [1, 0, 0, 0, 0],
    'b': [1, 1, 0, 0, 0],
    'c': [1, 0, 0, 1, 0],
    'd': [1, 0, 0, 1, 1],
    'e': [1, 0, 0, 0, 1],
    'f': [1, 1, 0, 1, 0],
    'g': [1, 1, 0, 1, 1],
    'h': [1, 1, 0, 0, 1],
    'i': [0, 1, 0, 1, 0],
    'j': [0, 1, 0, 1, 1],
    'k': [1, 0, 1, 0, 0],
    'l': [1, 1, 1, 0, 0],
    'm': [1, 0, 1, 1, 0],
    'n': [1, 0, 1, 1, 1],
    'o': [1, 0, 1, 0, 1],
    'p': [1, 1, 1, 1, 0],
    'q': [1, 1, 1, 1, 1],
    'r': [1, 1, 1, 0, 1],
    's': [0, 1, 1, 1, 0],
    't': [0, 1, 1, 1, 1],
    'u': [0, 0, 1, 0, 0],
    'v': [0, 0, 1, 1, 0],
    'w': [0, 1, 0, 0, 1],
    'x': [0, 0, 1, 1, 1],
    'y': [0, 0, 1, 0, 1],
    'z': [0, 0, 0, 1, 1],
}

# Capital marker — prefix before uppercase letters
CAPITAL_MARKER: List[int] = [0, 1, 0, 0, 0]

# Number indicator — prefix before digit sequences
NUMBER_MARKER: List[int] = [0, 0, 0, 0, 1]

# ---------------------------------------------------------------------------
# 2. Tamil vowels + consonants
#    Phonetic strategy: Tamil chars with phonetic similarity to English
#    letters share similar bit patterns where possible.
#    12 vowels + 10 common consonants = 22 characters
# ---------------------------------------------------------------------------
TAMIL_VOWELS: Dict[str, List[int]] = {
    'அ': [1, 0, 0, 0, 0],   # a
    'ஆ': [1, 0, 0, 0, 1],   # aa
    'இ': [0, 1, 0, 1, 0],   # i
    'ஈ': [0, 1, 0, 1, 1],   # ii
    'உ': [0, 0, 1, 0, 0],   # u
    'ஊ': [0, 0, 1, 0, 1],   # uu
    'எ': [1, 1, 0, 0, 0],   # e
    'ஏ': [1, 1, 0, 0, 1],   # ee
    'ஐ': [0, 1, 0, 0, 1],   # ai
    'ஒ': [1, 0, 1, 0, 1],   # o
    'ஓ': [1, 0, 1, 0, 0],   # oo
    'ஔ': [0, 1, 1, 0, 1],   # au
}

TAMIL_CONSONANTS: Dict[str, List[int]] = {
    # 10 most common Tamil consonants — each unique
    'க': [1, 0, 0, 1, 0],   # ka
    'ங': [1, 1, 0, 1, 1],   # nga
    'ச': [0, 0, 0, 1, 0],   # cha
    'ட': [1, 0, 0, 1, 1],   # ta (retroflex)
    'ண': [1, 0, 1, 1, 1],   # na (retroflex)
    'த': [0, 1, 1, 1, 1],   # tha
    'ந': [1, 0, 1, 1, 0],   # na
    'ப': [1, 1, 1, 1, 0],   # pa
    'ம': [1, 1, 1, 0, 0],   # ma
    'ய': [0, 0, 0, 1, 1],   # ya
}

# Combined Tamil map for lookup
TAMIL_BRAILLE: Dict[str, List[int]] = {**TAMIL_VOWELS, **TAMIL_CONSONANTS}

# Additional Tamil letters commonly produced by OCR/translation.
# We intentionally keep the Day 2 core maps unchanged for compatibility.
TAMIL_EXTENDED: Dict[str, List[int]] = {
    'ர': [1, 1, 1, 0, 1],
    'ல': [1, 1, 1, 0, 0],
    'ள': [0, 0, 1, 1, 0],
    'ழ': [0, 0, 1, 1, 1],
    'வ': [0, 0, 1, 1, 0],
    'ன': [1, 0, 1, 1, 0],
    'ற': [1, 1, 1, 0, 1],
    'ஞ': [1, 1, 0, 1, 1],
    'ஹ': [1, 1, 0, 0, 1],
    'ஜ': [0, 1, 0, 1, 1],
    'ஸ': [0, 1, 1, 1, 0],
    'ஷ': [1, 1, 0, 1, 0],
}

# Tamil combining vowel marks normalized to independent vowels for 5-dot output.
TAMIL_VOWEL_SIGNS_TO_VOWELS: Dict[str, str] = {
    'ா': 'ஆ',
    'ி': 'இ',
    'ீ': 'ஈ',
    'ு': 'உ',
    'ூ': 'ஊ',
    'ெ': 'எ',
    'ே': 'ஏ',
    'ை': 'ஐ',
    'ொ': 'ஒ',
    'ோ': 'ஓ',
    'ௌ': 'ஔ',
}

TAMIL_SKIP_SIGNS = {'்', 'ஃ', '\u200c', '\u200d'}

# ---------------------------------------------------------------------------
# 3. Punctuation, digits 0–9, space
# ---------------------------------------------------------------------------
PUNCTUATION: Dict[str, List[int]] = {
    ' ':  [0, 0, 0, 0, 0],  # space — uses 700ms gap in timing
    '.':  [0, 1, 1, 0, 0],
    ',':  [0, 1, 0, 0, 0],
    '?':  [0, 1, 1, 0, 1],
    '!':  [0, 1, 1, 1, 0],
    "'":  [0, 0, 0, 1, 0],
    '-':  [0, 0, 0, 1, 1],
    ':':  [0, 1, 1, 0, 0],
    ';':  [0, 1, 0, 0, 0],
    '(':  [1, 1, 1, 0, 1],
    ')':  [1, 1, 1, 0, 1],
    '"':  [0, 0, 1, 1, 0],
    '/':  [0, 0, 1, 1, 1],
}

# Digits reuse a–j patterns after NUMBER_MARKER prefix (standard Braille convention)
# 1→a, 2→b, 3→c, 4→d, 5→e, 6→f, 7→g, 8→h, 9→i, 0→j
DIGIT_MAP: Dict[str, List[int]] = {
    '1': ENGLISH_BRAILLE['a'],
    '2': ENGLISH_BRAILLE['b'],
    '3': ENGLISH_BRAILLE['c'],
    '4': ENGLISH_BRAILLE['d'],
    '5': ENGLISH_BRAILLE['e'],
    '6': ENGLISH_BRAILLE['f'],
    '7': ENGLISH_BRAILLE['g'],
    '8': ENGLISH_BRAILLE['h'],
    '9': ENGLISH_BRAILLE['i'],
    '0': ENGLISH_BRAILLE['j'],
}

# Master lookup combining English + punctuation (Tamil uses TAMIL_BRAILLE)
BRAILLE_MAP: Dict[str, List[int]] = {
    **ENGLISH_BRAILLE,
    **PUNCTUATION,
    **DIGIT_MAP,
}

# ---------------------------------------------------------------------------
# 5. encode_text() helper
#    Single entry point for EncodeAgent
#    Returns [{char, dots, on_ms, off_ms}] per character
# ---------------------------------------------------------------------------
def encode_text(text: str, lang: str = "en") -> List[Dict]:
    """
    Encode a text string into a list of Braille pin instructions.

    Each entry in the returned list is a dict:
        {
            'char':   the original character,
            'dots':   [int, int, int, int, int],  # 5 finger values (0 or 1)
            'on_ms':  int,   # how long pins stay raised
            'off_ms': int,   # gap before next character
        }

    Args:
        text: The input string to encode.
        lang: Language code — 'en' for English, 'ta' for Tamil.

    Returns:
        List of dicts with pin instructions for each character.
    """
    if lang == "ta":
        lookup = {
            **TAMIL_BRAILLE,
            **TAMIL_EXTENDED,
            **PUNCTUATION,
            **DIGIT_MAP,
        }
    else:
        lookup = BRAILLE_MAP
    result: List[Dict] = []
    in_number = False

    for ch in text:
        # --- Normalize Tamil combining signs to stable encodable symbols ---
        if lang == "ta":
            if ch in TAMIL_SKIP_SIGNS:
                continue
            if ch in TAMIL_VOWEL_SIGNS_TO_VOWELS:
                ch = TAMIL_VOWEL_SIGNS_TO_VOWELS[ch]

        # --- Space handling ---
        if ch == ' ':
            in_number = False
            result.append({
                'char': ' ',
                'dots': [0, 0, 0, 0, 0],
                'on_ms': 0,
                'off_ms': SPACE_GAP_MS,
            })
            continue

        # --- Digit handling (prefix with NUMBER_MARKER once) ---
        if ch.isdigit() and ch in DIGIT_MAP:
            if not in_number:
                result.append({
                    'char': '#',
                    'dots': list(NUMBER_MARKER),
                    'on_ms': DEFAULT_ON_MS,
                    'off_ms': DEFAULT_OFF_MS,
                })
                in_number = True
            result.append({
                'char': ch,
                'dots': list(DIGIT_MAP[ch]),
                'on_ms': DEFAULT_ON_MS,
                'off_ms': DEFAULT_OFF_MS,
            })
            continue

        in_number = False

        # --- Uppercase handling (prefix with CAPITAL_MARKER) ---
        if ch.isupper() and lang == "en":
            result.append({
                'char': '⇧',
                'dots': list(CAPITAL_MARKER),
                'on_ms': DEFAULT_ON_MS,
                'off_ms': DEFAULT_OFF_MS,
            })
            ch = ch.lower()

        # --- Lookup the character ---
        lower_ch = ch.lower() if lang == "en" else ch
        dots = lookup.get(lower_ch)

        if dots is not None:
            result.append({
                'char': ch,
                'dots': list(dots),
                'on_ms': DEFAULT_ON_MS,
                'off_ms': DEFAULT_OFF_MS,
            })
        else:
            logger.warning(f"Unknown char: {ch} (U+{ord(ch):04X})")
            result.append({
                'char': ch,
                'dots': [1, 0, 1, 0, 1],
                'on_ms': DEFAULT_ON_MS,
                'off_ms': DEFAULT_OFF_MS,
            })

    return result
