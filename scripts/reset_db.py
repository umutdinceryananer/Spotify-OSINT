from src.database import _connection

with _connection() as conn:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tracked_tracks")
        cur.execute("UPDATE playlists SET snapshot_id = NULL")
print("DB reset done.")
