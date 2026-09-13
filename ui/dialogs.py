from collections.abc import Callable

from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField


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


def prompt(title: str, initial: str, action_label: str, on_submit: Callable[[str], None]) -> None:
    field = MDTextField(text=initial, hint_text=title)

    def submit(_button: MDFlatButton) -> None:
        dialog.dismiss()
        if field.text.strip():
            on_submit(field.text)

    dialog = MDDialog(
        title=title,
        type="custom",
        content_cls=field,
        buttons=[
            MDFlatButton(text="Cancelar", on_release=lambda _button: dialog.dismiss()),
            MDFlatButton(text=action_label, on_release=submit),
        ],
    )
    dialog.open()
