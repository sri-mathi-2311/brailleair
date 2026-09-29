# config.py
# Central configuration for BarileAir

# Tesseract OCR
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SUPPORTED_LANGS = ["eng", "tam"]

# Config Settings
OCR_CONF_THRESHOLD = 60
VIBRATE_ON_MS = 500
VIBRATE_OFF_MS = 200
WORD_GAP_MS = 700
MAX_RETRY = 2
CAMERA_MODE = 'FILE' # FILE | WEBCAM | BLE

# Pipeline Settings
DEFAULT_LANG = "eng"
USE_LLM = False         # Disable LLM - no translation, direct Braille encoding
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # Replace with your actual key

# BLE Device
BLE_ADDRESS = ""   # TODO: Set your Braille display's BLE MAC address
BLE_UUID    = ""   # TODO: Set GATT characteristic UUID

# ESP32 Camera
ESP32_CAMERA_URL = "http://192.168.1.100/capture" # Default placeholder

# Pipeline
DEFAULT_LANG = "eng"
