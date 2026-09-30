import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from utils.clean_text import clean_article_text


MAX_RESPONSE_BYTES = 2_000_000
REQUEST_TIMEOUT_SECONDS = 10.0
USER_AGENT = "TechScopeAI/1.0"


class FetchError(ValueError):
    """Raised when a URL cannot be fetched safely or successfully."""


def validate_public_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise FetchError("Only public HTTP and HTTPS URLs are accepted")
    if parsed.username or parsed.password:
        raise FetchError("URLs with embedded credentials are not accepted")

    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    except (OSError, ValueError) as exc:
        raise FetchError("The URL hostname could not be resolved") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise FetchError("The URL must resolve to a public IP address")

    return parsed.geturl()


def fetch_article(raw_url: str) -> dict:
    url = validate_public_url(raw_url)

    try:
        with httpx.Client(
            follow_redirects=False,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            with client.stream("GET", url) as response:
                if 300 <= response.status_code < 400:
                    raise FetchError("Redirects are not supported for article URLs")
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_RESPONSE_BYTES:
                    raise FetchError("The remote response is too large")

                chunks = []
                total_bytes = 0
                for chunk in response.iter_bytes():
                    total_bytes += len(chunk)
                    if total_bytes > MAX_RESPONSE_BYTES:
                        raise FetchError("The remote response is too large")
                    chunks.append(chunk)
                html = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
    except FetchError:
        raise
    except (httpx.HTTPError, UnicodeError, ValueError) as exc:
        raise FetchError("The article could not be fetched") from exc

    cleaned_content = clean_article_text(html)
    if len(cleaned_content) < 100:
        raise FetchError("The fetched page does not contain enough article text")

    parsed = urlparse(url)
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(" ", strip=True) if title_tag else ""
    return {
        "url": url,
        "title": title,
        "source": parsed.hostname or "",
        "content": cleaned_content,
    }