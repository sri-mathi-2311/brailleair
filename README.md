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

## Setup
1. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Tesseract Configuration:**
   Install Tesseract OCR and confirm `TESSERACT_CMD` located in `config.py`.
3. **Environment Limits:**
   Configure limits (`OCR_CONF_THRESHOLD`: 60, `MAX_RETRY`: 2) within `config.py`.

## Usage
Run the main pipeline loop via CLI to perform an end-to-end translation.

```bash
python main.py --mode FILE --image test_images/test_english_1.png
```

## Benchmark
- **Test Set:** 5 mixed configuration images (English literal, Tamil native, Mixed formats). *(Target scale: 30 images)*
- **Engine Output Validation:** >80% accuracy minimum per word sequence matrix matching.
- **Latency constraint:** Sub-3s processing loop runtime execution (Excludes physical actuation cycle delays).
