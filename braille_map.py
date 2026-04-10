# braille_map.py
# Braille character mappings for English and Tamil

ENGLISH_BRAILLE: dict[str, str] = {
    # Grade-1 English Braille (Unicode Braille patterns)
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵',
}

TAMIL_BRAILLE: dict[str, str] = {
    # Placeholder — Tamil Braille mappings to be added
}


def text_to_braille(text: str, lang: str = "en") -> str:
    mapping = ENGLISH_BRAILLE if lang == "en" else TAMIL_BRAILLE
    return "".join(mapping.get(ch.lower(), ch) for ch in text)
