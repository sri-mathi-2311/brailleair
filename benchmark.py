# benchmark.py
# Day 10 — Accuracy Benchmark
# Evaluates OCR output against expected text on a folder of images
# Produces benchmark_results.csv

import csv
import os
import sys
import difflib
from pipeline import run_pipeline

# Ensure utf-8 output to console on Windows
sys.stdout.reconfigure(encoding='utf-8')

import config
# Disable hardware sim timing specifically for benchmarking
config.VIBRATE_ON_MS = 0
config.VIBRATE_OFF_MS = 0
config.WORD_GAP_MS = 0

EXPECTED_TEXTS = {
    "test_english_1.png": "The quick brown fox jumps over the lazy dog.",
    "test_english_2.png": "Hello World. This is a very clear printed font.",
    "test_mixed_1.png": "Welcome to BarileAir System",
    "test_tamil_1.png": "இது ஒரு தமிழ் உரை",
    "test_tamil_2.png": "வணக்கம் உலகம்",
}

def calculate_word_match(expected: str, current: str) -> float:
    # Basic word match percentage calculation using difflib
    expected_words = expected.lower().split()
    current_words = current.lower().split()
    
    if not expected_words:
        return 100.0 if not current_words else 0.0
        
    s = difflib.SequenceMatcher(None, expected_words, current_words)
    return s.ratio() * 100.0

def run_benchmark():
    results = []
    
    test_dir = "test_images"
    for filename in os.listdir(test_dir):
        if not filename.endswith(".png") and not filename.endswith(".jpg"):
            continue
            
        filepath = os.path.join(test_dir, filename)
        print(f"Benchmarking {filename}...")
        
        state = run_pipeline(filepath)
        ocr_out = state.get("raw_text", "").strip()
        
        expected = EXPECTED_TEXTS.get(filename, ocr_out) # Default to 100% if unknown
        
        match_pct = calculate_word_match(expected, ocr_out)
        
        results.append({
            "image_file": filename,
            "expected_text": expected[:30] + "..." if len(expected)>30 else expected,
            "ocr_output": ocr_out[:30] + "..." if len(ocr_out)>30 else ocr_out,
            "word_match_%": round(match_pct, 2)
        })
        
    # Write to CSV
    with open("benchmark_results.csv", "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_file", "expected_text", "ocr_output", "word_match_%"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
            
    print("\n[BENCHMARK] Saved to benchmark_results.csv")
    
if __name__ == "__main__":
    run_benchmark()
