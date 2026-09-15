import logging
import os
import threading
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

# O bootstrap do python-for-android define ANDROID_ARGUMENT no ambiente; é o
# mesmo critério de media_store.py e speech.py, sem trazer o Kivy para a ponte.
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

log = logging.getLogger(__name__)

if ON_ANDROID:
    from android import mActivity
    from jnius import JavaException, autoclass, detach

    File = autoclass("java.io.File")
    Uri = autoclass("android.net.Uri")
    InputImage = autoclass("com.google.mlkit.vision.common.InputImage")
    Tasks = autoclass("com.google.android.gms.tasks.Tasks")
    TextRecognition = autoclass("com.google.mlkit.vision.text.TextRecognition")
    TextRecognizerOptions = autoclass("com.google.mlkit.vision.text.latin.TextRecognizerOptions")


def available() -> bool:
    return ON_ANDROID


def recognize_text(image_path: Path, on_result: Callable[[str], None]) -> None:
    # O resultado chega em uma thread própria; quem usa leva-o para a thread
    # da interface. Fora do Android, ou em qualquer falha, o texto é vazio.
    if not ON_ANDROID:
        on_result("")
        return
    threading.Thread(target=_recognize, args=(image_path, on_result), daemon=True).start()


def _recognize(image_path: Path, on_result: Callable[[str], None]) -> None:
    try:
        on_result(_read_text(image_path))
    except JavaException as error:
        log.warning("Reconhecimento de texto falhou em %s: %s", image_path, error)
        on_result("")
    finally:
        detach()


def _read_text(image_path: Path) -> str:
    # fromFilePath aplica a orientação do EXIF. Tasks.await bloqueia só esta
    # thread até o modelo embarcado terminar; "await" é palavra reservada em
    # Python, daí o getattr.
    image = InputImage.fromFilePath(mActivity, Uri.fromFile(File(str(image_path))))
    task = _recognizer().process(image)
    return getattr(Tasks, "await")(task).getText()


@lru_cache(maxsize=1)
def _recognizer() -> object:
    return TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
