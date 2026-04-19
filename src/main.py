from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

from .communication import FileStateBridge
from .library_parser import SeratoLibraryParser
from .models import CurrentTrackState, TrackMetadata
from .profile_manager import load_profile, save_profile
from .serato_monitor import SeratoScreenMonitor
from .suggestion_engine import SuggestionConfig, SuggestionEngine


def load_config(path: str | None = None) -> dict:
    default_path = Path(__file__).parent / "config" / "default_config.yaml"
    with default_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if path:
        custom = load_profile(path)
        config = _deep_merge(config, custom)
    return config


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def build_engine(config: dict) -> SuggestionEngine:
    suggestion_config = config.get("suggestion", {})
    return SuggestionEngine(
        SuggestionConfig(
            max_results=int(suggestion_config.get("max_results", 5)),
            bpm_tolerance_percent=float(suggestion_config.get("bpm_tolerance_percent", 10)),
            compatible_semitones=tuple(int(x) for x in suggestion_config.get("compatible_semitones", [0, 1, 5])),
            energy_curve=str(suggestion_config.get("energy_curve", "build")),
        )
    )


def _demo_state() -> CurrentTrackState:
    return CurrentTrackState(
        title="Demo Track",
        bpm=124.0,
        key="Am",
        time_remaining_seconds=230,
        set_elapsed_seconds=2100,
        set_total_seconds=3600,
    )


def _demo_library() -> list[TrackMetadata]:
    return [
        TrackMetadata(title="Sunrise Groove", artist="DJ Nova", bpm=125, key="Am", duration_seconds=360, energy=0.68),
        TrackMetadata(title="Peak Hour Lights", artist="Kilo", bpm=127, key="Bm", duration_seconds=330, energy=0.84),
        TrackMetadata(title="Bassline Drift", artist="Mono", bpm=122, key="C", duration_seconds=300, energy=0.62),
        TrackMetadata(title="Neon Mirage", artist="Aria", bpm=124, key="Em", duration_seconds=390, energy=0.74),
        TrackMetadata(title="Afterglow", artist="Masa", bpm=120, key="G", duration_seconds=280, energy=0.56),
        TrackMetadata(title="Night Sprint", artist="Trek", bpm=129, key="A#m", duration_seconds=350, energy=0.9),
    ]


def run_headless(config: dict, demo: bool) -> int:
    parser = SeratoLibraryParser(config["library"]["db_path"])
    tracks = _demo_library() if demo else parser.parse_tracks()
    monitor = SeratoScreenMonitor(
        process_names=config["serato"]["process_names"],
        ocr_region=tuple(config["serato"]["ocr_region"]) if config["serato"].get("ocr_region") else None,
    )
    engine = build_engine(config)
    bridge = FileStateBridge(config["communication"]["state_file"])

    while True:
        current = _demo_state() if demo else monitor.detect_current_track()
        suggestions = engine.suggest(current, tracks) if current else []
        bridge.publish(current, suggestions)
        if current:
            print(f"Now playing: {current.title}")
            for item in suggestions:
                print(f"- {item.track.title}: {', '.join(item.reasons)}")
        else:
            print("Serato not running or OCR did not detect current track.")
        time.sleep(5)


def run_ui(config: dict, demo: bool, screenshot: str | None = None) -> int:
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication

    from .ui.plugin_ui import SuggestionPanel

    parser = SeratoLibraryParser(config["library"]["db_path"])
    tracks = _demo_library() if demo else parser.parse_tracks()
    monitor = SeratoScreenMonitor(
        process_names=config["serato"]["process_names"],
        ocr_region=tuple(config["serato"]["ocr_region"]) if config["serato"].get("ocr_region") else None,
    )
    engine = build_engine(config)
    bridge = FileStateBridge(config["communication"]["state_file"])

    app = QApplication(sys.argv)
    panel = SuggestionPanel()
    panel.show()

    def tick() -> None:
        current = _demo_state() if demo else monitor.detect_current_track()
        suggestions = engine.suggest(current, tracks) if current else []
        panel.update_view(current, suggestions)
        bridge.publish(current, suggestions)

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(2000)
    tick()

    if screenshot:
        app.processEvents()
        panel.grab().save(screenshot)
        return 0

    return app.exec_()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serato AI DJ Sidekick")
    parser.add_argument("--config", help="Path to profile YAML/JSON", default=None)
    parser.add_argument("--headless", action="store_true", help="Run without UI")
    parser.add_argument("--demo", action="store_true", help="Use demo data without Serato")
    parser.add_argument("--export-profile", help="Write merged profile to path")
    parser.add_argument("--screenshot", help="Save a UI screenshot and exit")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.export_profile:
        save_profile(config, args.export_profile)

    if args.headless:
        return run_headless(config, args.demo)
    return run_ui(config, args.demo, screenshot=args.screenshot)


if __name__ == "__main__":
    raise SystemExit(main())
