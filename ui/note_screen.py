from collections.abc import Callable
from pathlib import Path

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.toast import toast

import notes
import speech
import storage
from permissions import request_microphone_permission
from speech import SpeechFailure
from ui import dialogs
from ui.thumbnail_loader import ThumbnailLoader
from ui.widgets import SnapScreen

Builder.load_string("""
#:import theme ui.theme

<NoteScreen>:
    md_bg_color: theme.LAYER_0
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(theme.PADDING)
        spacing: dp(theme.PADDING)
        Widget:
        RoundedPhoto:
            id: thumbnail
            size_hint_y: None
            height: root.height * theme.NOTE_IMAGE_SHARE
        MDBoxLayout:
            size_hint_y: None
            height: dp(theme.NOTE_FIELD_HEIGHT)
            spacing: dp(theme.SPACING)
            FieldBox:
                padding: dp(theme.PADDING), dp(theme.SPACING)
                TextInput:
                    id: note_field
                    hint_text: "Ouvindo..." if root.listening else "Anotação"
                    background_normal: ""
                    background_active: ""
                    background_color: theme.TRANSPARENT
                    foreground_color: theme.TEXT
                    hint_text_color: theme.TEXT_MUTED
                    cursor_color: theme.ACCENT
                    font_name: theme.FONT
                    font_size: sp(theme.FONT_BODY)
                    padding: 0
            ToolIcon:
                icon: "microphone"
                pos_hint: {"center_y": .5}
                icon_color: theme.ON_ACCENT if root.listening else theme.TEXT
                md_bg_color: theme.ACCENT if root.listening else theme.TRANSPARENT
                on_release: root.dictate()
        Widget:
        MDBoxLayout:
            adaptive_size: True
            spacing: dp(theme.PADDING)
            pos_hint: {"center_x": .5}
            MDFlatButton:
                text: root.cancel_label
                on_release: root.cancel()
            MDRoundFlatButton:
                text: "Salvar"
                on_release: root.save()
""")

FAILURE_MESSAGES = {
    SpeechFailure.UNAVAILABLE: "Reconhecimento de voz indisponível neste aparelho.",
    SpeechFailure.NO_SPEECH: "Nenhuma fala detectada.",
    SpeechFailure.PERMISSION_DENIED: "Permissão de microfone negada.",
    SpeechFailure.RECOGNIZER_ERROR: "Falha no reconhecimento de voz.",
}


class NoteScreen(SnapScreen):
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
