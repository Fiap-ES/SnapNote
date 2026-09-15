from datetime import date, timedelta

MONTHS = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)
UNDATED = "Sem data"


def section_label(day: date | None, today: date) -> str:
    if day is None:
        return UNDATED
    if day == today:
        return "Hoje"
    if day == today - timedelta(days=1):
        return "Ontem"
    return f"{day.day} de {MONTHS[day.month - 1]} de {day.year}"
