from collections.abc import Callable
from pathlib import Path

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen

import notes
import speech
import storage
from permissions import request_microphone_permission
from speech import SpeechFailure
from ui import dialogs
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
        MDBoxLayout:
            adaptive_height: True
            spacing: dp(8)
            MDTextField:
                id: note_field
                hint_text: "Ouvindo..." if root.listening else "Anotação"
                mode: "rectangle"
                multiline: True
                max_height: dp(200)
            MDIconButton:
                icon: "microphone"
                pos_hint: {"center_y": .5}
                theme_icon_color: "Custom"
                icon_color: (1, 1, 1, 1) if root.listening else app.theme_cls.primary_color
                md_bg_color: app.theme_cls.error_color if root.listening else (0, 0, 0, 0)
                on_release: root.dictate()
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

FAILURE_MESSAGES = {
    SpeechFailure.UNAVAILABLE: "Reconhecimento de voz indisponível neste aparelho.",
    SpeechFailure.NO_SPEECH: "Nenhuma fala detectada.",
    SpeechFailure.PERMISSION_DENIED: "Permissão de microfone negada.",
    SpeechFailure.RECOGNIZER_ERROR: "Falha no reconhecimento de voz.",
}


class NoteScreen(MDScreen):
    photo_path = StringProperty("")
    cancel_label = StringProperty("")
    listening = BooleanProperty(False)

    def __init__(self, previews: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._previews = previews
        self._dictation = speech.Dictation(self._on_transcript, self._on_dictation_failure)

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

    def dictate(self) -> None:
        if self.listening:
            self.stop_dictation()
        elif self.ids.note_field.text.strip():
            dialogs.confirm(
                "Substituir a anotação atual pelo ditado?", "Substituir", self._request_dictation
            )
        else:
            self._request_dictation()

    def stop_dictation(self) -> None:
        self.listening = False
        self._dictation.cancel()

    # Trocar de tela no meio da escuta cancela o reconhecedor, para que um
    # resultado tardio não caia sobre uma anotação que já não está na tela.
    def on_pre_leave(self) -> None:
        self.stop_dictation()

    def _request_dictation(self) -> None:
        request_microphone_permission(self._start_dictation)

    def _start_dictation(self, granted: bool) -> None:
        if not granted:
            toast(FAILURE_MESSAGES[SpeechFailure.PERMISSION_DENIED])
            return
        self.listening = True
        self._dictation.start()

    # O SpeechRecognizer responde na thread principal do Android; widgets só
    # podem ser alterados na thread do Kivy.
    @mainthread
    def _on_transcript(self, text: str) -> None:
        self.listening = False
        self.ids.note_field.text = text

    @mainthread
    def _on_dictation_failure(self, failure: SpeechFailure) -> None:
        self.listening = False
        toast(FAILURE_MESSAGES[failure])
