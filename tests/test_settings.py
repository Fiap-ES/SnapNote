import json
from pathlib import Path

import pytest

import settings

SETTINGS_FILENAME = "settings.json"


@pytest.fixture
def settings_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / SETTINGS_FILENAME
    monkeypatch.setattr(settings, "_path", None)
    settings.use(path)
    return path


def stored(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_timeout_without_any_configuration_is_the_default(settings_file: Path) -> None:
    assert not settings_file.exists()
    assert settings.gemini_timeout() == settings.DEFAULT_TIMEOUT


def test_timeout_without_a_configured_location_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "_path", None)

    assert settings.gemini_timeout() == settings.DEFAULT_TIMEOUT


def test_saved_timeout_is_read_back(settings_file: Path) -> None:
    settings.save_gemini_timeout(25)

    assert settings.gemini_timeout() == 25.0
    assert stored(settings_file) == {settings.GEMINI_TIMEOUT: 25.0}


def test_saved_timeout_survives_a_new_session(settings_file: Path) -> None:
    settings.save_gemini_timeout(42)
    settings.use(settings_file)

    assert settings.gemini_timeout() == 42.0


def test_saving_replaces_the_previous_value(settings_file: Path) -> None:
    settings.save_gemini_timeout(20)
    settings.save_gemini_timeout(30)

    assert settings.gemini_timeout() == 30.0


def test_saving_keeps_the_other_stored_values(settings_file: Path) -> None:
    settings_file.write_text(json.dumps({"outro": "valor"}), encoding="utf-8")

    settings.save_gemini_timeout(20)

    assert stored(settings_file) == {"outro": "valor", settings.GEMINI_TIMEOUT: 20.0}


@pytest.mark.parametrize("seconds", [4.9, 0, -10, 60.1, 300])
def test_timeout_outside_the_range_is_rejected(settings_file: Path, seconds: float) -> None:
    with pytest.raises(ValueError):
        settings.save_gemini_timeout(seconds)

    assert not settings_file.exists()


def test_rejected_timeout_keeps_the_saved_one(settings_file: Path) -> None:
    settings.save_gemini_timeout(20)

    with pytest.raises(ValueError):
        settings.save_gemini_timeout(90)

    assert settings.gemini_timeout() == 20.0


@pytest.mark.parametrize("seconds", [5, 60, 15.5])
def test_timeout_inside_the_range_is_accepted(settings_file: Path, seconds: float) -> None:
    settings.save_gemini_timeout(seconds)

    assert settings.gemini_timeout() == float(seconds)


@pytest.mark.parametrize("content", ['{"gemini_timeout": 900}', '{"gemini_timeout": "vinte"}', "nao e json", "[]"])
def test_unusable_stored_value_falls_back_to_the_default(settings_file: Path, content: str) -> None:
    settings_file.write_text(content, encoding="utf-8")

    assert settings.gemini_timeout() == settings.DEFAULT_TIMEOUT
