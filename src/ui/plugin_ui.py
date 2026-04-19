from __future__ import annotations

from typing import Callable, List, Optional

from ..models import CurrentTrackState, SuggestedTrack

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMessageBox,
        QPushButton,
        QProgressBar,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover
    QApplication = None  # type: ignore


class SuggestionPanel(QWidget):
    def __init__(self, on_queue: Optional[Callable[[SuggestedTrack], None]] = None) -> None:
        if QApplication is None:
            raise RuntimeError("PyQt5 is not installed. Install requirements.txt to use the UI.")
        super().__init__()
        self.on_queue = on_queue
        self._suggestions: List[SuggestedTrack] = []
        self.setWindowTitle("Serato AI DJ Sidekick")
        self.setMinimumWidth(520)

        self.track_label = QLabel("Waiting for Serato...")
        self.bpm_label = QLabel("BPM range: -")
        self.key_label = QLabel("Key compatibility: -")
        self.energy_bar = QProgressBar()
        self.energy_bar.setRange(0, 100)

        self.suggestions_list = QListWidget()
        self.suggestions_list.setDragEnabled(True)

        queue_button = QPushButton("Queue selected")
        queue_button.clicked.connect(self._queue_selected)

        load_button = QPushButton("Load selected")
        load_button.clicked.connect(self._load_selected)

        actions = QHBoxLayout()
        actions.addWidget(queue_button)
        actions.addWidget(load_button)

        layout = QVBoxLayout()
        layout.addWidget(self.track_label)
        layout.addWidget(self.bpm_label)
        layout.addWidget(self.key_label)
        layout.addWidget(self.energy_bar)
        layout.addWidget(self.suggestions_list)
        layout.addLayout(actions)

        self.setLayout(layout)

    def update_view(self, state: CurrentTrackState | None, suggestions: List[SuggestedTrack]) -> None:
        self._suggestions = suggestions
        if state is None:
            self.track_label.setText("Serato not running. Open Serato DJ Pro to start detection.")
            self.bpm_label.setText("BPM range: -")
            self.key_label.setText("Key compatibility: -")
            self.energy_bar.setValue(0)
        else:
            bpm_text = f"{state.bpm:.1f}" if state.bpm else "unknown"
            key_text = state.key or "unknown"
            self.track_label.setText(f"Now Playing: {state.title}")
            self.bpm_label.setText(f"BPM range target: {bpm_text}")
            self.key_label.setText(f"Current key: {key_text}")
            self.energy_bar.setValue(int(state.set_progress * 100))

        self.suggestions_list.clear()
        for index, suggestion in enumerate(suggestions[:5], start=1):
            text = (
                f"{index}. {suggestion.track.title} — {suggestion.track.artist} | "
                f"{suggestion.track.bpm or '-'} BPM | {suggestion.track.key or '-'}"
            )
            item = QListWidgetItem(text)
            item.setToolTip("\n".join(suggestion.reasons))
            item.setData(Qt.UserRole, index - 1)
            self.suggestions_list.addItem(item)

    def _queue_selected(self) -> None:
        item = self.suggestions_list.currentItem()
        if item is None:
            return
        self._dispatch_action("Queued")

    def _load_selected(self) -> None:
        item = self.suggestions_list.currentItem()
        if item is None:
            return
        self._dispatch_action("Loaded")

    def _dispatch_action(self, verb: str) -> None:
        item = self.suggestions_list.currentItem()
        if item is None:
            return
        index = int(item.data(Qt.UserRole))
        suggestion = self._suggestions[index]
        if self.on_queue:
            self.on_queue(suggestion)
        QMessageBox.information(self, "Serato AI Sidekick", f"{verb}: {suggestion.track.title}")
