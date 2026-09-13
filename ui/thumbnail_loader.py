from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import PIL.Image
from kivy.clock import mainthread
from kivy.graphics.texture import Texture
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
    def __init__(self, max_size: int) -> None:
        self._max_size = max_size
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._images: dict[str, Future[PIL.Image.Image]] = {}

    def display(self, file_path: str, target: Thumbnail) -> None:
        # A decodificação roda em outra thread (o Pillow libera o GIL); a
        # textura, por ser um objeto OpenGL, só pode nascer na thread do Kivy.
        target.photo_path = file_path
        target.texture = None
        self._decode(file_path).add_done_callback(
            lambda done: self._show(target, file_path, done.result())
        )

    def _decode(self, file_path: str) -> Future[PIL.Image.Image]:
        if file_path not in self._images:
            self._images[file_path] = self._executor.submit(
                upright_thumbnail, Path(file_path), self._max_size
            )
        return self._images[file_path]

    @mainthread
    def _show(self, target: Thumbnail, file_path: str, image: PIL.Image.Image) -> None:
        # Uma carga antiga pode terminar depois de o widget já ter pedido
        # outra foto.
        if target.photo_path == file_path:
            target.texture = texture_from(image)
