from __future__ import annotations

import json
import re
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from braille_map import encode_text
from pipeline import run_pipeline


APP_TITLE = "BrailleAir Online Dashboard API"
UPLOAD_DIR = Path("web_uploads")
STATE_PATH = UPLOAD_DIR / "web_state.json"

UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title=APP_TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class WorkerControl:
    stop_event: threading.Event
    thread: threading.Thread | None = None


worker_control = WorkerControl(stop_event=threading.Event())
_state_lock = threading.Lock()
_state: dict[str, Any] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_state() -> dict[str, Any]:
    return {
        "resources": {},
        "sessions": {},
        "glove_status": {
            "connected": True,
            "battery_pct": 88,
            "charging": False,
            "temperature_c": 34.2,
            "charger_voltage": 0.0,
            "firmware_version": "v0.9.0",
            "motor_health": ["ok", "ok", "ok", "ok", "ok", "ok"],
            "last_seen_at": _utc_now(),
        },
    }


def _load_state() -> None:
    global _state
    with _state_lock:
        if STATE_PATH.exists():
            try:
                _state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            except Exception:
                _state = _default_state()
        else:
            _state = _default_state()
            _persist_state()


def _persist_state() -> None:
    payload = json.dumps(_state, ensure_ascii=False, indent=2)
    STATE_PATH.write_text(payload, encoding="utf-8")


def _split_words(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return [w for w in cleaned.split(" ") if w]


def _extract_text_from_url(url: str) -> str:
    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {exc}") from exc

    html = resp.text
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) < 30:
        raise HTTPException(status_code=400, detail="URL content is too short or unreadable")
    return text


def _extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}:
        state = run_pipeline(str(path))
        text = state.get("final_text") or state.get("raw_text") or ""
        return text.strip()

    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="PDF upload needs pypdf. Install with: pip install pypdf",
            ) from exc

        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

    if suffix == ".docx":
        try:
            import docx
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="DOCX upload needs python-docx. Install with: pip install python-docx",
            ) from exc

        document = docx.Document(str(path))
        return "\n".join(p.text for p in document.paragraphs).strip()

    raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")


def _session_payload(session: dict[str, Any], include_words: bool = False) -> dict[str, Any]:
    total = int(session["total_words"])
    idx = int(session["current_word_index"])

    payload: dict[str, Any] = {
        "session_id": session["id"],
        "resource_id": session["resource_id"],
        "status": session["status"],
        "current_word_index": idx,
        "total_words": total,
        "progress_pct": round((idx / total) * 100, 2) if total else 0,
        "wpm": session["wpm"],
        "packets_sent": session["packets_sent"],
        "glove_connected": session["glove_connected"],
        "updated_at": session["updated_at"],
    }

    if include_words:
        words = _state["resources"][session["resource_id"]]["words"]
        display_idx = min(idx, len(words) - 1) if words else -1
        current_word = words[display_idx] if display_idx >= 0 else ""
        start = max(0, idx - 8)
        end = min(len(words), idx + 12)
        payload.update(
            {
                "current_word": current_word,
                "tracking_window": words[start:end],
                "tracking_window_start": start,
            }
        )

    return payload


def _create_resource(source_type: str, source_name: str, source_ref: str, text: str) -> dict[str, Any]:
    words = _split_words(text)
    if not words:
        raise HTTPException(status_code=400, detail="No readable words found in resource")

    resource_id = str(uuid.uuid4())
    resource = {
        "id": resource_id,
        "source_type": source_type,
        "source_name": source_name,
        "source_ref": source_ref,
        "text": text,
        "words": words,
        "total_words": len(words),
        "created_at": _utc_now(),
    }

    with _state_lock:
        _state["resources"][resource_id] = resource
        _persist_state()

    return {
        "resource_id": resource_id,
        "source_type": source_type,
        "source_name": source_name,
        "total_words": len(words),
        "created_at": resource["created_at"],
    }


def _send_word_to_glove(word: str, lang: str) -> int:
    seq = encode_text(word, lang=lang)
    return len(seq)


