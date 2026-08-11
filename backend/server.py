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
CATEGORIES_FILE = STORAGE / "categories.json"
HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
PORT = int(os.getenv("BACKEND_PORT", "8000"))
MAX_REQUEST_BYTES = 32 * 1024 * 1024
DATA_URL = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,(.+)$", re.DOTALL)
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
DEFAULT_CATEGORIES = [
    ["face", "얼굴 · 메이크업", "◉"], ["hair", "헤어", "⌇"], ["top", "상의", "♢"],
    ["bottom", "하의", "▽"], ["shoes", "신발", "⌁"], ["accessory", "악세사리", "✦"],
    ["quality", "화질", "▦"], ["place", "장소", "⌂"], ["pose", "자세", "人"],
    ["composition", "구도", "⊞"],
]


def load_prompts() -> list[dict]:
    if not PROMPTS_FILE.exists():
        return []
    value = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("prompts.json must contain an array")
    return value


def atomic_json_write(value: object, target: Path | None = None) -> None:
    target = target or PROMPTS_FILE
    STORAGE.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f"{target.stem}-", suffix=".tmp", dir=STORAGE)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_categories() -> list[list[str]]:
    if not CATEGORIES_FILE.exists():
        return [item.copy() for item in DEFAULT_CATEGORIES]
    value = json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    validate_categories(value)
    return value


def validate_categories(value: object) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError("at least one category is required")
    ids: set[str] = set()
    for item in value:
        if not isinstance(item, list) or len(item) != 3 or not all(isinstance(part, str) for part in item):
            raise ValueError("invalid category")
        category_id, name, icon = item
        if not category_id.strip() or not name.strip() or not icon.strip() or category_id in ids:
            raise ValueError("category id, name, and icon must be unique/non-empty")
        ids.add(category_id)


def save_categories(value: object) -> list[list[str]]:
    validate_categories(value)
    category_ids = {item[0] for item in value}
    used_ids = {prompt["category"] for prompt in load_prompts()}
    if not used_ids.issubset(category_ids):
        raise ValueError("cannot remove a category that still has prompts")
    atomic_json_write(value, CATEGORIES_FILE)
    return value


def validate_prompt(prompt: object) -> None:
    if not isinstance(prompt, dict):
        raise ValueError("prompt must be an object")
    for field in ("id", "category", "title", "prompt"):
        if not isinstance(prompt.get(field), str) or not prompt[field].strip():
            raise ValueError(f"{field} is required")
    if prompt["category"] not in {item[0] for item in load_categories()}:
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
            if path == "/api/categories":
                return self.json_response(200, load_categories())
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
        path = urlparse(self.path).path
        if path not in {"/api/prompts", "/api/categories"}:
            return self.json_response(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                return self.json_response(413, {"error": "request is too large"})
            incoming = json.loads(self.rfile.read(length))
            saved = save_categories(incoming) if path == "/api/categories" else save_prompts(incoming)
            self.json_response(200, saved)
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
