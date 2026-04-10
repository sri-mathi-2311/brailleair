# fallback_dict.py
# Offline fallback dictionary for English -> Tamil Translation

FALLBACK_DICT = {
    "hello": "வணக்கம்",
    "world": "உலகம்",
    "welcome": "நல்வரவு",
    "system": "அமைப்பு",
    "test": "சோதனை",
    "document": "ஆவணம்",
    "the": "",
    "quick": "விரைவான",
    "brown": "பழுப்பு",
    "fox": "நரி",
    "jumps": "குதிக்கிறது",
    "over": "மேல்",
    "lazy": "சோம்பேறி",
    "dog": "நாய்",
    "this": "இது",
    "is": "ஆகும்",
    "a": "ஒரு",
    "sample": "மாதிரி",
    "english": "ஆங்கிலம்",
    "text": "உரை",
    "for": "முயற்சிக்கு",
    "ocr": "ஓசிஆர்",
    "testing": "சோதனை",
    "tesseract": "டெஸராக்ட்",
    "optical": "ஒளியியல்",
    "character": "எழுத்து",
    "recognition": "அறிதல்",
    "system.": "அமைப்பு.",
    "document.": "ஆவணம்.",
    "testing.": "சோதனை.",
    "dog.": "நாய்.",
    "india": "இந்தியா",
    "diverse": "பல்வேறு",
    "country": "நாடு",
    "with": "உடன்",
    "many": "பல",
    "languages": "மொழிகள்",
    "widely": "பரவலாக",
    "spoken": "பேசப்படும்",
    "across": "குறுக்கே",
    "nation": "தேசம்",
    "technology": "தொழில்நுட்பம்"
}

def translate(text: str) -> str:
    """Fallback translation using a simple dictionary approach."""
    words = text.split()
    translated_words = []
    for w in words:
        # Keep punctuation but lower to match Dict
        key = w.lower().strip(".,!?;:\"'")
        t = FALLBACK_DICT.get(key, w) # fallback to original if not found
        translated_words.append(t)
    return " ".join(translated_words)