def _worker_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        dirty = False
        now = time.time()

        with _state_lock:
            for session in _state["sessions"].values():
                if session["status"] != "running":
                    continue
                if session["next_run_at"] > now:
                    continue

                resource = _state["resources"].get(session["resource_id"])
                if not resource:
                    continue

                words = resource["words"]
                idx = session["current_word_index"]
                total = session["total_words"]

                if idx >= total:
                    session["status"] = "completed"
                    session["stopped_at"] = _utc_now()
                    session["updated_at"] = _utc_now()
                    dirty = True
                    continue

                word = words[idx]
                lang = "ta" if re.search(r"[\u0B80-\u0BFF]", word) else "en"
                packets = _send_word_to_glove(word, lang)

                session["current_word_index"] = idx + 1
                session["packets_sent"] += packets
                session["updated_at"] = _utc_now()

                if session["current_word_index"] >= total:
                    session["status"] = "completed"
                    session["stopped_at"] = _utc_now()
                else:
                    session["next_run_at"] = now + (60.0 / max(30, int(session["wpm"])))
                dirty = True

            if dirty:
                _persist_state()

        time.sleep(0.25)


class LinkPayload(BaseModel):
    url: str = Field(..., min_length=10)


class StartSessionPayload(BaseModel):
    resource_id: str
    wpm: int = 120


class GloveTelemetryUpdate(BaseModel):
    connected: bool | None = None
    battery_pct: int | None = Field(default=None, ge=0, le=100)
    charging: bool | None = None
    temperature_c: float | None = None
    charger_voltage: float | None = None
    firmware_version: str | None = None
    motor_health: list[str] | None = None


@app.on_event("startup")
def on_startup() -> None:
    _load_state()
    worker_control.stop_event.clear()
    worker_control.thread = threading.Thread(
        target=_worker_loop,
        args=(worker_control.stop_event,),
        daemon=True,
        name="brailleair-session-worker",
    )
    worker_control.thread.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    worker_control.stop_event.set()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{APP_TITLE} is running"}


@app.get("/online/encode")
async def encode_text_endpoint(text: str, lang: str = "en") -> dict[str, Any]:
    """Encode a text string into Braille vibration sequence for UI display."""
    import re
    detected_lang = lang
    if not lang or lang == "auto":
        detected_lang = "ta" if re.search(r"[\u0B80-\u0BFF]", text) else "en"
    seq = encode_text(text, lang=detected_lang)
    return {
        "text": text,
        "lang": detected_lang,
        "vibration_seq": seq,
    }


@app.get("/online/capture-esp32")
async def capture_esp32() -> dict[str, Any]:
    # Force URL mode for capture agent
    import config
    original_mode = config.CAMERA_MODE
    config.CAMERA_MODE = "URL"
    
    try:
        # We pass an empty string because run_pipeline will start with 'capture' node
        # which uses config.CAMERA_MODE
        state = run_pipeline("")
        
        if state.get("error"):
            raise HTTPException(status_code=500, detail=state["error"])
            
        # Return the results
        return {
            "success": True,
            "final_text": state.get("final_text", ""),
            "vibration_seq": state.get("vibration_seq", []),
            "lang": state.get("lang", "en")
        }
    finally:
        config.CAMERA_MODE = original_mode


@app.post("/online/upload-resource")
async def upload_resource(file: UploadFile = File(...)) -> dict[str, Any]:
    ext = Path(file.filename or "uploaded.bin").suffix.lower()
    file_id = str(uuid.uuid4())
    target = UPLOAD_DIR / f"{file_id}{ext}"

    with target.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)

    text = _extract_text_from_file(target)
    return _create_resource(
        source_type="file",
        source_name=file.filename or target.name,
        source_ref=str(target),
        text=text,
    )


@app.post("/upload-book")
async def upload_book_legacy(file: UploadFile = File(...)) -> dict[str, Any]:
    ext = Path(file.filename or "uploaded.bin").suffix.lower()
    file_id = str(uuid.uuid4())
    target = UPLOAD_DIR / f"{file_id}{ext}"

    with target.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)

    state = run_pipeline(str(target))
    return {
        "success": True,
        "filename": file.filename or target.name,
        "detected_lang": state.get("lang"),
        "final_text": state.get("final_text"),
        "vibration_seq": state.get("vibration_seq"),
    }


@app.post("/online/add-link")
async def add_link(payload: LinkPayload) -> dict[str, Any]:
    text = _extract_text_from_url(payload.url)
    return _create_resource(
        source_type="url",
        source_name=payload.url[:80],
        source_ref=payload.url,
        text=text,
    )


@app.get("/online/resources")
async def list_resources() -> dict[str, Any]:
    with _state_lock:
        items = sorted(
            _state["resources"].values(),
            key=lambda r: r["created_at"],
            reverse=True,
        )

    return {
        "resources": [
            {
                "resource_id": r["id"],
                "source_type": r["source_type"],
                "source_name": r["source_name"],
                "total_words": r["total_words"],
                "created_at": r["created_at"],
            }
            for r in items
        ]
    }


