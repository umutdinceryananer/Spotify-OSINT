"""Track addition time analysis — detects when a playlist owner is most active."""

import logging
from datetime import timezone, timedelta

logger = logging.getLogger(__name__)

_TZ_ISTANBUL = timezone(timedelta(hours=3))

_TIME_SLOTS = {
    "gece": (0, 6),       # 00:00–05:59
    "sabah": (6, 12),     # 06:00–11:59
    "öğleden sonra": (12, 18),  # 12:00–17:59
    "akşam": (18, 24),    # 18:00–23:59
}


def analyze_time_patterns(tracks: list[dict]) -> dict | None:
    """Analyze detected_at timestamps and return structured time patterns.

    Returns None if there are no tracks to analyze.
    """
    if not tracks:
        return None

    hours = []
    for t in tracks:
        dt = t["detected_at"]
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local = dt.astimezone(_TZ_ISTANBUL)
        hours.append(local.hour)

    # Hour frequency (0–23)
    hour_counts = [0] * 24
    for h in hours:
        hour_counts[h] += 1

    # Time slot distribution
    slot_counts = {}
    for slot_name, (start, end) in _TIME_SLOTS.items():
        slot_counts[slot_name] = sum(hour_counts[start:end])

    # Peak hour
    peak_hour = max(range(24), key=lambda h: hour_counts[h])

    # Most active slot
    most_active_slot = max(slot_counts, key=slot_counts.get)

    return {
        "total_tracks": len(tracks),
        "hour_counts": hour_counts,
        "slot_counts": slot_counts,
        "peak_hour": peak_hour,
        "most_active_slot": most_active_slot,
    }


_MODEL = "llama-3.3-70b-versatile"


def generate_time_report(patterns: dict, playlist_name: str) -> str | None:
    """Send time pattern data to Groq and get a Turkish commentary.

    Returns None if GROQ_API_KEY is not configured.
    """
    from groq import Groq
    from src.config import config

    if not config.groq_api_key:
        logger.warning("GROQ_API_KEY not set — skipping time report.")
        return None

    slot_summary = ", ".join(
        f"{slot}: {count}" for slot, count in patterns["slot_counts"].items()
    )

    prompt = (
        f'"{playlist_name}" adlı playlistte son 7 günde '
        f'{patterns["total_tracks"]} şarkı eklendi.\n\n'
        f"Zaman dilimi dağılımı (Türkiye saati):\n{slot_summary}\n"
        f'En yoğun saat: {patterns["peak_hour"]:02d}:00\n'
        f'En aktif zaman dilimi: {patterns["most_active_slot"]}\n\n'
        "Bu verilere dayanarak, playlist sahibinin yaşam düzeni ve "
        "alışkanlıkları hakkında bir yorum yap.\n\n"
        "Kurallar:\n"
        "- Yanıtını YALNIZCA Türkçe yaz. Başka dilde kesinlikle kelime kullanma.\n"
        "- Tam olarak 2-3 cümle yaz.\n"
        "- Pesimist ama gerçekçi bir bakış açısı benimse.\n"
        "- Klişelerden kaçın, günlük konuşma dili kullan.\n"
        "- Saatleri ve zaman dilimlerini yorumuna dahil et.\n"
        "- Kısa ve öz ol, gereksiz tekrar yapma."
    )

    client = Groq(api_key=config.groq_api_key)
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=400,
    )

    return response.choices[0].message.content.strip()


def run() -> None:
    """Generate and send weekly time analysis for all active playlists."""
    from src.database import get_active_playlists, get_tracks_for_report
    from src.telegram import send_time_analysis_notification, send_error_notification

    playlists = get_active_playlists()
    if not playlists:
        logger.info("No active playlists — nothing to report.")
        return

    for playlist in playlists:
        playlist_id = playlist["id"]
        playlist_name = playlist["name"]

        try:
            tracks = get_tracks_for_report(playlist_id)
            patterns = analyze_time_patterns(tracks)

            if patterns is None:
                logger.info("No tracks in last 7 days for '%s' — skipping.", playlist_name)
                continue

            commentary = generate_time_report(patterns, playlist_name)
            if commentary is None:
                logger.warning("Could not generate report for '%s'.", playlist_name)
                continue

            send_time_analysis_notification(commentary, playlist_name, patterns)
            logger.info("Time analysis sent for '%s'.", playlist_name)

        except Exception as exc:
            logger.exception("Report failed for '%s'.", playlist_name)
            send_error_notification(
                f"Weekly report failed for '{playlist_name}': {exc}"
            )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    )
    run()
