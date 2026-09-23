from kivy.clock import mainthread
from kivy.properties import BooleanProperty
from kivymd.toast import toast

import speech
from permissions import request_microphone_permission
from speech import SpeechFailure

FAILURE_MESSAGES = {
    SpeechFailure.UNAVAILABLE: "Reconhecimento de voz indisponível neste aparelho.",
    SpeechFailure.NO_SPEECH: "Nenhuma fala detectada.",
    SpeechFailure.PERMISSION_DENIED: "Permissão de microfone negada.",
    SpeechFailure.RECOGNIZER_ERROR: "Falha no reconhecimento de voz.",
}


# O SpeechRecognizer responde na thread principal do Android; widgets só
# podem ser alterados na thread do Kivy.
class DictationBehavior:
    listening = BooleanProperty(False)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._dictation = speech.Dictation(self._on_transcript, self._on_failure)

    def dictate(self) -> None:
        if self.listening:
            self.stop_dictation()
        else:
            self.start_dictation()

    def start_dictation(self) -> None:
        request_microphone_permission(self._on_permission)

    def stop_dictation(self) -> None:
        self.listening = False
        self._dictation.cancel()

    def apply_transcript(self, text: str) -> None:
        raise NotImplementedError

    def _on_permission(self, granted: bool) -> None:
        if not granted:
            toast(FAILURE_MESSAGES[SpeechFailure.PERMISSION_DENIED])
            return
        self.listening = True
        self._dictation.start()

    @mainthread
    def _on_transcript(self, text: str) -> None:
        self.listening = False
        self.apply_transcript(text)

    @mainthread
    def _on_failure(self, failure: SpeechFailure) -> None:
        self.listening = False
        toast(FAILURE_MESSAGES[failure])
