from pathlib import Path
from PIL import Image
from pyzbar.pyzbar import decode


SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}


def scan_qr_images(folder: str | Path) -> list[dict]:
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"QR codes folder not found: {folder}")

    results = []
    for img_path in folder.iterdir():
        if img_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            image = Image.open(img_path)
            decoded = decode(image)
            if not decoded:
                results.append({
                    "filename": img_path.name,
                    "url": None,
                    "error": "No QR code found in image",
                })
                continue
            for obj in decoded:
                url = obj.data.decode("utf-8").strip()
                results.append({
                    "filename": img_path.name,
                    "url": url,
                    "error": None,
                })
        except Exception as e:
            results.append({
                "filename": img_path.name,
                "url": None,
                "error": str(e),
            })
    return results
