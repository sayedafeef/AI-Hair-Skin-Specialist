import base64
import os
from io import BytesIO

from PIL import Image, ImageOps

MAX_DIMENSION = 1568
JPEG_QUALITY = 88


def encode_image_to_base64(image_path):
    """Reads a local image, normalizes it, and returns (base64_str, mime_type).

    Decodes with Pillow and re-encodes as a clean JPEG. This avoids issues
    with CMYK JPEGs, palette/alpha PNGs, odd ICC profiles, or oversized
    images that some vision APIs reject as "invalid image data".
    """
    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        raise ValueError(f"Image file missing or empty: {image_path}")

    try:
        img = Image.open(image_path)
        img.load()
    except Exception as e:
        raise ValueError(f"File is not a valid image: {image_path} ({e})")

    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    if img.mode != "RGB":
        img = img.convert("RGB")

    if max(img.size) > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return b64, "image/jpeg"
