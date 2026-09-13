import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from core import exif_store

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    path TEXT PRIMARY KEY,
    note TEXT,
    file_modified_at TEXT NOT NULL,
    indexed_at TEXT NOT NULL
)
"""

UPSERT = """
INSERT INTO notes (path, note, file_modified_at, indexed_at)
VALUES (?, ?, ?, ?)
ON CONFLICT(path) DO UPDATE SET
    note = excluded.note,
    file_modified_at = excluded.file_modified_at,
    indexed_at = excluded.indexed_at
"""


@dataclass(frozen=True)
class IndexedNote:
    path: str
    note: str


class NoteIndex:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def upsert(self, image_path: str | Path) -> None:
        with self._connection:
            self._connection.execute(UPSERT, _row_for(Path(image_path)))

    def remove(self, image_path: str | Path) -> None:
        with self._connection:
            self._connection.execute(
                "DELETE FROM notes WHERE path = ?", (_key(Path(image_path)),)
            )

    def rebuild(self, folder: str | Path) -> None:
        rows = (_row_for(path) for path in _jpegs_in(Path(folder)))
        # Limpeza e reinserção compartilham uma transação: se a leitura de
        # algum arquivo falhar no meio, o índice anterior permanece intacto.
        with self._connection:
            self._connection.execute("DELETE FROM notes")
            self._connection.executemany(UPSERT, rows)

    def notes(self) -> list[IndexedNote]:
        rows = self._connection.execute(
            "SELECT path, note FROM notes WHERE note IS NOT NULL ORDER BY path"
        )
        return [IndexedNote(path, note) for path, note in rows]


@contextmanager
def open_index(db_path: str | Path) -> Iterator[NoteIndex]:
    connection = sqlite3.connect(db_path)
    try:
        with connection:
            connection.execute(SCHEMA)
        yield NoteIndex(connection)
    finally:
        connection.close()


def _row_for(path: Path) -> tuple[str, str | None, str, str]:
    note = exif_store.read_note(path)
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    indexed_at = datetime.now(tz=timezone.utc)
    return (_key(path), note, modified_at.isoformat(), indexed_at.isoformat())


def _key(path: Path) -> str:
    return str(path.resolve())


def _jpegs_in(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.iterdir()
        if path.suffix.lower() in exif_store.JPEG_SUFFIXES
    )
