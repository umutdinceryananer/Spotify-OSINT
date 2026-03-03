import logging
import re
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

logger = logging.getLogger(__name__)


def get_lyrics(track_name: str, artist_name: str) -> str | None:
    """Scrape lyrics from Genius using a headless browser, or None if not found."""
    query = quote_plus(f"{track_name} {artist_name}")
    search_url = f"https://genius.com/search?q={query}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(search_url, timeout=15000)

            # Wait for JS-rendered song results (links ending in -lyrics)
            try:
                page.wait_for_selector('a[href$="-lyrics"]', timeout=8000)
            except PlaywrightTimeoutError:
                logger.info("No Genius results for '%s' by '%s'.", track_name, artist_name)
                return None

            link = page.query_selector('a[href$="-lyrics"]')
            if not link:
                logger.info("No Genius results for '%s' by '%s'.", track_name, artist_name)
                return None

            lyrics_url = link.get_attribute("href")
            if not lyrics_url:
                return None
            if not lyrics_url.startswith("http"):
                lyrics_url = f"https://genius.com{lyrics_url}"

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
