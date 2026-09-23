from ui.camera_screen import SUGGESTION_CAPTION, WAITING_CAPTION, suggestion_caption


def test_panel_announces_the_suggestion_still_being_generated() -> None:
    assert suggestion_caption(True, "") == WAITING_CAPTION


def test_arrived_suggestion_replaces_the_notice_with_the_usual_caption() -> None:
    assert suggestion_caption(False, "Recibo da farmácia, R$ 42,90.") == SUGGESTION_CAPTION


def test_suggestion_that_never_came_leaves_the_panel_without_caption() -> None:
    assert suggestion_caption(False, "") == ""
