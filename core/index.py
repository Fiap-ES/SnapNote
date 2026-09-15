import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from core import exif_store
from core.keywords import matches
from core.text import normalize

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    path TEXT PRIMARY KEY,
    note TEXT,
    file_modified_at TEXT NOT NULL,
    indexed_at TEXT NOT NULL,
    captured_at TEXT
);
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY,
    term TEXT NOT NULL,
    normalized TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS photo_keywords (
    path TEXT NOT NULL REFERENCES notes(path) ON DELETE CASCADE,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (path, keyword_id)
);
"""

UPSERT = """
INSERT INTO notes (path, note, file_modified_at, indexed_at, captured_at)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT(path) DO UPDATE SET
    note = excluded.note,
    file_modified_at = excluded.file_modified_at,
    indexed_at = excluded.indexed_at,
    captured_at = excluded.captured_at
"""

PHOTO_COLUMNS = "path, note, captured_at"

INSERT_LINK = "INSERT INTO photo_keywords (path, keyword_id) VALUES (?, ?)"


@dataclass(frozen=True)
class IndexedPhoto:
    path: str
    note: str | None
    # A data não entra na igualdade: duas leituras da mesma foto continuam
    # sendo a mesma foto, e índices anteriores a esta coluna a têm nula.
    captured_at: datetime | None = field(default=None, compare=False)


@dataclass(frozen=True)
class IndexedNote(IndexedPhoto):
    note: str


@dataclass(frozen=True)
class Keyword:
    id: int
    term: str


@dataclass(frozen=True)
class Group:
    keyword: Keyword
    photo_count: int


class DuplicateKeywordError(Exception):
    pass


class NoteIndex:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def upsert(self, image_path: str | Path) -> None:
        row = _row_for(Path(image_path))
        path, note = row[:2]
        annotated = [IndexedNote(path, note)] if note is not None else []
        with self._connection:
            self._connection.execute(UPSERT, row)
            self._connection.execute("DELETE FROM photo_keywords WHERE path = ?", (path,))
            self._connection.executemany(INSERT_LINK, _links(annotated, self.keywords()))

    def remove(self, image_path: str | Path) -> None:
        with self._connection:
            self._connection.execute(
                "DELETE FROM notes WHERE path = ?", (_key(Path(image_path)),)
            )

    def rebuild(self, folder: str | Path) -> None:
        rows = (_row_for(path) for path in _jpegs_in(Path(folder)))
        # Limpeza e reinserção compartilham uma transação: se a leitura de
        # algum arquivo falhar no meio, o índice anterior permanece intacto.
        # Apagar as fotos apaga os vínculos em cascata; todos são refeitos.
        with self._connection:
            self._connection.execute("DELETE FROM notes")
            self._connection.executemany(UPSERT, rows)
            self._connection.executemany(INSERT_LINK, _links(self.notes(), self.keywords()))

    def notes(self) -> list[IndexedNote]:
        rows = self._connection.execute(
            f"SELECT {PHOTO_COLUMNS} FROM notes WHERE note IS NOT NULL ORDER BY path"
        )
        return [IndexedNote(path, note, _parse_time(captured)) for path, note, captured in rows]

    def all_photos(self) -> list[IndexedPhoto]:
        rows = self._connection.execute(f"SELECT {PHOTO_COLUMNS} FROM notes ORDER BY path")
        return [IndexedPhoto(path, note, _parse_time(captured)) for path, note, captured in rows]

    def keywords(self) -> list[Keyword]:
        rows = self._connection.execute("SELECT id, term FROM keywords ORDER BY normalized")
        return [Keyword(keyword_id, term) for keyword_id, term in rows]

    def add_keyword(self, term: str) -> Keyword:
        term, normalized = _clean_term(term)
        with self._connection:
            cursor = self._execute_unique(
                "INSERT INTO keywords (term, normalized) VALUES (?, ?)", (term, normalized)
            )
            keyword = Keyword(cursor.lastrowid, term)
            self._connection.executemany(INSERT_LINK, _links(self.notes(), [keyword]))
        return keyword

    def rename_keyword(self, keyword_id: int, term: str) -> None:
        term, normalized = _clean_term(term)
        keyword = Keyword(keyword_id, term)
        with self._connection:
            self._execute_unique(
                "UPDATE keywords SET term = ?, normalized = ? WHERE id = ?",
                (term, normalized, keyword_id),
            )
            self._connection.execute(
                "DELETE FROM photo_keywords WHERE keyword_id = ?", (keyword_id,)
            )
            self._connection.executemany(INSERT_LINK, _links(self.notes(), [keyword]))

    def remove_keyword(self, keyword_id: int) -> None:
        with self._connection:
            self._connection.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))

    def groups(self) -> list[Group]:
        rows = self._connection.execute(
            """
            SELECT keywords.id, keywords.term, COUNT(photo_keywords.path)
            FROM keywords JOIN photo_keywords ON photo_keywords.keyword_id = keywords.id
            GROUP BY keywords.id ORDER BY keywords.normalized
            """
        )
        return [Group(Keyword(keyword_id, term), count) for keyword_id, term, count in rows]

    def group(self, keyword_id: int) -> list[IndexedPhoto]:
        rows = self._connection.execute(
            """
            SELECT notes.path, notes.note, notes.captured_at
            FROM notes JOIN photo_keywords ON photo_keywords.path = notes.path
            WHERE photo_keywords.keyword_id = ? ORDER BY notes.path
            """,
            (keyword_id,),
        )
        return [IndexedPhoto(path, note, _parse_time(captured)) for path, note, captured in rows]

    def _execute_unique(self, statement: str, parameters: tuple) -> sqlite3.Cursor:
        try:
            return self._connection.execute(statement, parameters)
        except sqlite3.IntegrityError as error:
            raise DuplicateKeywordError(parameters[0]) from error


@contextmanager
def open_index(db_path: str | Path) -> Iterator[NoteIndex]:
    connection = sqlite3.connect(db_path)
    try:
        # O SQLite só honra ON DELETE CASCADE com a verificação ligada, e ela
        # é por conexão.
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        _add_capture_column(connection)
        yield NoteIndex(connection)
    finally:
        connection.close()


def _links(notes: Iterable[IndexedNote], keywords: Iterable[Keyword]) -> list[tuple[str, int]]:
    return [
        (note.path, keyword.id)
        for note in notes
        for keyword in keywords
        if matches(keyword.term, note.note)
    ]


def _clean_term(term: str) -> tuple[str, str]:
    term = term.strip()
    if not term:
        raise ValueError("palavra-chave em branco")
    return term, normalize(term)


# Índices criados antes desta coluna a recebem aqui, já preenchida com a
# reserva: a data de modificação registrada na indexação, convertida de UTC
# para o horário local, como a reindexação faria.
def _add_capture_column(connection: sqlite3.Connection) -> None:
    columns = {row[1] for row in connection.execute("PRAGMA table_info(notes)")}
    if "captured_at" in columns:
        return
    connection.execute("ALTER TABLE notes ADD COLUMN captured_at TEXT")
    rows = connection.execute("SELECT path, file_modified_at FROM notes").fetchall()
    with connection:
        connection.executemany(
            "UPDATE notes SET captured_at = ? WHERE path = ?",
            [(_local_time(modified_at).isoformat(), path) for path, modified_at in rows],
        )


def _local_time(utc_iso: str) -> datetime:
    return datetime.fromisoformat(utc_iso).astimezone().replace(tzinfo=None)


def _row_for(path: Path) -> tuple[str, str | None, str, str, str]:
    note = exif_store.read_note(path)
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    indexed_at = datetime.now(tz=timezone.utc)
    # DateTimeOriginal é a data de captura; a modificação do arquivo é só a
    # reserva, porque muda a cada reescrita do EXIF.
    captured_at = exif_store.read_capture_time(path) or datetime.fromtimestamp(path.stat().st_mtime)
    return (_key(path), note, modified_at.isoformat(), indexed_at.isoformat(), captured_at.isoformat())


def _parse_time(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def _key(path: Path) -> str:
    return str(path.resolve())


def _jpegs_in(folder: Path) -> list[Path]:
    return sorted(
        path for path in folder.iterdir()
        if path.suffix.lower() in exif_store.JPEG_SUFFIXES
    )
