# BrailleAir

A comprehensive pipeline that converts OCR text from physical documents (English and Tamil) into active 5-bit vibration signals for BLE-enabled tactile hardware. 

## Problem
Visually impaired individuals face significant accessibility barriers when navigating printed materials in environments lacking Braille alternatives or auditory reading assistance. Real-time, localized translations of texts like labels, documents, and signs are difficult to parse independently.

## Solution
BrailleAir bridges this gap using CV-powered optical character recognition (OCR) and lightweight natural language translation. A mounted camera parses text, translates English to Tamil (or natively processes Tamil), and encodes the characters directly into 5-actuator Braille signals. These signals are mapped and transmitted over Bluetooth Low Energy (BLE) to a custom wearable device that pulses the user's fingers corresponding to Braille dot patterns.

## Architecture
*(Placeholder for Architecture Diagram)*

The system leverages a linear state-driven graph powered by LangGraph, operating through 5 specialized agents:
1. **CaptureAgent:** Intakes images via physical files, webcams, or BLE-streamed hardware cameras.
2. **PreprocessAgent:** Clears noise, resizes to 300DPI, and thresholds image using strictly defined CV2 logic.
3. **OCRAgent:** Utilizes Tesseract (`eng+tam`), executing automatic structural retries (`--psm 6`, `--psm 3`) and confidence-pruning.
4. **TranslateAgent:** Rapid translation routing for English characters via `googletrans` using offline caching fallbacks.
5. **EncodeAgent:** Compiles character strings down to `[1, 0, 0, 0, 0]` pin instructions tracking variable actuation timings and character gap durations.
6. **VibrateAgent:** Offloads commands via GATT properties onto the BLE Client module to trigger tactile feedback.

## Bill of Materials
- Camera Module (Webcam or BLE integrated)
- 5 x Miniature Linear Actuators / Vibration Motors
- Generic ESP32 or BLE Microcontroller
- 3D Printed Hand-mount housing

## Setup and Run
These commands assume Windows PowerShell and Python 3.12 or newer.

### 1. Set up Python
```powershell
cd D:\barileair
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn requests pydantic bleak langdetect langgraph pillow pytesseract opencv-python numpy typing-extensions pytest googletrans==4.0.0-rc1 pypdf python-docx
```

Install Tesseract OCR and confirm `TESSERACT_CMD` in `config.py` points to the installed executable. The default path is `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 2. Start the backend API
In a terminal with the virtual environment activated:
```powershell
cd D:\barileair
python web_api.py
```

The API runs at `http://localhost:8000`.

### 3. Start the frontend dashboard
Open a second terminal:
```powershell
cd D:\barileair\frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal, normally `http://localhost:5173`.

### 4. Run the CLI pipeline
```powershell
cd D:\barileair
.\.venv\Scripts\Activate.ps1
python main.py --mode FILE --image test_images/test_english_1.png
```

### 5. Run tests
```powershell
cd D:\barileair
.\.venv\Scripts\Activate.ps1
python -m pytest
```

The runtime settings, including `OCR_CONF_THRESHOLD` and `MAX_RETRY`, are defined in `config.py`.

## Benchmark
- **Test Set:** 5 mixed configuration images (English literal, Tamil native, Mixed formats). *(Target scale: 30 images)*
- **Engine Output Validation:** >80% accuracy minimum per word sequence matrix matching.
- **Latency constraint:** Sub-3s processing loop runtime execution (Excludes physical actuation cycle delays).
