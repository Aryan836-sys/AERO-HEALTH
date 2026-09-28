"""Safe image uploads for community reports.

Never trusts the client: the declared Content-Type and filename are ignored.
The type is decided from the file's own magic bytes, the size is capped while
reading (so an oversized body is never fully buffered), and the file is saved
under a random name we generate -- the client's filename never touches disk.
"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import get_settings

URL_PREFIX = "/uploads"
CHUNK = 64 * 1024


def _detect_extension(head: bytes) -> str | None:
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ".webp"
    return None


def upload_root() -> Path:
    root = Path(get_settings().upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


async def save_image(file: UploadFile) -> str:
    """Validate and store an uploaded image; returns its public URL path."""
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    data = bytearray()
    while chunk := await file.read(CHUNK):
        data.extend(chunk)
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Image is too large (max {get_settings().max_upload_mb} MB)",
            )

    extension = _detect_extension(bytes(data[:16]))
    if extension is None:
        raise HTTPException(
            status_code=415, detail="Unsupported image type (use JPEG, PNG or WebP)"
        )

    name = f"{uuid.uuid4().hex}{extension}"
    (upload_root() / name).write_bytes(data)
    return f"{URL_PREFIX}/{name}"


def delete_image(url: str | None) -> None:
    """Best-effort removal of a stored image (used by delete-my-data)."""
    if not url or not url.startswith(f"{URL_PREFIX}/"):
        return
    path = (upload_root() / Path(url).name).resolve()
    # Refuse anything that resolves outside the upload directory.
    if path.parent == upload_root() and path.exists():
        path.unlink(missing_ok=True)
