from kivy.animation import Animation
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.card import MDCard

from ui import theme
from ui.note_editor import NoteEditor
from ui.widgets import OverlayBehavior

Builder.load_string("""
#:import theme ui.theme

<NotePanel>:
    orientation: "vertical"
    size_hint: None, None
    adaptive_height: True
    radius: [dp(theme.NOTE_PANEL_RADIUS)]
    md_bg_color: theme.ISLAND
    elevation: theme.ISLAND_ELEVATION
    padding: dp(theme.PADDING), dp(theme.SPACING)
    spacing: dp(theme.SPACING)
    opacity: 0
    MDBoxLayout:
        adaptive_height: True
        MDFlatButton:
            text: "Cancelar"
            on_release: root.dispatch("on_cancel")
        Widget:
        MDRoundFlatButton:
            text: "Salvar"
            on_release: root.dispatch("on_save", editor.text)
    MDLabel:
        text: root.caption
        font_name: theme.FONT
        font_size: sp(theme.FONT_SMALL)
        theme_text_color: "Custom"
        text_color: theme.ACCENT
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1] if self.text else 0
    NoteEditor:
        id: editor
        size_hint_y: None
        height: dp(theme.NOTE_PANEL_FIELD_HEIGHT)
""")


# Os botões ficam acima do campo de propósito: no Android o sistema desloca
# a janela até o campo focado encostar no teclado, e assim tudo o que está
# acima dele permanece visível.
class NotePanel(OverlayBehavior, MDCard):
    __events__ = ("on_save", "on_cancel")
    caption = StringProperty("")

    def open(self, text: str, caption: str = "") -> None:
        editor = self.ids.editor
        editor.text = text
        self.caption = caption
        self.y = dp(theme.PADDING) - dp(theme.ISLAND_SLIDE)
        self.shown = True
        slide = Animation(y=dp(theme.PADDING), opacity=1, d=theme.ISLAND_DURATION, t="out_quad")
        slide.bind(on_complete=lambda *_args: editor.focus())
        slide.start(self)

    def suggest(self, text: str, caption: str) -> None:
        if not self.ids.editor.text:
            self.ids.editor.text = text
            self.caption = caption

    def close(self) -> None:
        Animation.cancel_all(self)
        self.ids.editor.stop_dictation()
        self.ids.editor.blur()
        self.opacity = 0
        self.shown = False

    def on_save(self, text: str) -> None:
        pass

    def on_cancel(self) -> None:
        pass
