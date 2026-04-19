# Serato AI DJ Sidekick

A Python companion plugin that runs alongside Serato DJ Pro and suggests the next track in real time.

## Features

- Real-time Serato monitoring through screen scraping + OCR (track name, BPM, key, time remaining)
- Rule-based suggestion engine with:
  - BPM matching (default ±10%, configurable)
  - Key compatibility (same key, +1/+5 semitone, Camelot-compatible)
  - Energy curve control (`build`, `cooldown`, `peak_mid`) with set-duration awareness
- Serato library parsing from SQLite metadata
- PyQt5 floating panel with top-5 recommendations, reasons, indicators, and queue/load actions
- Profile import/export (YAML/JSON)
- File-based communication bridge (`~/.serato_ai_sidekick/state.json`)
- Graceful behavior when Serato is not running

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python -m src.main --demo
```

Use `--headless` to run without GUI.

## Config

Default config: `/home/runner/work/serato-ai-dj-sidekick/serato-ai-dj-sidekick/src/config/default_config.yaml`

You can provide an override profile:

```bash
python -m src.main --config /path/to/profile.yaml
```

Export merged profile:

```bash
python -m src.main --config /path/to/profile.yaml --export-profile /path/to/out.json --headless --demo
```

## Tests

```bash
python -m unittest discover -s tests -v
```
