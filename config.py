# config.py
# Central configuration for BarileAir

# Tesseract OCR
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Windows path; adjust if needed
SUPPORTED_LANGS = ["eng", "tam"]

# BLE Device
BLE_ADDRESS = ""   # TODO: Set your Braille display's BLE MAC address
BLE_UUID    = ""   # TODO: Set GATT characteristic UUID

# Pipeline
DEFAULT_LANG = "eng"
