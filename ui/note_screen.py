from collections.abc import Callable
from pathlib import Path

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

import notes
import storage
from ui.thumbnail_loader import ThumbnailLoader

Builder.load_string("""
<NoteScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(16)
        Thumbnail:
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
                text: root.cancel_label
                on_release: root.cancel()
            MDRaisedButton:
                text: "Salvar"
                on_release: root.save()
""")


class NoteScreen(MDScreen):
    photo_path = StringProperty("")
    cancel_label = StringProperty("")

    def __init__(self, previews: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._previews = previews

    def edit(
        self,
        file_path: str,
        text: str,
        cancel_label: str,
        on_saved: Callable[[str, str | None], None],
        on_cancelled: Callable[[str], None],
    ) -> None:
        self.photo_path = file_path
        self.cancel_label = cancel_label
        self._on_saved = on_saved
        self._on_cancelled = on_cancelled
        self._previews.display(file_path, self.ids.thumbnail)
        self.ids.note_field.text = text

    def save(self) -> None:
        note = notes.save_note(
            Path(self.photo_path), self.ids.note_field.text, storage.index_path()
        )
        self._on_saved(self.photo_path, note)

    def cancel(self) -> None:
        self._on_cancelled(self.photo_path)
