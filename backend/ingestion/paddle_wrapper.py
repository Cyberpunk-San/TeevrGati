"""
PaddleOCR Subprocess Wrapper
============================
Runs PaddleOCR inside a Python 3.10 venv (venv_paddle/) via subprocess,
since PaddleOCR has no wheels for Python 3.14.

The main Python 3.14 backend calls this module; it invokes the 3.10 venv
and returns structured JSON results. Falls back gracefully to Gemini Vision
or PyMuPDF regex if the venv is not set up.

Setup (one-time):
    bash scripts/setup_paddleocr.sh
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_VENV_PADDLE  = _PROJECT_ROOT / "venv_paddle"
_PADDLE_PYTHON = _VENV_PADDLE / "bin" / "python"

_PADDLE_WORKER = """
import sys, json
from paddleocr import PaddleOCR

image_path = sys.argv[1]
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)
result = ocr.ocr(image_path, cls=True)

extracted = []
for line in result or []:
    for item in (line or []):
        if isinstance(item, (list, tuple)) and len(item) == 2:
            box, (text, conf) = item
            extracted.append({"text": text, "confidence": float(conf), "box": box})

print(json.dumps({"success": True, "extractions": extracted}))
"""

# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def is_paddle_available() -> bool:
    """True if the venv_paddle Python 3.10 environment is set up."""
    return _PADDLE_PYTHON.exists()


def run_paddle_ocr(image_path: str | Path, timeout: int = 60) -> Optional[list[dict]]:
    """
    Run PaddleOCR on an image file using the isolated Python 3.10 venv.

    Args:
        image_path: Path to the image to process.
        timeout:    Seconds before subprocess times out.

    Returns:
        List of dicts: [{"text": str, "confidence": float, "box": list}, ...]
        None if PaddleOCR unavailable or if an error occurs.
    """
    if not is_paddle_available():
        print("[PaddleOCR] venv_paddle not found — run scripts/setup_paddleocr.sh", file=sys.stderr)
        return None

    image_path = str(Path(image_path).resolve())
    if not os.path.exists(image_path):
        print(f"[PaddleOCR] Image not found: {image_path}", file=sys.stderr)
        return None

    # Write the worker script to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(_PADDLE_WORKER)
        worker_path = f.name

    try:
        proc = subprocess.run(
            [str(_PADDLE_PYTHON), worker_path, image_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            print(f"[PaddleOCR] Worker failed: {proc.stderr[-500:]}", file=sys.stderr)
            return None

        result = json.loads(proc.stdout.strip())
        if result.get("success"):
            extractions = result.get("extractions", [])
            print(f"[PaddleOCR] Extracted {len(extractions)} text regions", file=sys.stderr)
            return extractions
        return None

    except subprocess.TimeoutExpired:
        print(f"[PaddleOCR] Timed out after {timeout}s", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"[PaddleOCR] Invalid JSON from worker: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[PaddleOCR] Unexpected error: {e}", file=sys.stderr)
        return None
    finally:
        try:
            os.unlink(worker_path)
        except OSError:
            pass


def extract_text_from_image(image_path: str | Path) -> str:
    """
    High-level convenience: returns plain text from an image using PaddleOCR.
    Returns empty string if not available.
    """
    extractions = run_paddle_ocr(image_path)
    if not extractions:
        return ""
    # Sort by vertical position (top of bounding box), then join
    sorted_ex = sorted(extractions, key=lambda x: (x["box"][0][1] if x.get("box") else 0))
    return " ".join(e["text"] for e in sorted_ex if e.get("text"))


# ──────────────────────────────────────────────────────────────────────────────
# CLI self-test
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python paddle_wrapper.py <image_path>")
        print(f"PaddleOCR available: {is_paddle_available()}")
        sys.exit(0)

    img = sys.argv[1]
    print(f"Processing: {img}")
    result = run_paddle_ocr(img)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("No result / PaddleOCR not available.")
