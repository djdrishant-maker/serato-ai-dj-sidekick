import unittest

from src.serato_monitor import SeratoScreenMonitor


class SeratoMonitorTests(unittest.TestCase):
    def test_parses_ocr_content(self) -> None:
        text = """Track: Midnight Echo
BPM: 123.4
Key: Am
Time Remaining: 04:12
"""

        monitor = SeratoScreenMonitor(
            process_names=["Serato"],
            screenshot_func=lambda region=None: object(),
            ocr_func=lambda image: text,
            process_check_func=lambda names: True,
        )

        state = monitor.detect_current_track()
        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.title, "Midnight Echo")
        self.assertEqual(state.bpm, 123.4)
        self.assertEqual(state.key, "Am")
        self.assertEqual(state.time_remaining_seconds, 252)

    def test_returns_none_when_serato_not_running(self) -> None:
        monitor = SeratoScreenMonitor(
            process_names=["Serato"],
            screenshot_func=lambda region=None: object(),
            ocr_func=lambda image: "ignored",
            process_check_func=lambda names: False,
        )
        self.assertIsNone(monitor.detect_current_track())


if __name__ == "__main__":
    unittest.main()
