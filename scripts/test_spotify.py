"""
Integration test for Playwright-based playlist track scraping.
Usage: python -m scripts.test_spotify <playlist_id>
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_spotify.py <playlist_id>")
        sys.exit(1)

    playlist_id = sys.argv[1]

    from src.spotify import SpotifyClient

    client = SpotifyClient()
    tracks = client.get_playlist_tracks(playlist_id)

    if not tracks:
        logger.warning(
            "No tracks returned. Playlist may be empty, private, or invalid."
        )
        sys.exit(1)

    print(f"\nFetched {len(tracks)} tracks from playlist '{playlist_id}':\n")

    for i, track in enumerate(tracks[:5], 1):
        print(f"{i}. {track.track_name}")
        print(f"   Artists  : {', '.join(track.artist_names)}")
        print(f"   Album    : {track.album_name}")
        print(f"   URL      : {track.spotify_url}")
        print(f"   Added at : {track.added_at}")
        print()

    if len(tracks) > 5:
        print(f"... and {len(tracks) - 5} more tracks.\n")

    print("Issue 2 Playwright Scraping: PASSED")


if __name__ == "__main__":
    main()
