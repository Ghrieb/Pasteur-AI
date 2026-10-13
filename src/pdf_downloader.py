from pathlib import Path
import requests


PDF_MAGIC = b"%PDF"


def download_pdf(url: str, save_dir: str | Path, filename: str, timeout: int = 60) -> Path:
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    dest = save_dir / filename
    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download PDF from {url}: {e}")

    content_type = resp.headers.get("Content-Type", "")
    if "application/pdf" not in content_type and "octet-stream" not in content_type:
        if not _is_likely_pdf(resp.content[:len(PDF_MAGIC)]):
            raise RuntimeError(
                f"Response Content-Type is '{content_type}', not PDF. URL: {url}"
            )

    if not resp.content:
        raise RuntimeError(f"Downloaded file is empty (0 bytes). URL: {url}")

    if not _is_likely_pdf(resp.content[:len(PDF_MAGIC)]):
        raise RuntimeError(f"Downloaded file does not start with PDF header. URL: {url}")

    with open(dest, "wb") as f:
        f.write(resp.content)

    if dest.stat().st_size == 0:
        dest.unlink()
        raise RuntimeError(f"Saved PDF is empty (0 bytes). URL: {url}")

    return dest


def _is_likely_pdf(data: bytes) -> bool:
    return data.startswith(PDF_MAGIC)
