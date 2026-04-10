# pipeline.py
# Day 3 — LangGraph State + Pipeline Skeleton
# Orchestrates: capture → preprocess → ocr → (retry?) → translate → encode → vibrate → END

from typing import Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# ---------------------------------------------------------------------------
# 1. BrailleState TypedDict
#    Single shared state that all agents read/write
# ---------------------------------------------------------------------------
class BrailleState(TypedDict):
    image_path: str          # path to the input image
    cleaned_image: Any       # preprocessed image (numpy array or PIL Image)
    raw_text: str            # OCR-extracted raw text
    lang: str                # detected language ('en' or 'ta')
    final_text: str          # translated / cleaned text
    vibration_seq: list      # list of dicts from encode_text()
    retry_count: int         # number of OCR retry attempts
    error: str               # error message if any


# ---------------------------------------------------------------------------
# 2. Placeholder nodes — each prints its name and returns state unchanged
# ---------------------------------------------------------------------------
def capture_node(state: BrailleState) -> BrailleState:
    """Load / capture the input image."""
    print("[NODE] capture")
    return state


def preprocess_node(state: BrailleState) -> BrailleState:
    """Clean and enhance the image for OCR."""
    print("[NODE] preprocess")
    return state


def ocr_node(state: BrailleState) -> BrailleState:
    """Run Tesseract OCR on the cleaned image."""
    print("[NODE] ocr")
    # Increment retry_count so conditional edge can track attempts
    return {**state, "retry_count": state.get("retry_count", 0) + 1}


def translate_node(state: BrailleState) -> BrailleState:
    """Detect language and optionally translate."""
    print("[NODE] translate")
    return state


def encode_node(state: BrailleState) -> BrailleState:
    """Convert final text to 5-bit Braille sequences."""
    print("[NODE] encode")
    return state


def vibrate_node(state: BrailleState) -> BrailleState:
    """Send Braille vibration sequence to BLE device."""
    print("[NODE] vibrate")
    return state


# ---------------------------------------------------------------------------
# 3. Conditional retry edge
#    If raw_text is empty and retry_count < 2, loop back to preprocess
# ---------------------------------------------------------------------------
def should_retry(state: BrailleState) -> str:
    """Decide whether to retry OCR or continue to translate."""
    if state.get("raw_text", "") == "" and state.get("retry_count", 0) < 2:
        print(f"[RETRY] raw_text empty, retry_count={state.get('retry_count', 0)} -> back to preprocess")
        return "retry"
    return "continue"


# ---------------------------------------------------------------------------
# Build the LangGraph pipeline
# ---------------------------------------------------------------------------
def build_graph() -> StateGraph:
    graph = StateGraph(BrailleState)

    # Add nodes
    graph.add_node("capture", capture_node)
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("ocr", ocr_node)
    graph.add_node("translate", translate_node)
    graph.add_node("encode", encode_node)
    graph.add_node("vibrate", vibrate_node)

    # Set entry point
    graph.set_entry_point("capture")

    # Linear edges
    graph.add_edge("capture", "preprocess")
    graph.add_edge("preprocess", "ocr")

    # Conditional edge after OCR: retry if raw_text is empty
    graph.add_conditional_edges(
        "ocr",
        should_retry,
        {
            "retry": "preprocess",    # loop back
            "continue": "translate",  # proceed
        },
    )

    # Continue linear path
    graph.add_edge("translate", "encode")
    graph.add_edge("encode", "vibrate")
    graph.add_edge("vibrate", END)

    return graph


# ---------------------------------------------------------------------------
# 4. Compile and run
# ---------------------------------------------------------------------------
def run_pipeline(image_path: str):
    """Compile the graph and invoke with initial state."""
    graph = build_graph()
    app = graph.compile()

    initial_state: BrailleState = {
        "image_path": image_path,
        "cleaned_image": None,
        "raw_text": "",
        "lang": "",
        "final_text": "",
        "vibration_seq": [],
        "retry_count": 0,
        "error": "",
    }

    print(f"\n{'='*50}")
    print(f"  BarileAir Pipeline — LangGraph Skeleton")
    print(f"  Input: {image_path}")
    print(f"{'='*50}\n")

    result = app.invoke(initial_state)

    print(f"\n{'='*50}")
    print(f"  Pipeline complete!")
    print(f"  Final state keys: {list(result.keys())}")
    print(f"{'='*50}\n")

    return result


if __name__ == "__main__":
    run_pipeline("test_images/test_english_1.png")
