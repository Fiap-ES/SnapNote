from dataclasses import dataclass
from datetime import date, datetime
from itertools import groupby
from pathlib import Path

import media_store
from core.index import Group, IndexedPhoto, Keyword, open_index
from core.search import search
from core.taxonomy import TaxonomyPath

CAPTURE_NAME_FORMAT = "%Y%m%d_%H%M%S_%f"


@dataclass(frozen=True)
class DateSection:
    day: date | None
    photos: list[IndexedPhoto]


@dataclass(frozen=True)
class Album:
    group: Group
    cover: IndexedPhoto


@dataclass(frozen=True)
class TaxonomyAlbum:
    node: TaxonomyPath
    photo_count: int
    cover: IndexedPhoto


def find_photos(
    index_path: Path, term: str = "", keyword_id: int | None = None
) -> list[IndexedPhoto]:
    with open_index(index_path) as index:
        photos = index.all_photos() if keyword_id is None else index.group(keyword_id)
        if term:
            found = {entry.path for entry in search(index, term)}
            photos = [photo for photo in photos if photo.path in found]
    return sorted(photos, key=_capture_order, reverse=True)


def photo_sections(index_path: Path) -> list[DateSection]:
    photos = find_photos(index_path)
    return [
        DateSection(day, list(group))
        for day, group in groupby(photos, key=_capture_day)
    ]


def _capture_order(photo: IndexedPhoto) -> tuple[bool, datetime]:
    # Em ordem decrescente: com data primeiro, das mais recentes para as mais
    # antigas; sem data (índice anterior à coluna) por último.
    return (photo.captured_at is not None, photo.captured_at or datetime.min)


def _capture_day(photo: IndexedPhoto) -> date | None:
    return None if photo.captured_at is None else photo.captured_at.date()


def groups(index_path: Path) -> list[Group]:
    with open_index(index_path) as index:
        return index.groups()


def albums(index_path: Path) -> list[Album]:
    # A capa é a foto mais recente do grupo; groups() só lista grupos com
    # ao menos uma foto, então sempre há capa.
    with open_index(index_path) as index:
        return [
            Album(group, max(index.group(group.keyword.id), key=_capture_order))
            for group in index.groups()
        ]


def taxonomy_albums(index_path: Path, parent: TaxonomyPath | None = None) -> list[TaxonomyAlbum]:
    with open_index(index_path) as index:
        return [
            TaxonomyAlbum(group.node, group.photo_count, max(index.classified(group.node), key=_capture_order))
            for group in index.taxonomy_children(parent)
        ]


def classified_photos(index_path: Path, node: TaxonomyPath) -> list[IndexedPhoto]:
    with open_index(index_path) as index:
        return sorted(index.classified(node), key=_capture_order, reverse=True)


def keywords(index_path: Path) -> list[Keyword]:
    with open_index(index_path) as index:
        return index.keywords()


def add_keyword(index_path: Path, term: str) -> Keyword:
    with open_index(index_path) as index:
        return index.add_keyword(term)


def rename_keyword(index_path: Path, keyword_id: int, term: str) -> None:
    with open_index(index_path) as index:
        index.rename_keyword(keyword_id, term)


def remove_keyword(index_path: Path, keyword_id: int) -> None:
    with open_index(index_path) as index:
        index.remove_keyword(keyword_id)


def index_photo(image_path: Path, index_path: Path) -> None:
    with open_index(index_path) as index:
        index.upsert(image_path)


def delete_photo(image_path: Path, index_path: Path) -> None:
    image_path.unlink()
    media_store.notify(image_path)
    with open_index(index_path) as index:
        index.remove(image_path)


def rebuild_index(photos_dir: Path, index_path: Path) -> None:
    with open_index(index_path) as index:
        index.rebuild(photos_dir)
