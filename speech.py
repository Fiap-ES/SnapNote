import os
from collections.abc import Callable
from enum import Enum

# O bootstrap do python-for-android define ANDROID_ARGUMENT no ambiente; é o
# mesmo critério de media_store.py, sem trazer o Kivy para esta ponte.
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

LANGUAGE = "pt-BR"


class SpeechFailure(Enum):
    UNAVAILABLE = "unavailable"
    NO_SPEECH = "no_speech"
    PERMISSION_DENIED = "permission_denied"
    RECOGNIZER_ERROR = "recognizer_error"


if ON_ANDROID:
    from android import mActivity
    from android.runnable import run_on_ui_thread
    from jnius import PythonJavaClass, autoclass, java_method

    Intent = autoclass("android.content.Intent")
    RecognizerIntent = autoclass("android.speech.RecognizerIntent")
    SpeechRecognizer = autoclass("android.speech.SpeechRecognizer")

    FAILURES_BY_CODE = {
        SpeechRecognizer.ERROR_NO_MATCH: SpeechFailure.NO_SPEECH,
        SpeechRecognizer.ERROR_SPEECH_TIMEOUT: SpeechFailure.NO_SPEECH,
        SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS: SpeechFailure.PERMISSION_DENIED,
    }

    class RecognitionListener(PythonJavaClass):
        __javacontext__ = "app"
        __javainterfaces__ = ["android/speech/RecognitionListener"]

        def __init__(self, dictation: "Dictation") -> None:
            super().__init__()
            self._dictation = dictation

        @java_method("(Landroid/os/Bundle;)V")
        def onReadyForSpeech(self, params: object) -> None:
            pass

        @java_method("()V")
        def onBeginningOfSpeech(self) -> None:
            pass

        @java_method("(F)V")
        def onRmsChanged(self, rms: float) -> None:
            pass

        @java_method("([B)V")
        def onBufferReceived(self, buffer: object) -> None:
            pass

        @java_method("()V")
        def onEndOfSpeech(self) -> None:
            pass

        @java_method("(I)V")
        def onError(self, code: int) -> None:
            self._dictation.finish_with_error(code)

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(self, results: object) -> None:
            self._dictation.finish_with_results(results)

        @java_method("(Landroid/os/Bundle;)V")
        def onPartialResults(self, partial: object) -> None:
            pass

        @java_method("(ILandroid/os/Bundle;)V")
        def onEvent(self, event_type: int, params: object) -> None:
            pass

else:

    def run_on_ui_thread(function: Callable) -> Callable:
        return function


def available() -> bool:
    return ON_ANDROID and SpeechRecognizer.isRecognitionAvailable(mActivity)


class Dictation:
    # Todas as chamadas ao SpeechRecognizer precisam da thread principal do
    # Android, e é nela — não na do Kivy — que os callbacks chegam. Quem usa
    # esta classe deve levar on_result e on_failure para a própria thread.
    def __init__(
        self,
        on_result: Callable[[str], None],
        on_failure: Callable[[SpeechFailure], None],
    ) -> None:
        self._on_result = on_result
        self._on_failure = on_failure
        self._recognizer = None
        self._listener = None

    def start(self) -> None:
        if not available():
            self._on_failure(SpeechFailure.UNAVAILABLE)
            return
        self._listen()

    def cancel(self) -> None:
        self._release()

    def finish_with_results(self, bundle: object) -> None:
        results = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
        self._destroy()
        if results is None or results.size() == 0:
            self._on_failure(SpeechFailure.NO_SPEECH)
        else:
            self._on_result(results.get(0))

    def finish_with_error(self, code: int) -> None:
        self._destroy()
        self._on_failure(FAILURES_BY_CODE.get(code, SpeechFailure.RECOGNIZER_ERROR))

    @run_on_ui_thread
    def _listen(self) -> None:
        self._destroy()
        # O listener precisa de uma referência viva do lado Python: o proxy
        # do pyjnius não sobrevive só por estar registrado no Java.
        self._listener = RecognitionListener(self)
        self._recognizer = SpeechRecognizer.createSpeechRecognizer(mActivity)
        self._recognizer.setRecognitionListener(self._listener)
        self._recognizer.startListening(_recognition_intent())

    @run_on_ui_thread
    def _release(self) -> None:
        self._destroy()

    def _destroy(self) -> None:
        if self._recognizer is not None:
            self._recognizer.destroy()
            self._recognizer = None


def _recognition_intent() -> object:
    intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
    intent.putExtra(
        RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
    )
    intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, LANGUAGE)
    intent.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, mActivity.getPackageName())
    return intent
