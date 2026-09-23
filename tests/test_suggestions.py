from collections.abc import Callable
from pathlib import Path

import pytest

import suggestions

PHOTO = Path("/fotos/foto.jpg")


def fake_source(text: str, calls: list) -> Callable[[Path, Callable[[str], None]], None]:
    def source(image_path: Path, on_result: Callable[[str], None]) -> None:
        calls.append(image_path)
        on_result(text)

    return source


@pytest.fixture
def sources(monkeypatch: pytest.MonkeyPatch) -> dict:
    calls: dict = {"vision": [], "ocr": []}

    def use(description: str, recognized: str) -> None:
        monkeypatch.setattr(suggestions.vision, "describe_image", fake_source(description, calls["vision"]))
        monkeypatch.setattr(suggestions.ocr, "recognize_text", fake_source(recognized, calls["ocr"]))

    calls["use"] = use
    return calls


def suggest(image_path: Path = PHOTO) -> list[str]:
    results: list[str] = []
    suggestions.suggest_note(image_path, results.append)
    return results


def test_description_is_preferred_over_the_recognized_text(sources: dict) -> None:
    sources["use"]("Prateleira de parafusos numerados.", "PARAFUSO M6")

    assert suggest() == ["Prateleira de parafusos numerados."]
    assert sources["ocr"] == []


def test_failed_description_falls_back_to_the_recognized_text(sources: dict) -> None:
    sources["use"]("", "NOTA FISCAL 123")

    assert suggest() == ["NOTA FISCAL 123"]
    assert sources["ocr"] == [PHOTO]


def test_both_sources_empty_yields_no_suggestion(sources: dict) -> None:
    sources["use"]("", "")

    assert suggest() == [""]


def test_each_source_receives_the_captured_photo(sources: dict) -> None:
    sources["use"]("", "texto")
    photo = Path("/fotos/outra.jpg")

    suggest(photo)

    assert sources["vision"] == [photo] and sources["ocr"] == [photo]


def test_without_key_or_android_the_suggestion_is_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(suggestions.vision, "KEY_DIR", tmp_path)

    assert suggest() == [""]
