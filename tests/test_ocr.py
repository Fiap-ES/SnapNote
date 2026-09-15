import importlib
import sys
import types
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

import ocr


def test_ocr_is_unavailable_outside_android() -> None:
    assert ocr.ON_ANDROID is False
    assert ocr.available() is False


def test_recognize_text_yields_empty_text_outside_android() -> None:
    results: list[str] = []

    ocr.recognize_text(Path("/nao/existe.jpg"), results.append)

    assert results == [""]


class FakeTask:
    def __init__(self) -> None:
        self.success: object = None
        self.failure: object = None

    def addOnSuccessListener(self, listener: object) -> None:
        self.success = listener

    def addOnFailureListener(self, listener: object) -> None:
        self.failure = listener


class FakeBlock:
    def __init__(self, text: str) -> None:
        self._text = text

    def getText(self) -> str:
        return self._text


class FakeList:
    def __init__(self, items: list) -> None:
        self._items = items

    def size(self) -> int:
        return len(self._items)

    def get(self, index: int) -> object:
        return self._items[index]


class FakeText:
    def __init__(self, *blocks: str, fail: bool = False) -> None:
        self._blocks, self._fail = blocks, fail

    def getTextBlocks(self) -> FakeList:
        if self._fail:
            raise RuntimeError("leitura quebrada")
        return FakeList([FakeBlock(text) for text in self._blocks])


class FakeError:
    def getMessage(self) -> str:
        return "modelo indisponível"


@pytest.fixture
def android_ocr(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[types.ModuleType, FakeTask, dict]]:
    task = FakeTask()
    state = {"open_fails": False}

    def from_file_path(_context: object, _uri: object) -> object:
        if state["open_fails"]:
            raise RuntimeError("arquivo ilegível")
        return object()

    classes = {
        "java.io.File": lambda path: path,
        "android.net.Uri": types.SimpleNamespace(fromFile=lambda file: file),
        "com.google.mlkit.vision.common.InputImage": types.SimpleNamespace(fromFilePath=from_file_path),
        "com.google.mlkit.vision.text.TextRecognition": types.SimpleNamespace(
            getClient=lambda _options: types.SimpleNamespace(process=lambda _image: task)
        ),
        "com.google.mlkit.vision.text.latin.TextRecognizerOptions": types.SimpleNamespace(DEFAULT_OPTIONS=object()),
    }

    class PythonJavaClass:
        def __init__(self) -> None:
            pass

    jnius = types.ModuleType("jnius")
    jnius.PythonJavaClass = PythonJavaClass
    jnius.java_method = lambda _signature: (lambda function: function)
    jnius.autoclass = classes.__getitem__
    jnius.cast = lambda _cls, obj: obj
    android = types.ModuleType("android")
    android.mActivity = object()
    runnable = types.ModuleType("android.runnable")
    runnable.run_on_ui_thread = lambda function: function
    android.runnable = runnable

    monkeypatch.setitem(sys.modules, "jnius", jnius)
    monkeypatch.setitem(sys.modules, "android", android)
    monkeypatch.setitem(sys.modules, "android.runnable", runnable)
    monkeypatch.setenv("ANDROID_ARGUMENT", "1")
    module = importlib.reload(ocr)
    yield module, task, state
    monkeypatch.delenv("ANDROID_ARGUMENT")
    importlib.reload(ocr)


def test_recognized_text_is_delivered(android_ocr: tuple) -> None:
    module, task, _state = android_ocr
    results: list[str] = []

    module.recognize_text(Path("/foto.jpg"), results.append)
    assert results == [] and module._pending
    task.success.onSuccess(FakeText("NOTA FISCAL 123", "Padaria Central"))

    assert results == ["NOTA FISCAL 123\nPadaria Central"] and not module._pending


def test_recognizer_failure_yields_empty_text(android_ocr: tuple) -> None:
    module, task, _state = android_ocr
    results: list[str] = []

    module.recognize_text(Path("/foto.jpg"), results.append)
    task.failure.onFailure(FakeError())

    assert results == [""] and not module._pending


def test_failure_to_start_yields_empty_text_without_raising(android_ocr: tuple) -> None:
    module, _task, state = android_ocr
    state["open_fails"] = True
    results: list[str] = []

    module.recognize_text(Path("/foto.jpg"), results.append)

    assert results == [""]


def test_broken_result_yields_empty_text_without_raising(android_ocr: tuple) -> None:
    module, task, _state = android_ocr
    results: list[str] = []

    module.recognize_text(Path("/foto.jpg"), results.append)
    task.success.onSuccess(FakeText(fail=True))

    assert results == [""]


def test_failing_consumer_does_not_propagate_into_java(android_ocr: tuple) -> None:
    module, task, _state = android_ocr

    def consumer(_text: str) -> None:
        raise RuntimeError("consumidor quebrado")

    module.recognize_text(Path("/foto.jpg"), consumer)
    task.success.onSuccess(FakeText("texto"))


def test_suggestion_keeps_only_the_first_blocks(android_ocr: tuple) -> None:
    module, task, _state = android_ocr
    results: list[str] = []
    blocks = ["Título", "Subtítulo", "Data", "corpo com fórmulas", "mais corpo"]

    module.recognize_text(Path("/foto.jpg"), results.append)
    task.success.onSuccess(FakeText(*blocks))

    assert results == ["\n".join(blocks[: module.MAX_BLOCKS])]
    assert "corpo" not in results[0]


def test_suggestion_is_capped_by_character_limit(android_ocr: tuple) -> None:
    module, task, _state = android_ocr
    results: list[str] = []

    module.recognize_text(Path("/foto.jpg"), results.append)
    task.success.onSuccess(FakeText("x" * (module.MAX_CHARS + 40)))

    assert results == ["x" * module.MAX_CHARS]


def test_result_without_blocks_yields_empty_text(android_ocr: tuple) -> None:
    module, task, _state = android_ocr
    results: list[str] = []

    module.recognize_text(Path("/foto.jpg"), results.append)
    task.success.onSuccess(FakeText())

    assert results == [""]