@app.delete("/online/resources/{resource_id}")
async def delete_resource(resource_id: str) -> dict[str, Any]:
    with _state_lock:
        if resource_id not in _state["resources"]:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        resource = _state["resources"][resource_id]
        if resource.get("source_type") == "file":
            ref = resource.get("source_ref")
            if ref and "inline://" not in ref:
                file_path = Path(ref)
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception:
                        pass
        
        del _state["resources"][resource_id]
        
        sessions_to_remove = [k for k, v in _state["sessions"].items() if v.get("resource_id") == resource_id]
        for sid in sessions_to_remove:
            del _state["sessions"][sid]
            
        _persist_state()
        
    return {"success": True, "deleted": resource_id}


@app.post("/online/sessions/start")
async def start_session(payload: StartSessionPayload) -> dict[str, Any]:
    with _state_lock:
        resource = _state["resources"].get(payload.resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        session_id = str(uuid.uuid4())
        now = _utc_now()
        session = {
            "id": session_id,
            "resource_id": payload.resource_id,
            "status": "running",
            "current_word_index": 0,
            "total_words": resource["total_words"],
            "wpm": max(30, min(300, payload.wpm)),
            "glove_connected": True,
            "packets_sent": 0,
            "next_run_at": time.time(),
            "created_at": now,
            "updated_at": now,
            "stopped_at": None,
        }
        _state["sessions"][session_id] = session
        _persist_state()

        return _session_payload(session, include_words=True)


@app.post("/online/sessions/{session_id}/pause")
async def pause_session(session_id: str) -> dict[str, Any]:
    with _state_lock:
        session = _state["sessions"].get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session["status"] = "paused"
        session["updated_at"] = _utc_now()
        _persist_state()
        return _session_payload(session, include_words=True)


@app.post("/online/sessions/{session_id}/resume")
async def resume_session(session_id: str) -> dict[str, Any]:
    with _state_lock:
        session = _state["sessions"].get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session["status"] = "running"
        session["next_run_at"] = time.time()
        session["updated_at"] = _utc_now()
        _persist_state()
        return _session_payload(session, include_words=True)


class SpeedPayload(BaseModel):
    wpm: int = Field(..., ge=30, le=300)

@app.post("/online/sessions/{session_id}/speed")
async def update_session_speed(session_id: str, payload: SpeedPayload) -> dict[str, Any]:
    with _state_lock:
        session = _state["sessions"].get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session["wpm"] = payload.wpm
        session["updated_at"] = _utc_now()
        _persist_state()
        return _session_payload(session, include_words=True)


@app.post("/online/sessions/{session_id}/stop")
async def stop_session(session_id: str) -> dict[str, Any]:
    with _state_lock:
        session = _state["sessions"].get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session["status"] = "stopped"
        session["stopped_at"] = _utc_now()
        session["updated_at"] = _utc_now()
        _persist_state()
        return _session_payload(session, include_words=True)


@app.get("/online/sessions")
async def list_sessions() -> dict[str, Any]:
    with _state_lock:
        items = sorted(_state["sessions"].values(), key=lambda s: s["updated_at"], reverse=True)
        return {"sessions": [_session_payload(s) for s in items[:50]]}


@app.get("/online/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    with _state_lock:
        session = _state["sessions"].get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return _session_payload(session, include_words=True)


@app.get("/online/telemetry/glove")
async def glove_telemetry() -> dict[str, Any]:
    with _state_lock:
        g = _state["glove_status"].copy()

    g["safety"] = {
        "temperature_alert": g["temperature_c"] >= 42.0,
        "battery_alert": g["battery_pct"] <= 15,
    }
    return g


@app.post("/online/telemetry/glove")
async def update_glove_telemetry(payload: GloveTelemetryUpdate) -> dict[str, Any]:
    with _state_lock:
        g = _state["glove_status"]

        if payload.connected is not None:
            g["connected"] = payload.connected
        if payload.battery_pct is not None:
            g["battery_pct"] = payload.battery_pct
        if payload.charging is not None:
            g["charging"] = payload.charging
        if payload.temperature_c is not None:
            g["temperature_c"] = payload.temperature_c
        if payload.charger_voltage is not None:
            g["charger_voltage"] = payload.charger_voltage
        if payload.firmware_version is not None:
            g["firmware_version"] = payload.firmware_version
        if payload.motor_health is not None:
            g["motor_health"] = payload.motor_health

        g["last_seen_at"] = _utc_now()
        _persist_state()

    return await glove_telemetry()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
