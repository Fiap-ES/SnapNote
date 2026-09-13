from collections.abc import Callable
from pathlib import Path

import piexif
import pytest
from PIL import Image

from core import exif_store

MakeJpeg = Callable[..., Path]

UNDEFINED_USER_COMMENT = b"\x00" * 8 + b"texto gravado por outra camera"


def write_raw_user_comment(path: Path, raw: bytes) -> None:
    exif = piexif.load(str(path))
    exif["Exif"][piexif.ExifIFD.UserComment] = raw
    piexif.insert(piexif.dump(exif), str(path))


@pytest.fixture
def make_jpeg(tmp_path: Path) -> MakeJpeg:
    def _make_jpeg(name: str = "foto.jpg", note: str | None = None) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (4, 4), "white").save(path)
        if note is not None:
            exif_store.write_note(path, note)
        return path

    return _make_jpeg
