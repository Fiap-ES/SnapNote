from kivy.lang import Builder
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.screen import MDScreen

from ui import theme
from ui.thumbnail_loader import Thumbnail

Builder.load_string("""
#:import theme ui.theme
#:import md_icons kivymd.icon_definitions.md_icons

<IconGlyph>:
    text: md_icons.get(self.icon, "")
    font_name: theme.ICON_FONT
    font_size: sp(theme.ICON_SIZE)
    color: theme.TEXT
    size_hint_x: None
    width: self.texture_size[0]

<SnapScreen>:
    md_bg_color: theme.BACKGROUND

<ScreenBar>:
    size_hint_y: None
    height: dp(theme.SCREEN_BAR_HEIGHT)
    padding: dp(theme.SPACING), 0
    ToolIcon:
        icon: "arrow-left"
        pos_hint: {"center_y": .5}
        on_release: root.dispatch("on_back")
    Label:
        text: root.title
        font_name: theme.FONT
        font_size: sp(theme.TITLE_SIZE)
        color: theme.TEXT
        halign: "left"
        valign: "center"
        text_size: self.size
        shorten: True

<Card>:
    md_bg_color: theme.LAYER_1
    radius: [dp(theme.CARD_RADIUS)]

<RowCard>:
    size_hint_y: None
    height: dp(theme.ROW_CARD_HEIGHT)
    padding: dp(theme.PADDING), 0
    spacing: dp(theme.PADDING)

<FieldBox>:
    padding: dp(theme.PADDING), 0
    spacing: dp(theme.SPACING)
    md_bg_color: theme.LAYER_1
    radius: [dp(theme.CARD_RADIUS)]

<TopScrim>:
    canvas:
        Color:
            rgba: theme.TEXT
        Rectangle:
            texture: self.texture
            pos: self.pos
            size: self.size

<RoundedPhoto>:
    fit_mode: "contain"
    color: theme.TEXT if self.texture else theme.TRANSPARENT
    radius: dp(theme.PHOTO_RADIUS)
    canvas.before:
        StencilPush
        RoundedRectangle:
            pos: self.frame[:2]
            size: self.frame[2:]
            radius: [self.radius]
        StencilUse
        Color:
            rgba: theme.TRANSPARENT if self.texture else theme.LAYER_1
        RoundedRectangle:
            pos: self.frame[:2]
            size: self.frame[2:]
            radius: [self.radius]
    canvas.after:
        StencilUnUse
        RoundedRectangle:
            pos: self.frame[:2]
            size: self.frame[2:]
            radius: [self.radius]
        StencilPop

<TextChip>:
    font_name: theme.FONT
    font_size: sp(theme.FONT_SMALL)
    color: theme.ACCENT if self.active else theme.TEXT
    size_hint: None, None
    size: self.texture_size[0] + dp(theme.CHIP_PADDING) * 2, dp(theme.CHIP_HEIGHT)

<ModeChip>:
    font_name: theme.FONT_MODE_ACTIVE if self.active else theme.FONT_MODE
    bold: self.active
    font_size: sp(theme.FONT_MODE_SIZE)

<Pill>:
    canvas.before:
        Color:
            rgba: theme.PILL if self.active else theme.TRANSPARENT
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height / 2]

<ZoomChip>:
    canvas.before:
        Color:
            rgba: theme.PILL if self.active else theme.TRANSPARENT
        Ellipse:
            pos: self.center_x - self.height / 2, self.y
            size: self.height, self.height

<ToolIcon>:
    icon_size: sp(theme.ICON_SIZE)
    theme_icon_color: "Custom"
    icon_color: theme.TEXT
    md_bg_color: theme.TRANSPARENT

<ShutterButton>:
    size_hint: None, None
    size: dp(theme.SHUTTER_SIZE), dp(theme.SHUTTER_SIZE)
    canvas:
        Color:
            rgba: theme.TEXT
        Line:
            circle: self.center_x, self.center_y, self.width / 2 - dp(theme.SHUTTER_OUTER_RING) / 2
            width: dp(theme.SHUTTER_OUTER_RING)
        Color:
            rgba: theme.ACCENT
        Line:
            circle: self.center_x, self.center_y, self.width / 2 - dp(theme.SHUTTER_OUTER_RING + theme.SHUTTER_GAP) - dp(theme.SHUTTER_INNER_RING) / 2
            width: dp(theme.SHUTTER_INNER_RING)
""")


class SnapScreen(MDScreen):
    pass


class ScreenBar(MDBoxLayout):
    __events__ = ("on_back",)
    title = StringProperty("")

    def on_back(self) -> None:
        pass


class Card(MDBoxLayout):
    pass


class RowCard(Card):
    pass


class FieldBox(MDBoxLayout):
    pass


class TopScrim(Widget):
    texture = ObjectProperty(None)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.texture = _vertical_gradient(theme.TRANSPARENT, theme.SCRIM_TOP)


# Dois texels com filtragem linear bastam para um degradê vertical suave;
# a textura do Kivy começa pela linha de baixo.
def _vertical_gradient(bottom: tuple, top: tuple) -> Texture:
    texture = Texture.create(size=(1, 2), colorfmt="rgba")
    pixels = bytes(round(channel * 255) for color in (bottom, top) for channel in color)
    texture.blit_buffer(pixels, colorfmt="rgba", bufferfmt="ubyte")
    return texture


class RoundedPhoto(Thumbnail):
    radius = NumericProperty(0)
    frame = ListProperty([0, 0, 0, 0])

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.bind(pos=self._update_frame, size=self._update_frame, texture=self._update_frame)
        self._update_frame()

    # O recorte segue o retângulo em que a imagem é desenhada: em "contain"
    # ela é menor que o widget; em "cover", maior, e o recorte para na borda.
    def _update_frame(self, *_args: object) -> None:
        width = min(self.norm_image_size[0], self.width)
        height = min(self.norm_image_size[1], self.height)
        self.frame = [self.center_x - width / 2, self.center_y - height / 2, width, height]


class IconGlyph(Label):
    icon = StringProperty("")


class TextChip(ButtonBehavior, Label):
    active = BooleanProperty(False)


class Pill(TextChip):
    pass


class ZoomChip(TextChip):
    pass


class ModeChip(TextChip):
    pass


class ToolIcon(MDIconButton):
    pass


class ShutterButton(ButtonBehavior, Widget):
    pass
