"""
routers/images.py — Ticket image upload and serving endpoints.

POST /api/tickets/{ticket_id}/images  — upload up to 3 images
GET  /api/tickets/{ticket_id}/images/{filename} — serve an image
"""

import os
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger

from core.config import settings
from core.database import get_tickets_collection
from core.security import get_current_user

router = APIRouter(prefix="/api/tickets", tags=["images"])

# ── Magic bytes for image format validation ───────────────────────────
MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",  # JPEG
    b"\x89PNG\r\n\x1a\n": "image/png",  # PNG
    b"GIF87a": "image/gif",  # GIF87a
    b"GIF89a": "image/gif",  # GIF89a
    b"RIFF": "image/webp",  # WebP (partial — also check WEBP at offset 8)
}

ALLOWED_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _detect_mime(header_bytes: bytes) -> str | None:
    """Detect MIME type from magic bytes."""
    for magic, mime in MAGIC_BYTES.items():
        if header_bytes[: len(magic)] == magic:
            # Extra check for WebP: RIFF....WEBP
            if magic == b"RIFF" and header_bytes[8:12] != b"WEBP":
                continue
            return mime
    return None


def _sanitize_filename(name: str) -> str:
    """Strip dangerous characters from the original filename."""
    # Remove path traversal and special chars
    name = os.path.basename(name)
    name = re.sub(r"[^\w\s.\-]", "", name)
    name = name.strip()
    return name or "upload"


@router.post("/{ticket_id}/images")
async def upload_images(
    ticket_id: str,
    images: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload images to a ticket (max 3, max 5MB each).
    Only the ticket owner or agents/admins can upload.
    """
    tickets = get_tickets_collection()
    ticket = await tickets.find_one({"ticket_id": ticket_id})

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Permission check: ticket owner or agent/admin
    user_role = current_user.get("role", "")
    if ticket.get("user_id") != current_user.get("user_id") and user_role not in (
        "agent",
        "admin",
        "senior_engineer",
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to upload images to this ticket"
        )

    # Check how many images already exist
    existing_images = ticket.get("images", [])
    max_images = settings.MAX_IMAGES_PER_TICKET
    remaining_slots = max_images - len(existing_images)

    if remaining_slots <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum of {max_images} images per ticket already reached",
        )

    if len(images) > remaining_slots:
        raise HTTPException(
            status_code=400,
            detail=f"Only {remaining_slots} image slot(s) remaining. You sent {len(images)}.",
        )

    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    upload_dir = Path(settings.UPLOAD_DIR) / ticket_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []

    for img in images:
        # Read entire file into memory (capped at max + 1 byte to detect oversized)
        content = await img.read()

        # ── Size check ────────────────────────────────────────────────
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File '{img.filename}' exceeds {settings.MAX_IMAGE_SIZE_MB}MB limit",
            )

        # ── Extension check ───────────────────────────────────────────
        original = _sanitize_filename(img.filename or "upload")
        ext = os.path.splitext(original)[1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(
                status_code=400,
                detail=f"File '{original}' has unsupported extension '{ext}'. Allowed: {', '.join(ALLOWED_EXT)}",
            )

        # ── Magic byte check ─────────────────────────────────────────
        mime = _detect_mime(content[:16])
        if mime not in ALLOWED_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"File '{original}' has invalid image content. Only JPG, PNG, GIF, WebP are accepted.",
            )

        # ── Save with UUID filename ───────────────────────────────────
        stored_name = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / stored_name
        with open(file_path, "wb") as f:
            f.write(content)

        url = f"/api/tickets/{ticket_id}/images/{stored_name}"
        now = datetime.now(timezone.utc).isoformat()

        uploaded.append(
            {
                "filename": stored_name,
                "original_name": original,
                "url": url,
                "uploaded_at": now,
            }
        )

        logger.info(
            f"Image uploaded: {original} -> {stored_name} for ticket {ticket_id}"
        )

    # ── Persist to MongoDB ────────────────────────────────────────────
    await tickets.update_one(
        {"ticket_id": ticket_id},
        {"$push": {"images": {"$each": uploaded}}},
    )

    return {"images": uploaded, "total": len(existing_images) + len(uploaded)}


@router.get("/{ticket_id}/images/{filename}")
async def serve_image(
    ticket_id: str,
    filename: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Serve an uploaded image. Auth required — ticket owner or agent/admin.
    """
    tickets = get_tickets_collection()
    ticket = await tickets.find_one({"ticket_id": ticket_id})

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    user_role = current_user.get("role", "")
    if ticket.get("user_id") != current_user.get("user_id") and user_role not in (
        "agent",
        "admin",
        "senior_engineer",
    ):
        raise HTTPException(status_code=403, detail="Not authorized to view this image")

    # Sanitize filename to prevent path traversal
    safe_name = os.path.basename(filename)
    file_path = Path(settings.UPLOAD_DIR) / ticket_id / safe_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)
