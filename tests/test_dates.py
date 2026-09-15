from datetime import date

from ui.dates import section_label

TODAY = date(2026, 9, 14)


def test_today_and_yesterday_are_relative() -> None:
    assert section_label(date(2026, 9, 14), TODAY) == "Hoje"
    assert section_label(date(2026, 9, 13), TODAY) == "Ontem"


def test_other_days_are_spelled_out_in_portuguese() -> None:
    assert section_label(date(2026, 9, 1), TODAY) == "1 de setembro de 2026"
    assert section_label(date(2025, 3, 21), TODAY) == "21 de março de 2025"


def test_missing_date_has_its_own_label() -> None:
    assert section_label(None, TODAY) == "Sem data"
