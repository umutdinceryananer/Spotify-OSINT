import logging
import time

from src.database import get_active_playlists, get_known_track_ids, is_first_run, save_tracks
from src.spotify import SpotifyClient
from src.telegram import send_error_notification, send_new_track_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)

logger = logging.getLogger(__name__)


def run() -> None:
    client = SpotifyClient()
    playlists = get_active_playlists()

    if not playlists:
        logger.info("No active playlists to monitor.")
        return

    logger.info("Monitoring %d playlist(s).", len(playlists))

    for playlist in playlists:
        playlist_id = playlist["id"]
        playlist_name = playlist["name"]

        logger.info("Checking playlist: '%s' (%s)", playlist_name, playlist_id)

        current_tracks = client.get_playlist_tracks(playlist_id)

        if not current_tracks:
            logger.warning(
                "Playlist '%s' (%s) returned no tracks — private or inaccessible, skipping.",
                playlist_name,
                playlist_id,
            )
            continue

        if is_first_run(playlist_id):
            save_tracks(current_tracks, playlist_id)
            logger.info(
                "First run for '%s': saved %d tracks, no notifications sent.",
                playlist_name,
                len(current_tracks),
            )
            continue

        known_ids = get_known_track_ids(playlist_id)
        new_tracks = [t for t in current_tracks if t.track_id not in known_ids]

        if not new_tracks:
            logger.info("No new tracks in '%s'.", playlist_name)
            continue

        logger.info(
            "%d new track(s) detected in '%s'.", len(new_tracks), playlist_name
        )

        for track in new_tracks:
            send_new_track_notification(track, playlist_name)
            time.sleep(1)  # Telegram rate limit: 1 message/second per chat

        save_tracks(new_tracks, playlist_id)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        logger.exception("Unhandled exception in monitor run.")
        send_error_notification(str(exc))
        raise
