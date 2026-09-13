import speech


def test_speech_is_unavailable_outside_android() -> None:
    assert speech.ON_ANDROID is False
    assert speech.available() is False


def test_start_reports_unavailable_instead_of_raising() -> None:
    results: list[str] = []
    failures: list[speech.SpeechFailure] = []
    dictation = speech.Dictation(results.append, failures.append)

    dictation.start()
    dictation.cancel()

    assert results == []
    assert failures == [speech.SpeechFailure.UNAVAILABLE]
