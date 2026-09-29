#!/usr/bin/env python3
"""Quick test to verify pipeline does NOT translate."""

from pipeline import run_pipeline

print("\n" + "="*60)
print("Testing pipeline with English image")
print("="*60 + "\n")

state = run_pipeline('test_images/test_english_1.png')

print("\n" + "="*60)
print("RESULTS:")
print("="*60)
print(f"Raw text:   {state.get('raw_text', '')[:80]}")
print(f"Final text: {state.get('final_text', '')[:80]}")
print(f"Language:   {state.get('lang', '')}")
print(f"Are they identical? {state.get('raw_text', '') == state.get('final_text', '')}")
print("="*60 + "\n")

if state.get('raw_text') != state.get('final_text'):
    print("⚠️  WARNING: Raw text and final text are DIFFERENT!")
    print("   This means translation is happening!")
    print(f"   Raw:   {repr(state.get('raw_text', '')[:50])}")
    print(f"   Final: {repr(state.get('final_text', '')[:50])}")
else:
    print("✓ PASS: Raw text and final text are identical - NO translation!")
