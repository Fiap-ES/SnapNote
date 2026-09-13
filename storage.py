import shutil
from pathlib import Path

from kivy.app import App
from kivy.utils import platform

import media_store

if platform == "android":
    from android.storage import app_storage_path, primary_external_storage_path

CAPTURE_SUBDIR = "captures"
INDEX_FILENAME = "snapnote.db"
PUBLIC_ALBUM = Path("DCIM") / "SnapNote"


def app_dir() -> Path:
    if platform == "android":
        return Path(app_storage_path())
    return Path(App.get_running_app().user_data_dir)


def capture_location() -> str:
    # No Android o camera4kivy só grava capturas "private" dentro de
    # <app_dir>/DCIM; no desktop aceita qualquer diretório existente. Nos
    # dois casos a captura é só uma escala: publish() a leva para o álbum.
    return "private" if platform == "android" else str(app_dir())


def photos_dir() -> Path:
    # DCIM/SnapNote fica no armazenamento compartilhado e sobrevive à
    # desinstalação; no desktop a mesma estrutura vive dentro de app_dir().
    root = Path(primary_external_storage_path()) if platform == "android" else app_dir()
    album = root / PUBLIC_ALBUM
    album.mkdir(parents=True, exist_ok=True)
    return album


def index_path() -> Path:
    return app_dir() / INDEX_FILENAME


def publish(capture: Path) -> Path:
    photo = photos_dir() / capture.name
    shutil.move(capture, photo)
    media_store.notify(photo)
    return photo
