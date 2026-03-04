"""Unit tests for time pattern analysis — no DB, no API, pure logic."""

from datetime import datetime, timezone, timedelta

from src.report import analyze_time_patterns, _TZ_ISTANBUL


def _make_track(utc_hour: int, day_offset: int = 0) -> dict:
    """Create a fake track dict with a specific UTC hour."""
    dt = datetime(2026, 3, 1, utc_hour, 30, tzinfo=timezone.utc) + timedelta(days=day_offset)
    return {
        "track_name": f"Track at {utc_hour}:30 UTC",
        "artist_names": ["Test Artist"],
        "detected_at": dt,
    }


class TestAnalyzeTimePatterns:
    def test_empty_list_returns_none(self):
        assert analyze_time_patterns([]) is None

    def test_utc_to_istanbul_conversion(self):
        """UTC 23:30 should become 02:30 Istanbul (next day), falling in 'gece' slot."""
        tracks = [_make_track(utc_hour=23)]  # 23:30 UTC = 02:30 Istanbul
        result = analyze_time_patterns(tracks)

        assert result is not None
        assert result["peak_hour"] == 2  # 02:30 Istanbul
        assert result["most_active_slot"] == "gece"

    def test_slot_distribution(self):
        """Tracks spread across different Istanbul hours."""
        tracks = [
            _make_track(utc_hour=1),   # 04:30 Istanbul → gece
            _make_track(utc_hour=2),   # 05:30 Istanbul → gece
            _make_track(utc_hour=5),   # 08:30 Istanbul → sabah
            _make_track(utc_hour=12),  # 15:30 Istanbul → öğleden sonra
            _make_track(utc_hour=18),  # 21:30 Istanbul → akşam
            _make_track(utc_hour=19),  # 22:30 Istanbul → akşam
            _make_track(utc_hour=20),  # 23:30 Istanbul → akşam
        ]
        result = analyze_time_patterns(tracks)

        assert result["total_tracks"] == 7
        assert result["slot_counts"]["gece"] == 2
        assert result["slot_counts"]["sabah"] == 1
        assert result["slot_counts"]["öğleden sonra"] == 1
        assert result["slot_counts"]["akşam"] == 3
        assert result["most_active_slot"] == "akşam"

    def test_peak_hour_with_multiple_at_same_hour(self):
        """Multiple tracks at the same Istanbul hour should produce correct peak."""
        tracks = [
            _make_track(utc_hour=21, day_offset=0),  # 00:30 Istanbul
            _make_track(utc_hour=21, day_offset=1),  # 00:30 Istanbul
            _make_track(utc_hour=21, day_offset=2),  # 00:30 Istanbul
            _make_track(utc_hour=10, day_offset=0),  # 13:30 Istanbul
        ]
        result = analyze_time_patterns(tracks)

        assert result["peak_hour"] == 0  # 00:30 Istanbul, 3 tracks
        assert result["hour_counts"][0] == 3
        assert result["hour_counts"][13] == 1

    def test_naive_datetime_treated_as_utc(self):
        """Timestamps without tzinfo should be treated as UTC."""
        naive_dt = datetime(2026, 3, 1, 21, 0)  # no tzinfo
        tracks = [{"track_name": "Test", "artist_names": ["A"], "detected_at": naive_dt}]
        result = analyze_time_patterns(tracks)

        # 21:00 UTC = 00:00 Istanbul
        assert result["peak_hour"] == 0

    def test_single_track(self):
        tracks = [_make_track(utc_hour=15)]  # 18:30 Istanbul → akşam
        result = analyze_time_patterns(tracks)

        assert result["total_tracks"] == 1
        assert result["peak_hour"] == 18
        assert result["most_active_slot"] == "akşam"

    def test_all_night_owl(self):
        """All tracks in the dead of night — classic insomniac pattern."""
        tracks = [
            _make_track(utc_hour=22, day_offset=i)  # 01:30 Istanbul
            for i in range(5)
        ]
        result = analyze_time_patterns(tracks)

        assert result["total_tracks"] == 5
        assert result["slot_counts"]["gece"] == 5
        assert result["slot_counts"]["sabah"] == 0
        assert result["most_active_slot"] == "gece"
        assert result["peak_hour"] == 1
