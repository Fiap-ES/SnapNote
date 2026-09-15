import logging
import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

# O bootstrap do python-for-android define ANDROID_ARGUMENT no ambiente; é o
# mesmo critério de media_store.py e speech.py, sem trazer o Kivy para a ponte.
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

log = logging.getLogger(__name__)

# Em documentos, o topo (título e cabeçalho) é lido com precisão e o corpo
# com fórmulas vira ruído; a sugestão fica nos primeiros blocos, com um teto
# de caracteres para um bloco anormalmente longo.
MAX_BLOCKS = 3
MAX_CHARS = 160

if ON_ANDROID:
    from android import mActivity
    from android.runnable import run_on_ui_thread
    from jnius import PythonJavaClass, autoclass, cast, java_method

    File = autoclass("java.io.File")
    Uri = autoclass("android.net.Uri")
    InputImage = autoclass("com.google.mlkit.vision.common.InputImage")
    TextRecognition = autoclass("com.google.mlkit.vision.text.TextRecognition")
    TextRecognizerOptions = autoclass("com.google.mlkit.vision.text.latin.TextRecognizerOptions")
    TEXT_CLASS = "com.google.mlkit.vision.text.Text"
    BLOCK_CLASS = "com.google.mlkit.vision.text.Text$TextBlock"

    class RecognitionListener(PythonJavaClass):
        __javacontext__ = "app"
        __javainterfaces__ = [
            "com/google/android/gms/tasks/OnSuccessListener",
            "com/google/android/gms/tasks/OnFailureListener",
        ]

        def __init__(self, image_path: Path, on_result: Callable[[str], None]) -> None:
            super().__init__()
            self._image_path = image_path
            self._on_result = on_result

        @java_method("(Ljava/lang/Object;)V")
        def onSuccess(self, result: object) -> None:
            _finish(self, self._image_path, self._on_result, lambda: summarize(_block_texts(result)))

        @java_method("(Ljava/lang/Exception;)V")
        def onFailure(self, error: object) -> None:
            log.warning("Reconhecimento de texto falhou em %s: %s", self._image_path, error.getMessage())
            _finish(self, self._image_path, self._on_result, lambda: "")

    # getTextBlocks devolve um java.util.List na ordem de leitura do
    # reconhecedor; os itens chegam como Object e precisam do cast para TextBlock.
    def _block_texts(result: object) -> list[str]:
        blocks = cast(TEXT_CLASS, result).getTextBlocks()
        return [cast(BLOCK_CLASS, blocks.get(i)).getText() for i in range(blocks.size())]

else:

    def run_on_ui_thread(function: Callable) -> Callable:
        return function


# O listener precisa de uma referência viva do lado Python enquanto o ML Kit
# o guarda do lado Java.
_pending: set = set()


def available() -> bool:
    return ON_ANDROID


def summarize(blocks: list[str]) -> str:
    return "\n".join(blocks[:MAX_BLOCKS])[:MAX_CHARS].strip()


def recognize_text(image_path: Path, on_result: Callable[[str], None]) -> None:
    # Fora do Android, ou em qualquer falha, o texto é vazio. No Android o
    # resultado chega na thread principal do sistema; quem usa leva-o para a
    # thread da interface.
    if not ON_ANDROID:
        on_result("")
        return
    _start(image_path, on_result)


# Toda chamada JNI fica na thread principal do Android: threads criadas em
# Python resolvem classes pelo class loader do sistema e não enxergam as do
# aplicativo (pyjnius 1.7 não consulta o class loader da aplicação), e uma
# exceção Java pendente numa thread nativa derruba o processo ao desanexá-la.
# O ML Kit faz a inferência em executor próprio e responde nesta mesma thread.
@run_on_ui_thread
def _start(image_path: Path, on_result: Callable[[str], None]) -> None:
    try:
        image = InputImage.fromFilePath(mActivity, Uri.fromFile(File(str(image_path))))
        listener = RecognitionListener(image_path, on_result)
        _pending.add(listener)
        task = _recognizer().process(image)
        task.addOnSuccessListener(listener)
        task.addOnFailureListener(listener)
    except Exception as error:
        log.warning("Reconhecimento de texto não iniciou em %s: %s", image_path, error)
        on_result("")


def _finish(
    listener: object, image_path: Path, on_result: Callable[[str], None], read: Callable[[], str]
) -> None:
    # Uma exceção Python dentro de um callback vindo do Java voltaria ao Java
    # como exceção não capturada na thread principal.
    _pending.discard(listener)
    try:
        text = read()
    except Exception as error:
        log.warning("Leitura do resultado falhou em %s: %s", image_path, error)
        text = ""
    try:
        on_result(text)
    except Exception:
        log.exception("Entrega do texto reconhecido falhou em %s", image_path)


@lru_cache(maxsize=1)
def _recognizer() -> object:
    return TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
