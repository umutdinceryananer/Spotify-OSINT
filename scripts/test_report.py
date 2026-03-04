"""
Integration test for weekly time analysis report.
Requires .env with DATABASE_URL, GROQ_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
Usage: python -m scripts.test_report
"""

from src.database import get_active_playlists, get_tracks_for_report
from src.report import analyze_time_patterns, generate_time_report
from src.telegram import send_time_analysis_notification

playlists = get_active_playlists()
if not playlists:
    print("No active playlists found.")
    raise SystemExit(1)

playlist = playlists[0]
print(f"Testing with playlist: '{playlist['name']}' ({playlist['id']})")

# Step 1: DB query
tracks = get_tracks_for_report(playlist["id"], days=30)  # 30 days for more data
print(f"\nStep 1 — DB query: {len(tracks)} tracks found (last 30 days)")

if not tracks:
    print("No tracks in the last 30 days. Cannot test further.")
    raise SystemExit(1)

for t in tracks[:5]:
    print(f"  {t['detected_at']} — {t['track_name']} by {', '.join(t['artist_names'])}")
if len(tracks) > 5:
    print(f"  ... and {len(tracks) - 5} more")

# Step 2: Time pattern analysis
patterns = analyze_time_patterns(tracks)
print(f"\nStep 2 — Time patterns:")
print(f"  Total tracks: {patterns['total_tracks']}")
print(f"  Peak hour (Istanbul): {patterns['peak_hour']:02d}:00")
print(f"  Most active slot: {patterns['most_active_slot']}")
print(f"  Slot breakdown: {patterns['slot_counts']}")

# Step 3: Groq commentary
print("\nStep 3 — Generating Groq commentary...")
commentary = generate_time_report(patterns, playlist["name"])
if commentary:
    print(f"  {commentary}")
else:
    print("  GROQ_API_KEY not set or generation failed.")
    raise SystemExit(1)

# Step 4: Telegram notification
print("\nStep 4 — Sending Telegram notification...")
send_time_analysis_notification(commentary, playlist["name"], patterns)
print("  Sent! Check your Telegram.")
