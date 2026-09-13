from pathlib import Path

from PIL import Image

from thumbnails import upright_thumbnail

ORIENTATION_TAG = 0x0112
ROTATED_90_CLOCKWISE = 6


def save_landscape_jpeg(path: Path, orientation: int | None = None) -> None:
    exif = Image.Exif()
    if orientation is not None:
        exif[ORIENTATION_TAG] = orientation
    Image.new("RGB", (400, 200), "white").save(path, exif=exif)


def test_thumbnail_fits_within_max_size_keeping_aspect_ratio(tmp_path: Path) -> None:
    photo = tmp_path / "foto.jpg"
    save_landscape_jpeg(photo)

    assert upright_thumbnail(photo, 100).size == (100, 50)


def test_thumbnail_applies_exif_orientation(tmp_path: Path) -> None:
    photo = tmp_path / "foto.jpg"
    save_landscape_jpeg(photo, orientation=ROTATED_90_CLOCKWISE)

    assert upright_thumbnail(photo, 100).size == (50, 100)


def test_thumbnail_is_rgb(tmp_path: Path) -> None:
    photo = tmp_path / "foto.jpg"
    Image.new("L", (400, 200)).save(photo)

    assert upright_thumbnail(photo, 100).mode == "RGB"
