import io
import os
import uuid
from pathlib import Path
from PIL import Image, UnidentifiedImageError

import config

def process_and_save_receipt(file_stream_or_bytes, dest_dir=None) -> str:
    """
    Securely validates and stores uploaded payment receipts.

    - Validates image integrity using Pillow (Image.open().verify()).
    - Verifies format is within ('JPEG', 'PNG', 'WEBP').
    - Re-encodes image to clean RGB JPEG to strip dangerous EXIF metadata,
      embedded scripts, and polyglot payloads.
    - Saves to private_uploads/{uuid4().hex}.jpg outside the web root.
    - Raises ValueError if the file is invalid, unsupported, empty, or corrupted.
    - Returns the safe filepath as a string.
    """
    if file_stream_or_bytes is None:
        raise ValueError("No receipt file provided.")

    if isinstance(file_stream_or_bytes, (str, Path)):
        if not os.path.exists(file_stream_or_bytes):
            raise ValueError(f"File not found: {file_stream_or_bytes}")
        with open(file_stream_or_bytes, "rb") as f:
            raw_bytes = f.read()
    elif hasattr(file_stream_or_bytes, "read"):
        if hasattr(file_stream_or_bytes, "seek"):
            try:
                file_stream_or_bytes.seek(0)
            except Exception:
                pass
        raw_bytes = file_stream_or_bytes.read()
        if isinstance(raw_bytes, str):
            raw_bytes = raw_bytes.encode("utf-8")
    elif isinstance(file_stream_or_bytes, (bytes, bytearray)):
        raw_bytes = bytes(file_stream_or_bytes)
    else:
        raise ValueError(f"Unsupported input type for file_stream_or_bytes: {type(file_stream_or_bytes)}")

    if not raw_bytes:
        raise ValueError("Receipt file content is empty.")

    bio = io.BytesIO(raw_bytes)

    # 1. Image integrity verification
    try:
        with Image.open(bio) as img:
            img.verify()
    except (UnidentifiedImageError, SyntaxError, OSError, Exception) as e:
        raise ValueError(f"Invalid or corrupted image: {e}")

    # verify() leaves file pointer in undefined state; re-open fresh stream for decoding
    bio.seek(0)
    try:
        with Image.open(bio) as img:
            img_format = img.format
            if img_format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError(f"Unsupported image format '{img_format}'. Only JPEG, PNG, and WEBP are allowed.")

            # Re-encode to clean RGB JPEG (strips EXIF, scripts, polyglots)
            rgb_img = img.convert("RGB")

            if dest_dir is None:
                dest_dir = getattr(config, "PRIVATE_UPLOADS_DIR", os.path.join(config.BASE_DIR, "private_uploads"))
            os.makedirs(dest_dir, exist_ok=True)

            unique_filename = f"{uuid.uuid4().hex}.jpg"
            safe_filepath = os.path.join(str(dest_dir), unique_filename)
            rgb_img.save(safe_filepath, format="JPEG", quality=90)
            return str(safe_filepath)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Failed to process and re-encode image: {e}")
