from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from ui import dialogs
from ui.dictation import DictationBehavior

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


class NoteEditor(DictationBehavior, MDBoxLayout):
    text = StringProperty("")

    def focus(self) -> None:
        self.ids.note_field.focus = True

    def blur(self) -> None:
        self.ids.note_field.focus = False

    # Uma anotação escrita não se perde sem confirmação; a busca, sim.
    def dictate(self) -> None:
        if not self.listening and self.text.strip():
            dialogs.confirm(
                "Substituir a anotação atual pelo ditado?", "Substituir", self.start_dictation
            )
            return
        super().dictate()

    def apply_transcript(self, text: str) -> None:
        self.text = text
