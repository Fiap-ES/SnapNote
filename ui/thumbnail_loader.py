from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import PIL.Image
from kivy.clock import mainthread
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.image import Image

from thumbnails import upright_thumbnail


class Thumbnail(Image):
    photo_path = StringProperty("")


def texture_from(image: PIL.Image.Image) -> Texture:
    texture = Texture.create(size=image.size, colorfmt="rgb")
    texture.blit_buffer(image.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
    # O Pillow enumera as linhas de cima para baixo; a textura do Kivy tem a
    # origem embaixo.
    texture.flip_vertical()
    return texture


class ThumbnailLoader:
    def __init__(self, max_size: int, max_cached: int | None = None) -> None:
        self._max_size = max_size
        self._max_cached = max_cached
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._images: dict[str, Future[PIL.Image.Image]] = {}

    def display(self, file_path: str, target: Thumbnail) -> None:
        target.photo_path = file_path
        image = self._decode(file_path)
        # Uma imagem já decodificada vira textura na hora: passar pelo Clock
        # deixaria o widget em branco por um quadro a cada troca de foto.
        if image.done() and image.exception() is None:
            target.texture = texture_from(image.result())
            return
        # A decodificação roda em outra thread (o Pillow libera o GIL); a
        # textura, por ser um objeto OpenGL, só pode nascer na thread do Kivy.
        target.texture = None
        image.add_done_callback(lambda done: self._show(target, file_path, done))

    def _decode(self, file_path: str) -> Future[PIL.Image.Image]:
        image = self._images.pop(file_path, None)
        if image is None:
            image = self._executor.submit(upright_thumbnail, Path(file_path), self._max_size)
            # Uma leitura pode falhar se o arquivo estiver sendo reescrito pelo
            # piexif naquele instante; a falha não fica em cache, e a próxima
            # exibição tenta de novo.
            image.add_done_callback(lambda done: self._forget_failure(file_path, done))
        # Reinserir no fim mantém o dicionário em ordem de uso, e o descarte
        # tira sempre a imagem parada há mais tempo.
        self._images[file_path] = image
        self._evict()
        return image

    def _evict(self) -> None:
        while self._max_cached is not None and len(self._images) > self._max_cached:
            self._images.pop(next(iter(self._images)))

    @mainthread
    def _forget_failure(self, file_path: str, done: Future[PIL.Image.Image]) -> None:
        if done.exception() is None:
            return
        Logger.warning("SnapNote: falha ao decodificar %s: %s", file_path, done.exception())
        if self._images.get(file_path) is done:
            self._images.pop(file_path)

    @mainthread
    def _show(self, target: Thumbnail, file_path: str, done: Future[PIL.Image.Image]) -> None:
        # Uma carga antiga pode terminar depois de o widget já ter pedido
        # outra foto.
        if done.exception() is None and target.photo_path == file_path:
            target.texture = texture_from(done.result())
