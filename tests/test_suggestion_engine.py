import unittest

from src.models import CurrentTrackState, TrackMetadata
from src.suggestion_engine import SuggestionConfig, SuggestionEngine


class SuggestionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SuggestionEngine(
            SuggestionConfig(max_results=5, bpm_tolerance_percent=10, compatible_semitones=(0, 1, 5), energy_curve="build")
        )

    def test_returns_top_matches_with_reasons(self) -> None:
        current = CurrentTrackState(
            title="Current",
            bpm=124,
            key="Am",
            time_remaining_seconds=420,
            set_elapsed_seconds=2400,
            set_total_seconds=3600,
        )
        library = [
            TrackMetadata(title="Exact Fit", bpm=124, key="Am", energy=0.66, duration_seconds=300),
            TrackMetadata(title="Compatible Fit", bpm=128, key="Bm", energy=0.75, duration_seconds=330),
            TrackMetadata(title="Bad BPM", bpm=160, key="Am", energy=0.9, duration_seconds=300),
        ]

        suggestions = self.engine.suggest(current, library)

        self.assertGreaterEqual(len(suggestions), 2)
        self.assertEqual(suggestions[0].track.title, "Exact Fit")
        self.assertTrue(any("BPM compatible" in reason for reason in suggestions[0].reasons))

    def test_excludes_current_track(self) -> None:
        current = CurrentTrackState("Current", 120, "C", 300)
        library = [TrackMetadata(title="Current", bpm=120, key="C")]
        self.assertEqual(self.engine.suggest(current, library), [])


if __name__ == "__main__":
    unittest.main()
