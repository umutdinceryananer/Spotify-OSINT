import logging
import re
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://genius.com/api/search/multi"


def get_lyrics(track_name: str, artist_name: str) -> str | None:
    """Scrape lyrics from Genius using a headless browser, or None if not found."""
    query = quote_plus(f"{track_name} {artist_name}")
    api_url = f"{_SEARCH_URL}?q={query}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()

            response = page.goto(api_url, timeout=15000)
            if not response or not response.ok:
                logger.warning(
                    "Genius API returned %s for '%s' — skipping lyrics.",
                    response.status if response else "no response",
                    track_name,
                )
                return None

            data = response.json()
            sections = data.get("response", {}).get("sections", [])

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
            page.goto(lyrics_url, timeout=15000)
            page.wait_for_selector('[data-lyrics-container="true"]', timeout=10000)

            containers = page.query_selector_all('[data-lyrics-container="true"]')
            if not containers:
                logger.warning("No lyrics containers found on Genius page: %s", lyrics_url)
                return None

            lines = [container.inner_text() for container in containers]
            lyrics = "\n".join(lines).strip()
            lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)

            return lyrics if lyrics else None

        except Exception:
            logger.warning("Genius scraping failed for '%s'.", track_name, exc_info=True)
            return None
        finally:
            browser.close()
