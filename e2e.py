import logging
import sys

from agents.ocr import run as o_run
from agents.preprocess import run as p_run
from agents.translate import run as t_run

logging.basicConfig(level=logging.INFO)


def _safe_preview(text: str) -> str:
    try:
        text.encode(sys.stdout.encoding or "utf-8")
        return text
    except Exception:
        return text.encode("ascii", errors="replace").decode("ascii")


state1 = {"image_path": "test_images/test_english_1.png", "retry_count": 0, "lang": ""}
state1 = p_run(state1)
state1 = o_run(state1)
state1 = t_run(state1)
print("Final 1:", _safe_preview(state1.get("final_text", "")))

state2 = {"image_path": "test_images/test_tamil_1.png", "retry_count": 0, "lang": ""}
state2 = p_run(state2)
state2 = o_run(state2)
state2 = t_run(state2)
print("Final 2:", _safe_preview(state2.get("final_text", "")))
