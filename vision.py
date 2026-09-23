import base64
import io
import json
import logging
import os
import ssl
import threading
import urllib.request
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import settings
import thumbnails

# O bootstrap do python-for-android define ANDROID_ARGUMENT no ambiente; é o
# mesmo critério de ocr.py e speech.py, sem trazer o Kivy para esta ponte.
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

log = logging.getLogger(__name__)

MODEL = "gemini-3.6-flash"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
MIME_TYPE = "image/jpeg"

MAX_OUTPUT_TOKENS = 120
MAX_CHARS = 200

# Um modelo de visão não aproveita a resolução de uma captura de 12 MP, e os
# megabytes dela estourariam o tempo limite em rede móvel.
MAX_IMAGE_SIDE = 1024
JPEG_QUALITY = 85

PROMPT = (
    "Descreva esta foto em uma única frase curta e objetiva, em português do Brasil, "
    "adequada para servir de anotação da foto. Se houver texto legível na imagem, "
    "privilegie o conteúdo desse texto. Responda apenas com a frase, sem aspas."
)

KEY_NAME = "GEMINI_API_KEY"
KEY_DIR = Path(__file__).resolve().parent
ENV_FILE = ".env"
SECRETS_FILE = "secrets.json"

if ON_ANDROID:
    from android import mActivity
    from jnius import autoclass, cast

    Context = autoclass("android.content.Context")
    NetworkCapabilities = autoclass("android.net.NetworkCapabilities")
    CONNECTIVITY_MANAGER = "android.net.ConnectivityManager"

    def _connected() -> bool:
        service = mActivity.getSystemService(Context.CONNECTIVITY_SERVICE)
        manager = cast(CONNECTIVITY_MANAGER, service)
        network = manager.getActiveNetwork()
        if network is None:
            return False
        capabilities = manager.getNetworkCapabilities(network)
        return capabilities is not None and capabilities.hasCapability(
            NetworkCapabilities.NET_CAPABILITY_INTERNET
        )

else:

    def _connected() -> bool:
        return True


def api_key() -> str:
    return _key_from_env(KEY_DIR / ENV_FILE) or _key_from_secrets(KEY_DIR / SECRETS_FILE)


def available() -> bool:
    return bool(api_key())


def online() -> bool:
    # Fora do Android, ou quando o estado da rede não pode ser lido, quem
    # decide é a própria chamada: sem rede ela falha de imediato.
    try:
        return _connected()
    except Exception as error:
        log.warning("Estado da rede indisponível: %s", error)
        return True


def describe_image(image_path: Path, on_result: Callable[[str], None]) -> None:
    # Sem chave ou sem rede não há tentativa; a descrição vazia diz a quem
    # chamou que não há sugestão vinda do modelo.
    if not available() or not online():
        on_result("")
        return
    threading.Thread(target=_describe, args=(image_path, on_result), daemon=True).start()


def _describe(image_path: Path, on_result: Callable[[str], None]) -> None:
    # Falha de rede, tempo limite e resposta inesperada terminam todos em
    # descrição vazia: esta thread não pode deixar exceção escapar.
    try:
        description = _request_description(image_path)
    except Exception as error:
        log.warning("Descrição de %s indisponível: %s", image_path.name, error)
        description = ""
    try:
        on_result(description)
    except Exception:
        log.exception("Entrega da descrição falhou em %s", image_path.name)


def _request_description(image_path: Path) -> str:
    request = urllib.request.Request(
        ENDPOINT,
        data=_body(image_path),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key()},
    )
    timeout = settings.gemini_timeout()
    with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _description(payload)


def _body(image_path: Path) -> bytes:
    image = _encoded_image(image_path)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": PROMPT},
                    {"inline_data": {"mime_type": MIME_TYPE, "data": image}},
                ]
            }
        ],
        # O raciocínio do modelo acrescentaria segundos a uma resposta de uma
        # frase só; desligado, a sugestão chega dentro do tempo limite.
        "generationConfig": {
            "thinkingConfig": {"thinkingBudget": 0},
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }
    return json.dumps(payload).encode("utf-8")


# A redução acontece só em memória: a foto no cartão continua em resolução
# total, e a cópia enviada vai sem os metadados do original.
def _encoded_image(image_path: Path) -> str:
    buffer = io.BytesIO()
    reduced = thumbnails.upright_thumbnail(image_path, MAX_IMAGE_SIDE)
    reduced.save(buffer, "JPEG", quality=JPEG_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _description(payload: dict) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        log.warning("Resposta do modelo sem descrição: %s", payload)
        return ""
    parts = candidates[0].get("content", {}).get("parts") or []
    return _shorten("".join(part.get("text", "") for part in parts))


def _shorten(text: str) -> str:
    return " ".join(text.split())[:MAX_CHARS].strip()


def _key_from_env(path: Path) -> str:
    for line in _read(path).splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == KEY_NAME:
            return value.strip().strip("\"'")
    return ""


def _key_from_secrets(path: Path) -> str:
    content = _read(path)
    if not content:
        return ""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        log.warning("%s não é um JSON válido; a chave foi ignorada.", path.name)
        return ""
    key = data.get(KEY_NAME) if isinstance(data, dict) else None
    return key.strip() if isinstance(key, str) else ""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


@lru_cache(maxsize=1)
def _ssl_context() -> ssl.SSLContext:
    # No Android não existe o pacote de certificados que o OpenSSL procura
    # por padrão; o do certifi vai embarcado no aplicativo.
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())
