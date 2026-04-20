import tempfile
import unittest
from pathlib import Path

from src.profile_manager import load_profile, save_profile


class ProfileManagerTests(unittest.TestCase):
    def test_yaml_round_trip(self) -> None:
        profile = {"suggestion": {"bpm_tolerance_percent": 8, "energy_curve": "cooldown"}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.yaml"
            save_profile(profile, str(path))
            loaded = load_profile(str(path))
        self.assertEqual(loaded["suggestion"]["bpm_tolerance_percent"], 8)
        self.assertEqual(loaded["suggestion"]["energy_curve"], "cooldown")

    def test_json_round_trip(self) -> None:
        profile = {"set": {"default_duration_minutes": 90}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.json"
            save_profile(profile, str(path))
            loaded = load_profile(str(path))
        self.assertEqual(loaded["set"]["default_duration_minutes"], 90)


if __name__ == "__main__":
    unittest.main()
