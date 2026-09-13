from pathlib import Path

import piexif
import pytest
from PIL import Image

from core import exif_store
from core.exif_store import ImageNotFoundError, UnsupportedFormatError
from tests.conftest import UNDEFINED_USER_COMMENT, MakeJpeg, write_raw_user_comment

NOTE_WITH_ACCENTS = "Farmácia São João — remédio p/ pressão, ação às 9h, maçã"


def test_note_survives_write_read_cycle_with_accents(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg()

    exif_store.write_note(path, NOTE_WITH_ACCENTS)

    assert exif_store.read_note(path) == NOTE_WITH_ACCENTS


def test_note_is_stored_with_unicode_encoding_prefix(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg()

    exif_store.write_note(path, NOTE_WITH_ACCENTS)

    raw = piexif.load(str(path))["Exif"][piexif.ExifIFD.UserComment]
    assert raw.startswith(b"UNICODE\x00")


def test_read_note_returns_none_when_image_has_no_note(make_jpeg: MakeJpeg) -> None:
    assert exif_store.read_note(make_jpeg()) is None


def test_read_note_returns_none_for_undefined_encoding(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg()
    write_raw_user_comment(path, UNDEFINED_USER_COMMENT)

    assert exif_store.read_note(path) is None


def test_write_note_replaces_previous_note(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg(note="primeira")

    exif_store.write_note(path, "segunda")

    assert exif_store.read_note(path) == "segunda"


def test_write_note_preserves_existing_exif(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg()
    camera_exif = {
        "0th": {piexif.ImageIFD.Make: b"Canon", piexif.ImageIFD.Model: b"EOS R"},
        "Exif": {piexif.ExifIFD.DateTimeOriginal: b"2026:09:13 10:00:00"},
    }
    piexif.insert(piexif.dump(camera_exif), str(path))

    exif_store.write_note(path, "nota")

    exif = piexif.load(str(path))
    assert exif["0th"][piexif.ImageIFD.Make] == b"Canon"
    assert exif["0th"][piexif.ImageIFD.Model] == b"EOS R"
    assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2026:09:13 10:00:00"


def test_remove_note_deletes_user_comment_and_keeps_other_exif(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg(note="nota")
    exif = piexif.load(str(path))
    exif["0th"][piexif.ImageIFD.Make] = b"Canon"
    piexif.insert(piexif.dump(exif), str(path))

    exif_store.remove_note(path)

    assert exif_store.read_note(path) is None
    assert piexif.load(str(path))["0th"][piexif.ImageIFD.Make] == b"Canon"


def test_remove_note_without_note_leaves_file_untouched(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg()
    original = path.read_bytes()

    exif_store.remove_note(path)

    assert path.read_bytes() == original


def test_write_note_keeps_image_decodable(make_jpeg: MakeJpeg) -> None:
    path = make_jpeg()

    exif_store.write_note(path, NOTE_WITH_ACCENTS)

    with Image.open(path) as image:
        assert image.size == (4, 4)


def test_missing_file_raises_image_not_found(tmp_path: Path) -> None:
    with pytest.raises(ImageNotFoundError):
        exif_store.read_note(tmp_path / "inexistente.jpg")


def test_non_jpeg_raises_unsupported_format(tmp_path: Path) -> None:
    path = tmp_path / "foto.png"
    Image.new("RGB", (4, 4), "white").save(path)

    with pytest.raises(UnsupportedFormatError):
        exif_store.write_note(path, "nota")
