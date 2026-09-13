from collections.abc import Callable

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog


def confirm(text: str, action_label: str, on_confirm: Callable[[], None]) -> None:
    def run(_button: MDFlatButton) -> None:
        dialog.dismiss()
        on_confirm()

    dialog = MDDialog(
        text=text,
        buttons=[
            MDFlatButton(text="Cancelar", on_release=lambda _button: dialog.dismiss()),
            MDFlatButton(text=action_label, on_release=run),
        ],
    )
    dialog.open()


def progress(text: str) -> MDDialog:
    dialog = MDDialog(text=text, auto_dismiss=False)
    dialog.open()
    return dialog
