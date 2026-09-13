from pathlib import Path

from kivy.app import App
from kivy.utils import platform

if platform == "android":
    from android.storage import app_storage_path

PHOTOS_SUBDIR = "photos"
INDEX_FILENAME = "snapnote.db"


def data_dir() -> Path:
    # No Android o camera4kivy só grava capturas "private" dentro de
    # <app_storage_path>/DCIM; no desktop ele aceita qualquer diretório
    # existente, papel que o user_data_dir do Kivy cumpre. A galeria pode
    # abrir antes da primeira captura, quando o camera4kivy ainda não criou
    # a pasta.
    if platform == "android":
        root = Path(app_storage_path()) / "DCIM"
    else:
        root = Path(App.get_running_app().user_data_dir)
    root.mkdir(exist_ok=True)
    return root


def capture_location() -> str:
    return "private" if platform == "android" else str(data_dir())


def photos_dir() -> Path:
    folder = data_dir() / PHOTOS_SUBDIR
    folder.mkdir(exist_ok=True)
    return folder


def index_path() -> Path:
    return data_dir() / INDEX_FILENAME
