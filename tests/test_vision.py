import base64
import io
import json
import logging
import threading
import urllib.error
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import settings
import vision
from tests.conftest import MakeJpeg

KEY = "chave-de-teste"
DELIVERY_TIMEOUT = 5.0


def answer(text: str) -> bytes:
    return json.dumps({"candidates": [{"content": {"parts": [{"text": text}]}}]}).encode("utf-8")


class FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False


@pytest.fixture
def key_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(vision, "KEY_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def env_key(key_dir: Path) -> Path:
    (key_dir / vision.ENV_FILE).write_text(f"OUTRA=1\n{vision.KEY_NAME}={KEY}\n", encoding="utf-8")
    return key_dir


@pytest.fixture
def gemini(monkeypatch: pytest.MonkeyPatch) -> Iterator[SimpleNamespace]:
    fake = SimpleNamespace(calls=[], body=answer("Recibo da farmácia."), error=None)

    def urlopen(request: object, timeout: float | None = None, context: object = None) -> FakeResponse:
        fake.calls.append(SimpleNamespace(request=request, timeout=timeout))
        if fake.error is not None:
            raise fake.error
        return FakeResponse(fake.body)

    monkeypatch.setattr(vision.urllib.request, "urlopen", urlopen)
    yield fake


def describe(image_path: Path) -> str:
    delivered = threading.Event()
    results: list[str] = []

    def collect(text: str) -> None:
        results.append(text)
        delivered.set()

    vision.describe_image(image_path, collect)

    assert delivered.wait(DELIVERY_TIMEOUT)
    return results[0]


def sent_body(fake: SimpleNamespace) -> dict:
    return json.loads(fake.calls[0].request.data.decode("utf-8"))


def sent_image(fake: SimpleNamespace) -> Image.Image:
    part = sent_body(fake)["contents"][0]["parts"][1]["inline_data"]
    return Image.open(io.BytesIO(base64.b64decode(part["data"])))


def test_description_is_delivered(env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg) -> None:
    photo = make_jpeg()

    assert describe(photo) == "Recibo da farmácia."


def test_request_carries_the_key_the_prompt_and_the_image(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    photo = make_jpeg(size=(80, 60))

    describe(photo)

    request = gemini.calls[0].request
    assert request.get_header("X-goog-api-key") == KEY
    parts = sent_body(gemini)["contents"][0]["parts"]
    assert parts[0]["text"] == vision.PROMPT
    assert parts[1]["inline_data"]["mime_type"] == vision.MIME_TYPE
    assert sent_image(gemini).size == (80, 60)


def test_large_photo_is_reduced_and_left_untouched_on_disk(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    photo = make_jpeg(size=(2400, 1800))
    original = photo.read_bytes()

    describe(photo)

    sent = sent_image(gemini)
    assert max(sent.size) == vision.MAX_IMAGE_SIDE
    assert sent.size == (vision.MAX_IMAGE_SIDE, 768)
    assert photo.read_bytes() == original


def test_photo_within_the_limit_is_sent_as_it_is(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    describe(make_jpeg(size=(320, 240)))

    assert sent_image(gemini).size == (320, 240)


def test_call_uses_the_configured_timeout(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "gemini_timeout", lambda: 25.0)

    describe(make_jpeg())

    assert gemini.calls[0].timeout == 25.0


def test_call_without_configuration_uses_the_default_timeout(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "_path", None)

    describe(make_jpeg())

    assert gemini.calls[0].timeout == settings.DEFAULT_TIMEOUT


def test_network_failure_yields_empty_description(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    gemini.error = urllib.error.URLError("sem rota para o destino")

    assert describe(make_jpeg()) == ""


def test_timeout_yields_empty_description(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    gemini.error = TimeoutError("tempo esgotado")

    assert describe(make_jpeg()) == ""


def test_rejected_key_yields_empty_description(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    gemini.error = urllib.error.HTTPError(vision.ENDPOINT, 400, "Bad Request", {}, None)

    assert describe(make_jpeg()) == ""


def test_missing_key_skips_the_call(key_dir: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg) -> None:
    assert vision.available() is False
    assert describe(make_jpeg()) == ""
    assert gemini.calls == []


def test_key_can_come_from_secrets_json(
    key_dir: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    (key_dir / vision.SECRETS_FILE).write_text(json.dumps({vision.KEY_NAME: KEY}), encoding="utf-8")

    assert vision.available() is True
    assert describe(make_jpeg()) == "Recibo da farmácia."
    assert gemini.calls[0].request.get_header("X-goog-api-key") == KEY


def test_broken_secrets_file_is_ignored(key_dir: Path) -> None:
    (key_dir / vision.SECRETS_FILE).write_text("{isto nao e json", encoding="utf-8")

    assert vision.api_key() == ""


def test_invalid_response_yields_empty_description(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    gemini.body = b"<html>erro do servidor</html>"

    assert describe(make_jpeg()) == ""


def test_response_without_candidates_yields_empty_description(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    gemini.body = json.dumps({"promptFeedback": {"blockReason": "SAFETY"}}).encode("utf-8")

    assert describe(make_jpeg()) == ""


def test_description_is_capped_and_kept_in_one_line(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg
) -> None:
    gemini.body = answer("  Nota\nfiscal " + "x" * vision.MAX_CHARS)

    description = describe(make_jpeg())

    assert len(description) == vision.MAX_CHARS
    assert description.startswith("Nota fiscal ")


def test_offline_skips_the_call(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(vision, "_connected", lambda: False)

    assert describe(make_jpeg()) == ""
    assert gemini.calls == []


def test_unreadable_network_state_lets_the_call_decide(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> bool:
        raise RuntimeError("serviço indisponível")

    monkeypatch.setattr(vision, "_connected", broken)

    assert vision.online() is True


def test_failing_consumer_does_not_escape_the_thread(
    env_key: Path, gemini: SimpleNamespace, make_jpeg: MakeJpeg, caplog: pytest.LogCaptureFixture
) -> None:
    called = threading.Event()

    def consumer(_text: str) -> None:
        called.set()
        raise RuntimeError("consumidor quebrado")

    with caplog.at_level(logging.ERROR, logger=vision.__name__):
        vision.describe_image(make_jpeg(), consumer)

        assert called.wait(DELIVERY_TIMEOUT)
