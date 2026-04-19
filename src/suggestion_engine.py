from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from .models import CurrentTrackState, SuggestedTrack, TrackMetadata

NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}

CAM_MEANING = {
    "A": "minor",
    "B": "major",
}


@dataclass
class SuggestionConfig:
    max_results: int = 5
    bpm_tolerance_percent: float = 10.0
    compatible_semitones: Tuple[int, ...] = (0, 1, 5)
    energy_curve: str = "build"


class SuggestionEngine:
    def __init__(self, config: SuggestionConfig) -> None:
        self.config = config

    def suggest(self, current: CurrentTrackState, tracks: Iterable[TrackMetadata]) -> List[SuggestedTrack]:
        suggestions: List[SuggestedTrack] = []
        for track in tracks:
            if track.title == current.title:
                continue
            score, reasons = self._score_track(current, track)
            if score <= 0:
                continue
            suggestions.append(SuggestedTrack(track=track, score=round(score, 3), reasons=reasons))

        suggestions.sort(key=lambda item: item.score, reverse=True)
        return suggestions[: self.config.max_results]

    def _score_track(self, current: CurrentTrackState, track: TrackMetadata) -> tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []

        bpm_score, bpm_reason = self._bpm_score(current.bpm, track.bpm)
        score += bpm_score
        if bpm_reason:
            reasons.append(bpm_reason)

        key_score, key_reasons = self._key_score(current.key, track.key)
        score += key_score
        reasons.extend(key_reasons)

        energy_score, energy_reason = self._energy_score(current, track)
        score += energy_score
        if energy_reason:
            reasons.append(energy_reason)

        if current.time_remaining_seconds is not None and track.duration_seconds is not None:
            if track.duration_seconds <= current.time_remaining_seconds + 120:
                score += 0.15
                reasons.append("Fits remaining set time")

        return score, reasons

    def _bpm_score(self, current_bpm: float | None, candidate_bpm: float | None) -> tuple[float, str | None]:
        if not current_bpm or not candidate_bpm:
            return 0.0, None
        tolerance = current_bpm * (self.config.bpm_tolerance_percent / 100.0)
        delta = abs(candidate_bpm - current_bpm)
        if delta > tolerance:
            return -1.0, None
        closeness = max(0.0, 1.0 - (delta / max(tolerance, 1e-6)))
        return 1.7 * closeness, f"BPM compatible ({candidate_bpm:.1f} within ±{self.config.bpm_tolerance_percent:.0f}%)"

    def _key_score(self, current_key: str | None, candidate_key: str | None) -> tuple[float, List[str]]:
        if not current_key or not candidate_key:
            return 0.0, []

        current_parsed = self._parse_key(current_key)
        candidate_parsed = self._parse_key(candidate_key)
        if current_parsed is None or candidate_parsed is None:
            return 0.0, []

        score = 0.0
        reasons: List[str] = []
        current_semi, current_mode = current_parsed
        candidate_semi, candidate_mode = candidate_parsed
        semitone_delta = (candidate_semi - current_semi) % 12

        if semitone_delta in self.config.compatible_semitones:
            score += 1.2 if semitone_delta == 0 else 0.9
            reasons.append(f"Key compatible (+{semitone_delta} semitone)")

        current_camelot = self._to_camelot(current_semi, current_mode)
        candidate_camelot = self._to_camelot(candidate_semi, candidate_mode)
        if current_camelot and candidate_camelot and self._camelot_compatible(current_camelot, candidate_camelot):
            score += 0.9
            reasons.append(f"Camelot compatible ({current_camelot} -> {candidate_camelot})")

        return score, reasons

    def _energy_score(self, current: CurrentTrackState, track: TrackMetadata) -> tuple[float, str | None]:
        target = self._target_energy(current.set_progress, current.time_remaining_seconds)
        candidate = self._track_energy(track)
        distance = abs(target - candidate)
        score = max(0.0, 1.0 - distance) * 1.1
        return score, f"Energy match ({candidate:.2f}, target {target:.2f})"

    def _target_energy(self, set_progress: float, time_remaining_seconds: int | None) -> float:
        if self.config.energy_curve == "cooldown":
            base = 1.0 - set_progress
        elif self.config.energy_curve == "peak_mid":
            base = 1.0 - abs(0.5 - set_progress) * 2
        else:
            base = set_progress

        if time_remaining_seconds is not None:
            if time_remaining_seconds < 10 * 60:
                base = max(base, 0.75)
            elif time_remaining_seconds < 20 * 60:
                base = max(base, 0.6)

        return max(0.0, min(1.0, base))

    @staticmethod
    def _track_energy(track: TrackMetadata) -> float:
        if track.energy is not None:
            return max(0.0, min(1.0, track.energy))
        if not track.bpm:
            return 0.5
        return max(0.0, min(1.0, (track.bpm - 80.0) / 80.0))

    @staticmethod
    def _parse_key(key: str) -> tuple[int, str] | None:
        key = key.strip()
        if len(key) < 1:
            return None
        note = key[0].upper()
        accidental = ""
        remainder = key[1:]
        if remainder and remainder[0] in {"#", "b"}:
            accidental = remainder[0]
            remainder = remainder[1:]
        mode = "minor" if remainder.lower().startswith("m") else "major"
        full_note = note + accidental
        if full_note not in NOTE_TO_SEMITONE:
            return None
        return NOTE_TO_SEMITONE[full_note], mode

    @staticmethod
    def _to_camelot(semitone: int, mode: str) -> str:
        major_map = {11: 1, 6: 2, 1: 3, 8: 4, 3: 5, 10: 6, 5: 7, 0: 8, 7: 9, 2: 10, 9: 11, 4: 12}
        minor_map = {8: 1, 3: 2, 10: 3, 5: 4, 0: 5, 7: 6, 2: 7, 9: 8, 4: 9, 11: 10, 6: 11, 1: 12}
        table = minor_map if mode == "minor" else major_map
        number = table.get(semitone)
        suffix = "A" if mode == "minor" else "B"
        return f"{number}{suffix}" if number else ""

    @staticmethod
    def _camelot_compatible(current: str, candidate: str) -> bool:
        try:
            c_num = int(current[:-1])
            c_mode = current[-1]
            t_num = int(candidate[:-1])
            t_mode = candidate[-1]
        except Exception:
            return False

        neighbors = {((c_num - 2) % 12) + 1, (c_num % 12) + 1, c_num}
        return (t_num in neighbors and t_mode == c_mode) or (t_num == c_num and t_mode != c_mode)
