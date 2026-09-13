from pathlib import Path

from PIL import Image, ImageOps


def upright_thumbnail(image_path: Path, max_size: int) -> Image.Image:
    # A câmera grava a foto em resolução total e guarda a rotação apenas na
    # tag Orientation do EXIF, que o Kivy ignora. thumbnail() decodifica o
    # JPEG já reduzido e exif_transpose aplica a rotação sobre a miniatura.
    with Image.open(image_path) as image:
        image.thumbnail((max_size, max_size))
        return ImageOps.exif_transpose(image).convert("RGB")
