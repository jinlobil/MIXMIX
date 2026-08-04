#!/usr/bin/env python3
"""Prompt Atelier local JSON and image-file API (standard library only)."""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import shutil
import tempfile
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
STORAGE = ROOT / "storage"
IMAGE_DIR = STORAGE / "images"
PROMPTS_FILE = STORAGE / "prompts.json"
HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("BACKEND_PORT", "8000"))
MAX_REQUEST_BYTES = 32 * 1024 * 1024
DATA_URL = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,(.+)$", re.DOTALL)
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
CATEGORIES = {"face", "hair", "top", "bottom", "shoes", "accessory", "quality", "place", "pose", "composition"}


def load_prompts() -> list[dict]:
    if not PROMPTS_FILE.exists():
        return []
    value = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("prompts.json must contain an array")
    return value


def atomic_json_write(value: list[dict]) -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="prompts-", suffix=".tmp", dir=STORAGE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, PROMPTS_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def validate_prompt(prompt: object) -> None:
    if not isinstance(prompt, dict):
        raise ValueError("prompt must be an object")
    for field in ("id", "category", "title", "prompt"):
        if not isinstance(prompt.get(field), str) or not prompt[field].strip():
            raise ValueError(f"{field} is required")
    if prompt["category"] not in CATEGORIES:
        raise ValueError("unknown category")
    images = prompt.get("images", [])
    if not isinstance(images, list) or len(images) > 3:
        raise ValueError("a prompt can have up to 3 images")
    if not all(isinstance(image, str) for image in images):
        raise ValueError("invalid image value")


def store_data_url(value: str) -> str:
    match = DATA_URL.match(value)
    if not match:
        raise ValueError("only JPEG, PNG, and WebP images are accepted")
    mime, encoded = match.groups()
    try:
        content = base64.b64decode(encoded, validate=True)
    except ValueError as error:
        raise ValueError("invalid image data") from error
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("each image must be 10MB or smaller")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{EXTENSIONS[mime]}"
    target = IMAGE_DIR / name
    target.write_bytes(content)
    return f"/uploads/{name}"


def save_prompts(incoming: object) -> list[dict]:
    if not isinstance(incoming, list):
        raise ValueError("request body must be an array")
    for prompt in incoming:
        validate_prompt(prompt)
    previous = load_prompts()
    created: list[Path] = []
    normalized: list[dict] = []
    try:
        for prompt in incoming:
            item = {key: value for key, value in prompt.items() if key != "images"}
            item["images"] = []
            for image in prompt.get("images", []):
                if image.startswith("/uploads/"):
                    name = Path(unquote(urlparse(image).path)).name
                    item["images"].append(f"/uploads/{name}")
                else:
                    stored = store_data_url(image)
                    created.append(IMAGE_DIR / Path(stored).name)
                    item["images"].append(stored)
            normalized.append(item)
        atomic_json_write(normalized)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise

    referenced = {Path(image).name for prompt in normalized for image in prompt.get("images", [])}
    old_referenced = {Path(image).name for prompt in previous for image in prompt.get("images", [])}
    for name in old_referenced - referenced:
        (IMAGE_DIR / name).unlink(missing_ok=True)
    return normalized


class Handler(BaseHTTPRequestHandler):
    server_version = "PromptAtelier/1.0"

    def json_response(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                return self.json_response(200, {"ok": True, "storage": "json"})
            if path == "/api/prompts":
                return self.json_response(200, load_prompts())
            if path.startswith("/uploads/"):
                name = Path(unquote(path)).name
                target = IMAGE_DIR / name
                if not target.is_file():
                    return self.json_response(404, {"error": "image not found"})
                content = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(target)[0] or "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
                self.end_headers()
                self.wfile.write(content)
                return
            self.json_response(404, {"error": "not found"})
        except (OSError, ValueError, json.JSONDecodeError) as error:
            self.json_response(500, {"error": str(error)})

    def do_PUT(self) -> None:
        if urlparse(self.path).path != "/api/prompts":
            return self.json_response(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                return self.json_response(413, {"error": "request is too large"})
            incoming = json.loads(self.rfile.read(length))
            self.json_response(200, save_prompts(incoming))
        except (ValueError, json.JSONDecodeError) as error:
            self.json_response(400, {"error": str(error)})
        except OSError as error:
            self.json_response(500, {"error": str(error)})

    def log_message(self, message: str, *args: object) -> None:
        print(f"[backend] {self.address_string()} - {message % args}")


def main() -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Prompt Atelier Python API → http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
