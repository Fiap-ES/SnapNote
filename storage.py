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
    # existente, papel que o user_data_dir do Kivy cumpre.
    if platform == "android":
        return Path(app_storage_path()) / "DCIM"
    return Path(App.get_running_app().user_data_dir)


def capture_location() -> str:
    return "private" if platform == "android" else str(data_dir())


def index_path() -> Path:
    return data_dir() / INDEX_FILENAME
