from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from .models import CurrentTrackState


@dataclass
class OCRResult:
    text: str


class SeratoScreenMonitor:
    def __init__(
        self,
        process_names: list[str],
        ocr_region: Optional[tuple[int, int, int, int]] = None,
        screenshot_func: Optional[Callable[..., object]] = None,
        ocr_func: Optional[Callable[[object], str]] = None,
        process_check_func: Optional[Callable[[list[str]], bool]] = None,
    ) -> None:
        self.process_names = process_names
        self.ocr_region = ocr_region
        self._screenshot = screenshot_func
        self._ocr = ocr_func
        self._process_check = process_check_func or self._default_process_check

    def serato_running(self) -> bool:
        return self._process_check(self.process_names)

    def detect_current_track(self) -> CurrentTrackState | None:
        if not self.serato_running():
            return None
        text = self._capture_and_ocr_text()
        if not text:
            return None

        title = self._extract_title(text)
        bpm = self._extract_float(text, r"BPM\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)")
        key = self._extract_key(text)
        remaining = self._extract_time_remaining_seconds(text)

        if not title:
            return None

        return CurrentTrackState(
            title=title,
            bpm=bpm,
            key=key,
            time_remaining_seconds=remaining,
        )

    def _capture_and_ocr_text(self) -> str:
        image = None
        if self._screenshot:
            image = self._screenshot(region=self.ocr_region)
        else:
            try:
                import pyautogui  # type: ignore

                image = pyautogui.screenshot(region=self.ocr_region)
            except Exception:
                return ""

        if self._ocr:
            return self._ocr(image)
        try:
            import pytesseract  # type: ignore

            return pytesseract.image_to_string(image)
        except Exception:
            return ""

    @staticmethod
    def _default_process_check(process_names: list[str]) -> bool:
        commands = [
            ["ps", "aux"],
            ["tasklist"],
        ]
        for command in commands:
            try:
                output = subprocess.run(command, check=False, capture_output=True, text=True).stdout.lower()
            except Exception:
                continue
            if any(name.lower() in output for name in process_names):
                return True
        return False

    @staticmethod
    def _extract_title(text: str) -> str | None:
        title_match = re.search(r"Track\s*[:\-]\s*(.+)", text, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()

        non_empty = [line.strip() for line in text.splitlines() if line.strip()]
        return non_empty[0] if non_empty else None

    @staticmethod
    def _extract_float(text: str, pattern: str) -> float | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _extract_key(text: str) -> str | None:
        key_match = re.search(r"Key\s*[:\-]?\s*([A-G][#b]?m?)", text, re.IGNORECASE)
        return key_match.group(1) if key_match else None

    @staticmethod
    def _extract_time_remaining_seconds(text: str) -> int | None:
        match = re.search(r"(?:Time\s*Remaining|Remaining)\s*[:\-]?\s*(\d{1,2}:\d{2})", text, re.IGNORECASE)
        if not match:
            return None
        minutes, seconds = match.group(1).split(":")
        return int(minutes) * 60 + int(seconds)
