from speech import SpeechFailure
from ui.dictation import FAILURE_MESSAGES


def test_every_failure_has_a_message() -> None:
    assert set(FAILURE_MESSAGES) == set(SpeechFailure)
