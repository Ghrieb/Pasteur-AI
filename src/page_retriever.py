import requests


def retrieve_page(url: str, timeout: int = 30) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url}")
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to retrieve page {url}: {e}")
