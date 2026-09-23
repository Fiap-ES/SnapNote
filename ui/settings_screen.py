from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.toast import toast

import settings
from ui.widgets import SnapScreen

Builder.load_string("""
#:import theme ui.theme

<SettingsScreen>:
    md_bg_color: theme.LAYER_0
    MDBoxLayout:
        orientation: "vertical"
        ScreenBar:
            title: "Configurações"
            on_back: root.dispatch("on_back")
        MDBoxLayout:
            orientation: "vertical"
            adaptive_height: True
            padding: dp(theme.PADDING)
            spacing: dp(theme.PADDING)
            Card:
                orientation: "vertical"
                adaptive_height: True
                padding: dp(theme.PADDING)
                spacing: dp(theme.SPACING)
                Label:
                    text: "Tempo limite da descrição por IA"
                    font_name: theme.FONT_REGULAR
                    font_size: sp(theme.FONT_BODY)
                    color: theme.TEXT
                    halign: "left"
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                Label:
                    text: root.hint
                    font_name: theme.FONT
                    font_size: sp(theme.FONT_SMALL)
                    color: theme.TEXT_MUTED
                    halign: "left"
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                FieldBox:
                    size_hint_y: None
                    height: dp(theme.SEARCH_HEIGHT)
                    radius: [self.height / 2]
                    md_bg_color: theme.LAYER_0
                    TextInput:
                        id: timeout_field
                        input_filter: "float"
                        input_type: "number"
                        multiline: False
                        write_tab: False
                        background_normal: ""
                        background_active: ""
                        background_color: theme.TRANSPARENT
                        foreground_color: theme.TEXT
                        cursor_color: theme.ACCENT
                        font_name: theme.FONT
                        font_size: sp(theme.FONT_BODY)
                        padding: 0, (self.height - self.line_height) / 2
                    Label:
                        text: "segundos"
                        font_name: theme.FONT
                        font_size: sp(theme.FONT_SMALL)
                        color: theme.TEXT_MUTED
                        size_hint_x: None
                        width: self.texture_size[0]
            MDRoundFlatButton:
                text: "Salvar"
                pos_hint: {"center_x": .5}
                on_release: root.save()
        Widget:
""")

SAVED_MESSAGE = "Tempo limite salvo."
RANGE_HINT = f"Entre {settings.MIN_TIMEOUT:g} e {settings.MAX_TIMEOUT:g} segundos."
INVALID_MESSAGE = f"Valor inválido. {RANGE_HINT}"


def seconds_text(seconds: float) -> str:
    return f"{seconds:g}"


class SettingsScreen(SnapScreen):
    __events__ = ("on_back",)
    hint = StringProperty(RANGE_HINT)

    def refresh(self) -> None:
        self.ids.timeout_field.text = seconds_text(settings.gemini_timeout())

    # Campo vazio e valor fora da faixa chegam aqui como o mesmo ValueError,
    # de float() ou do próprio módulo de configuração.
    def save(self) -> None:
        try:
            settings.save_gemini_timeout(float(self.ids.timeout_field.text))
        except ValueError:
            toast(INVALID_MESSAGE)
            return
        self.refresh()
        toast(SAVED_MESSAGE)

    def on_back(self) -> None:
        pass
