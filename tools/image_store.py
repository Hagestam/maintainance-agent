# tools/image_store.py
"""
Saves incoming WhatsApp images to disk and returns a stable file path
that gets stored in work_order.photo_url.

Directory layout:
    uploads/
        work_order_photos/
            20240723_143201_26XXXXXXXXX.jpg
            ...

You can swap the local-disk logic for S3/GCS later without touching
any other file — just change `save_image()` to return a cloud URL.
"""
import base64
import os
from datetime import datetime

# Where photos land on disk (relative to project root).
# Change to an absolute path like "/var/data/uploads" in production.
UPLOAD_DIR = os.path.join("uploads", "work_order_photos")


def save_image(
    image_base64: str,
    mime_type: str,
    from_number: str,
) -> str | None:
    """
    Decodes a base64 image and writes it to UPLOAD_DIR.

    Returns:
        The file path string (stored in work_order.photo_url), or
        None if anything goes wrong (so the work order still gets created).
    """
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Pick the right extension from the MIME type (image/jpeg → .jpg)
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg":  ".jpg",
            "image/png":  ".png",
            "image/webp": ".webp",
            "image/gif":  ".gif",
        }
        ext = ext_map.get(mime_type.lower(), ".jpg")

        # Build a unique filename: timestamp + sanitised phone number
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_number = from_number.replace("@c.us", "").replace("+", "")
        filename = f"{timestamp}_{safe_number}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Decode and write
        image_bytes = base64.b64decode(image_base64)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return filepath

    except Exception as exc:
        print(f"[image_store] Failed to save image: {exc}")
        return None
