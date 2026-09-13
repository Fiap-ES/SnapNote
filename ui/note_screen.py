from pathlib import Path

import PIL.Image
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

import notes
import storage
from thumbnails import upright_thumbnail

THUMBNAIL_MAX_SIZE = 1024

Builder.load_string("""
<NoteScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(16)
        Image:
            id: thumbnail
            fit_mode: "contain"
        MDTextField:
            id: note_field
            hint_text: "Anotação"
            mode: "rectangle"
            multiline: True
            max_height: dp(200)
        MDBoxLayout:
            adaptive_size: True
            spacing: dp(16)
            pos_hint: {"center_x": .5}
            MDFlatButton:
                text: "Descartar"
                on_release: root.discard()
            MDRaisedButton:
                text: "Salvar"
                on_release: root.save()
""")


def texture_from(image: PIL.Image.Image) -> Texture:
    texture = Texture.create(size=image.size, colorfmt="rgb")
    texture.blit_buffer(image.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
    # O Pillow enumera as linhas de cima para baixo; a textura do Kivy tem a
    # origem embaixo.
    texture.flip_vertical()
    return texture


class NoteScreen(MDScreen):
    __events__ = ("on_finished",)
    photo_path = StringProperty("")

    def show_photo(self, file_path: str) -> None:
        self.photo_path = file_path
        thumbnail = upright_thumbnail(Path(file_path), THUMBNAIL_MAX_SIZE)
        self.ids.thumbnail.texture = texture_from(thumbnail)
        self.ids.note_field.text = ""

    def save(self) -> None:
        notes.save_note(Path(self.photo_path), self.ids.note_field.text, storage.index_path())
        self.dispatch("on_finished")

    def discard(self) -> None:
        notes.discard_photo(Path(self.photo_path))
        self.dispatch("on_finished")

    def on_finished(self) -> None:
        pass
