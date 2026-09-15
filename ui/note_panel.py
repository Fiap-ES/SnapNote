from kivy.animation import Animation
from kivy.lang import Builder
from kivy.metrics import dp
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

    def open(self, text: str) -> None:
        editor = self.ids.editor
        editor.text = text
        self.y = dp(theme.PADDING) - dp(theme.ISLAND_SLIDE)
        self.shown = True
        slide = Animation(y=dp(theme.PADDING), opacity=1, d=theme.ISLAND_DURATION, t="out_quad")
        slide.bind(on_complete=lambda *_args: editor.focus())
        slide.start(self)

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
