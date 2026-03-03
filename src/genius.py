import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://genius.com/api/search/multi"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def get_lyrics(track_name: str, artist_name: str) -> str | None:
    """Search Genius and return lyrics by scraping, or None if not found."""
    response = requests.get(
        _SEARCH_URL,
        headers=_HEADERS,
        params={"q": f"{track_name} {artist_name}"},
        timeout=10,
    )
    response.raise_for_status()

    sections = response.json().get("response", {}).get("sections", [])
    lyrics_url = None
    for section in sections:
        for hit in section.get("hits", []):
            if hit.get("type") == "song":
                lyrics_url = hit["result"]["url"]
                break
        if lyrics_url:
            break

    if not lyrics_url:
        logger.info("No Genius results for '%s' by '%s'.", track_name, artist_name)
        return None

    logger.info("Fetching lyrics from %s", lyrics_url)
    page = requests.get(lyrics_url, headers=_HEADERS, timeout=10)
    page.raise_for_status()

    soup = BeautifulSoup(page.text, "html.parser")
    containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})

    if not containers:
        logger.warning("No lyrics containers found on Genius page: %s", lyrics_url)
        return None

    lines = []
    for container in containers:
        for br in container.find_all("br"):
            br.replace_with("\n")
        lines.append(container.get_text())

    lyrics = "\n".join(lines).strip()
    lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)

    return lyrics if lyrics else None
