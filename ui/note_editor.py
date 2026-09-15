from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout

import speech
from permissions import request_microphone_permission
from speech import SpeechFailure
from ui import dialogs

Builder.load_string("""
#:import theme ui.theme

<NoteEditor>:
    spacing: dp(theme.SPACING)
    FieldBox:
        padding: dp(theme.PADDING), dp(theme.SPACING)
        TextInput:
            id: note_field
            text: root.text
            on_text: root.text = self.text
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
""")

FAILURE_MESSAGES = {
    SpeechFailure.UNAVAILABLE: "Reconhecimento de voz indisponível neste aparelho.",
    SpeechFailure.NO_SPEECH: "Nenhuma fala detectada.",
    SpeechFailure.PERMISSION_DENIED: "Permissão de microfone negada.",
    SpeechFailure.RECOGNIZER_ERROR: "Falha no reconhecimento de voz.",
}


class NoteEditor(MDBoxLayout):
    text = StringProperty("")
    listening = BooleanProperty(False)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._dictation = speech.Dictation(self._on_transcript, self._on_dictation_failure)

    def focus(self) -> None:
        self.ids.note_field.focus = True

    def blur(self) -> None:
        self.ids.note_field.focus = False

    def dictate(self) -> None:
        if self.listening:
            self.stop_dictation()
        elif self.text.strip():
            dialogs.confirm(
                "Substituir a anotação atual pelo ditado?", "Substituir", self._request_dictation
            )
        else:
            self._request_dictation()

    def stop_dictation(self) -> None:
        self.listening = False
        self._dictation.cancel()

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
        self.text = text

    @mainthread
    def _on_dictation_failure(self, failure: SpeechFailure) -> None:
        self.listening = False
        toast(FAILURE_MESSAGES[failure])
