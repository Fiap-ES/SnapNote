import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

GEMINI_TIMEOUT = "gemini_timeout"

# O tempo limite cobre o envio da imagem e a geração da frase. Passado isso a
# sugestão chegaria tarde demais para ser útil e o ML Kit assume.
DEFAULT_TIMEOUT = 15.0
MIN_TIMEOUT = 5.0
MAX_TIMEOUT = 60.0

# O índice é um cache reconstruível a partir das fotos; a configuração é do
# usuário e vive em arquivo próprio, ao lado dele.
_path: Path | None = None


def use(path: Path) -> None:
    global _path
    _path = path


def gemini_timeout() -> float:
    seconds = _read().get(GEMINI_TIMEOUT)
    return float(seconds) if _in_range(seconds) else DEFAULT_TIMEOUT


def save_gemini_timeout(seconds: float) -> None:
    if not _in_range(seconds):
        raise ValueError(
            f"Tempo limite fora da faixa de {MIN_TIMEOUT:g} a {MAX_TIMEOUT:g} segundos: {seconds}"
        )
    _store(GEMINI_TIMEOUT, float(seconds))


def _in_range(seconds: object) -> bool:
    return isinstance(seconds, (int, float)) and MIN_TIMEOUT <= seconds <= MAX_TIMEOUT


def _read() -> dict:
    if _path is None or not _path.exists():
        return {}
    try:
        stored = json.loads(_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        log.warning("Configuração ilegível em %s: %s", _path, error)
        return {}
    return stored if isinstance(stored, dict) else {}


def _store(name: str, value: object) -> None:
    if _path is None:
        log.warning("Sem local de configuração definido; %s não foi salvo.", name)
        return
    _path.parent.mkdir(parents=True, exist_ok=True)
    _path.write_text(json.dumps(_read() | {name: value}), encoding="utf-8")
