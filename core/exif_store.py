from datetime import datetime
from pathlib import Path

import piexif
import piexif.helper

JPEG_SUFFIXES = frozenset({".jpg", ".jpeg"})
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"


class ExifStoreError(Exception):
    pass


class ImageNotFoundError(ExifStoreError):
    pass


class UnsupportedFormatError(ExifStoreError):
    pass


def write_note(image_path: str | Path, text: str) -> None:
    path = _jpeg_path(image_path)
    exif = piexif.load(str(path))
    # UserComment começa com 8 bytes que declaram a codificação do corpo.
    # O prefixo "UNICODE" grava o texto em UTF-16BE, a única opção do padrão
    # EXIF capaz de representar acentos e cedilha sem perda.
    exif["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
        text, encoding="unicode"
    )
    piexif.insert(piexif.dump(exif), str(path))


def read_note(image_path: str | Path) -> str | None:
    path = _jpeg_path(image_path)
    raw = piexif.load(str(path))["Exif"].get(piexif.ExifIFD.UserComment)
    if raw is None:
        return None
    try:
        return piexif.helper.UserComment.load(raw)
    except ValueError:
        # Câmeras de terceiros gravam UserComment com codificação indefinida
        # (prefixo de 8 bytes nulos); uma anotação ilegível vale como ausente.
        return None


def write_capture_time(image_path: str | Path, taken_at: datetime) -> None:
    path = _jpeg_path(image_path)
    exif = piexif.load(str(path))
    exif["Exif"][piexif.ExifIFD.DateTimeOriginal] = taken_at.strftime(EXIF_DATETIME_FORMAT).encode("ascii")
    piexif.insert(piexif.dump(exif), str(path))


def read_capture_time(image_path: str | Path) -> datetime | None:
    path = _jpeg_path(image_path)
    raw = piexif.load(str(path))["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
    if raw is None:
        return None
    try:
        return datetime.strptime(raw.decode("ascii"), EXIF_DATETIME_FORMAT)
    except ValueError:
        # Algumas câmeras gravam o campo preenchido com espaços ou zeros;
        # uma data ilegível vale como ausente.
        return None


def remove_note(image_path: str | Path) -> None:
    path = _jpeg_path(image_path)
    exif = piexif.load(str(path))
    # Sem campo a remover, o arquivo não é reescrito.
    if exif["Exif"].pop(piexif.ExifIFD.UserComment, None) is not None:
        piexif.insert(piexif.dump(exif), str(path))


def _jpeg_path(image_path: str | Path) -> Path:
    path = Path(image_path)
    if not path.is_file():
        raise ImageNotFoundError(str(path))
    if path.suffix.lower() not in JPEG_SUFFIXES:
        raise UnsupportedFormatError(str(path))
    return path
