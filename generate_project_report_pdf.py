from pathlib import Path
import textwrap


OUTPUT = Path("BrailleAir_Project_Report.pdf")


REPORT_TEXT = """
BrailleAir Project Report

Project name: BrailleAir
Report date: 11 April 2026
Report style: Simple English

1. Project Summary
BrailleAir is an assistive technology project. It takes an image of printed text,
reads the text with OCR, changes the text into Tamil, converts the result into a
Braille-like 5-bit vibration pattern, and then sends or simulates vibration commands
for a tactile device. The project also includes a web API and a React frontend.

2. What The Project Uses
- Python backend
- LangGraph state pipeline
- OpenCV for image preprocessing
- Tesseract OCR for English and Tamil text reading
- Langdetect for language detection
- googletrans for online translation when available
- Local fallback dictionary for offline translation
- Gemini LLM integration through google.generativeai
- Bleak for Bluetooth Low Energy support
- FastAPI backend
- React, Vite, Axios, Framer Motion, and Lucide React frontend
- Pytest for tests

3. Main Working Flow
Step 1: Capture image from file, webcam, or planned BLE source.
Step 2: Preprocess image with grayscale, denoise, deskew, threshold, and resize.
Step 3: OCR reads the text.
Step 4: Retry OCR if the first result is empty.
Step 5: Optional LLM refine step with Gemini.
Step 6: Local translation path if LLM is skipped or fails.
Step 7: Encode final text into a vibration sequence.
Step 8: Simulate or send vibration commands to hardware.

4. What Result The Project Gives
The expected result is:
image text -> Tamil text -> vibration sequence for a tactile device.

In local verification on a sample English image, the pipeline:
- read the text successfully,
- produced translated output through the offline fallback path,
- generated 153 vibration commands,
- ran the vibration sequence in terminal simulation mode.

So the main project idea works as a prototype.

5. Does It Work Offline?
Answer: Partly yes.
- OCR and preprocessing can work offline if Tesseract is installed.
- The local fallback dictionary gives a basic offline translation path.
- The vibration simulator works offline.
- BLE capture is not finished yet.
- Real BLE sending code exists, but the main pipeline currently uses simulation.

Offline conclusion:
The core demo works offline in a limited way, but full hardware support is not complete.

6. Does It Work Online?
Answer: Partly yes.
- A FastAPI backend exists.
- API routes such as / and /upload-book are present.
- A React frontend dashboard exists.
- But the frontend build failed locally because of a Vite/SWC process error.
- The online translation library is also not healthy in the current setup.

Online conclusion:
The online architecture exists, but it is not fully stable in the current environment.

7. Is LLM Integrated?
Answer: Yes.
- The file agents/refine.py integrates Gemini through google.generativeai.
- config.py has USE_LLM = True.
- The LLM step is placed before the normal translation step.
- It is meant to fix OCR mistakes and translate to Tamil.

Current LLM status:
- The key in config.py is only a placeholder.
- The Gemini package used here is deprecated.
- In testing, the LLM step timed out and did not complete successfully.

LLM conclusion:
LLM integration exists in code, but it is not working correctly in the current setup.

8. Important Problems Found
- After local translation, the language state stays as english, so Tamil text is encoded
  through the English path. This causes many Tamil characters to fall back to a default buzz
  pattern instead of using proper Tamil mapping.
- The Gemini key is not configured for real use.
- googletrans fails because of a compatibility problem with httpcore.
- BLE capture mode is still a stub.
- The frontend did not build successfully in this local environment.
- Windows console output can fail on Tamil text unless UTF-8 output is enabled.

9. Verification Results
- Tesseract executable found: Yes
- Core Python dependencies found: Yes
- Pytest result: 34 tests passed
- Backend sample pipeline run: Success in offline fallback mode
- FastAPI route structure: Present
- Frontend build: Failed locally
- LLM runtime check: Integrated but not operational now

10. Benchmark Note
The existing benchmark_results.csv file shows mixed OCR quality.
One sample scored about 56.25 percent, another 10.53 percent, mixed text 37.5 percent,
and Tamil samples 0 percent. This shows the project idea is working, but OCR quality and
Tamil handling still need improvement.

11. Final Conclusion
BrailleAir is a meaningful project with a clear goal. It already has a full processing pipeline,
a web API, a frontend, a Braille encoding layer, and optional AI integration.

The project is partially working.
The offline core demo works in a basic form.
The online structure exists, but it is not fully reliable in the current environment.
The LLM is integrated, but it is not working correctly now.

In simple words:
BrailleAir is a good working prototype, not a finished production-ready system.
""".strip()


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_lines(text: str, width: int = 92) -> list[str]:
    wrapped: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            wrapped.append("")
            continue
        if raw_line.startswith("- "):
            parts = textwrap.wrap(raw_line, width=width, subsequent_indent="  ")
            wrapped.extend(parts or [""])
        else:
            wrapped.extend(textwrap.wrap(raw_line, width=width) or [""])
    return wrapped


def build_pages(lines: list[str], lines_per_page: int = 46) -> list[list[str]]:
    return [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]


def make_content_stream(page_lines: list[str]) -> bytes:
    commands = [
        "BT",
        "/F1 11 Tf",
        "14 TL",
        "50 790 Td",
    ]
    for line in page_lines:
        if line == "":
            commands.append("() Tj")
        else:
            commands.append(f"({escape_pdf_text(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    content = "\n".join(commands).encode("ascii", errors="ignore")
    return content


def create_pdf(text: str, output_path: Path) -> None:
    lines = wrap_lines(text)
    pages = build_pages(lines)

    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    font_obj = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids = []
    content_ids = []

    pages_id_placeholder = add_object(b"")

    for page_lines in pages:
        stream = make_content_stream(page_lines)
        content_obj = add_object(
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii") + stream + b"\nendstream"
        )
        content_ids.append(content_obj)
        page_obj = add_object(
            f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_obj} 0 R >>".encode("ascii")
        )
        page_ids.append(page_obj)

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_id_placeholder - 1] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids [ {kids} ] >>".encode("ascii")
    )

    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_id_placeholder} 0 R >>".encode("ascii"))

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode(
            "ascii"
        )
    )

    output_path.write_bytes(pdf)


if __name__ == "__main__":
    create_pdf(REPORT_TEXT, OUTPUT)
    print(OUTPUT.resolve())
