from urllib.parse import urljoin, urlparse, urlencode, parse_qs, ParseResult
from bs4 import BeautifulSoup


def find_download_link(html: str, page_url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    candidates = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "Download=True" in href and "handler=Download" in href:
            candidates.append(href)

    if not candidates:
        raise RuntimeError("No download link (Download=True + handler=Download) found on page")

    if len(candidates) > 1:
        candidates.sort(key=len)

    relative = candidates[0]
    absolute = urljoin(page_url, relative)
    return _normalise_download_url(absolute)


def _normalise_download_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["Download"] = ["True"]
    query["handler"] = ["Download"]
    new_query = urlencode(query, doseq=True)
    normalised = ParseResult(
        scheme=parsed.scheme,
        netloc=parsed.netloc,
        path=parsed.path,
        params=parsed.params,
        query=new_query,
        fragment=parsed.fragment,
    )
    return normalised.geturl()
