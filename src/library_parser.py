from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List

from .models import TrackMetadata


class SeratoLibraryParser:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path).expanduser()

    def parse_tracks(self) -> List[TrackMetadata]:
        if not self.db_path.exists():
            return []

        connection = sqlite3.connect(str(self.db_path))
        try:
            return self._read_tracks(connection)
        finally:
            connection.close()

    def _read_tracks(self, connection: sqlite3.Connection) -> List[TrackMetadata]:
        table_columns = self._table_columns(connection)
        candidate_tables = [
            table
            for table, columns in table_columns.items()
            if {"title", "name"}.intersection(columns)
        ]

        tracks: List[TrackMetadata] = []
        for table in candidate_tables:
            columns = table_columns[table]
            sql = self._track_query(table, columns)
            for row in connection.execute(sql):
                title = row[0]
                if not title:
                    continue
                tracks.append(
                    TrackMetadata(
                        title=str(title),
                        artist=str(row[1] or ""),
                        bpm=float(row[2]) if row[2] is not None else None,
                        key=str(row[3]) if row[3] else None,
                        duration_seconds=int(row[4]) if row[4] is not None else None,
                        energy=float(row[5]) if row[5] is not None else None,
                        crate=str(row[6]) if row[6] else None,
                        path=str(row[7]) if row[7] else None,
                    )
                )
        return tracks

    @staticmethod
    def _table_columns(connection: sqlite3.Connection) -> Dict[str, set[str]]:
        tables = {}
        for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            info = connection.execute(f"PRAGMA table_info('{table}')").fetchall()
            tables[table] = {str(row[1]).lower() for row in info}
        return tables

    @staticmethod
    def _pick(columns: set[str], *options: str, default: str = "NULL") -> str:
        for option in options:
            if option in columns:
                return option
        return default

    def _track_query(self, table: str, columns: set[str]) -> str:
        title_col = self._pick(columns, "title", "name")
        artist_col = self._pick(columns, "artist", "album_artist")
        bpm_col = self._pick(columns, "bpm")
        key_col = self._pick(columns, "key", "musical_key")
        duration_col = self._pick(columns, "duration", "length", "duration_seconds")
        energy_col = self._pick(columns, "energy", "rating")
        crate_col = self._pick(columns, "crate", "crate_name")
        path_col = self._pick(columns, "path", "location", "file_path")
        return (
            f"SELECT {title_col}, {artist_col}, {bpm_col}, {key_col}, "
            f"{duration_col}, {energy_col}, {crate_col}, {path_col} FROM '{table}'"
        )
