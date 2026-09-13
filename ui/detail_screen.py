from pathlib import Path

from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen

import library
import storage
from core.index import IndexedPhoto
from ui import dialogs
from ui.thumbnail_loader import ThumbnailLoader

NO_NOTE_TEXT = "Sem anotação"

Builder.load_string("""
<DetailScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Foto"
            left_action_items: [["arrow-left", lambda _button: root.dispatch("on_back")]]
            right_action_items:
                [["pencil", lambda _button: root.dispatch("on_edit_requested", root.photo)],
                ["delete", lambda _button: root.confirm_delete()]]
        Thumbnail:
            id: image
            fit_mode: "contain"
            size_hint_y: 0.6
        MDScrollView:
            MDLabel:
                id: note_label
                adaptive_height: True
                padding: dp(16), dp(16)
""")


class DetailScreen(MDScreen):
    __events__ = ("on_edit_requested", "on_deleted", "on_back")
    photo = ObjectProperty(None)

    def __init__(self, previews: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._previews = previews

    def show(self, photo: IndexedPhoto) -> None:
        self.photo = photo
        label = self.ids.note_label
        label.text = NO_NOTE_TEXT if photo.note is None else photo.note
        label.theme_text_color = "Hint" if photo.note is None else "Primary"
        self._previews.display(photo.path, self.ids.image)

    def confirm_delete(self) -> None:
        dialogs.confirm("Excluir esta foto?", "Excluir", self.delete)

    def delete(self) -> None:
        library.delete_photo(Path(self.photo.path), storage.index_path())
        self.dispatch("on_deleted")

    def on_edit_requested(self, photo: IndexedPhoto) -> None:
        pass

    def on_deleted(self) -> None:
        pass

    def on_back(self) -> None:
        pass
