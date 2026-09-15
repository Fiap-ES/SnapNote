from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from ui import theme
from ui.widgets import RoundedPhoto

Builder.load_string("""
#:import theme ui.theme

<StripCell>:
    fit_mode: "cover"
    radius: dp(theme.THUMB_RADIUS)
    active: self.strip is not None and self.strip.current == self.position
    color: (theme.TEXT if self.active else theme.STRIP_DIM) if self.texture else theme.TRANSPARENT
    canvas.after:
        Color:
            rgba: theme.ACCENT if self.active else theme.TRANSPARENT
        Line:
            rounded_rectangle: (self.x + dp(theme.STRIP_OUTLINE) / 2, self.y + dp(theme.STRIP_OUTLINE) / 2, self.width - dp(theme.STRIP_OUTLINE), self.height - dp(theme.STRIP_OUTLINE), dp(theme.THUMB_RADIUS))
            width: dp(theme.STRIP_OUTLINE)

<ThumbnailStrip>:
    size_hint_y: None
    height: dp(theme.STRIP_THUMB)
    do_scroll_y: False
    bar_width: 0
    viewclass: "StripCell"
    RecycleBoxLayout:
        orientation: "horizontal"
        size_hint_x: None
        width: self.minimum_width
        default_size: dp(theme.STRIP_THUMB), dp(theme.STRIP_THUMB)
        default_size_hint: None, None
        spacing: dp(theme.STRIP_SPACING)
        padding: (root.width - dp(theme.STRIP_THUMB)) / 2, 0
""")


class StripCell(RecycleDataViewBehavior, ButtonBehavior, RoundedPhoto):
    strip = ObjectProperty(None, rebind=True)
    position = NumericProperty(-1)
    active = BooleanProperty(False)

    def refresh_view_attrs(self, strip: "ThumbnailStrip", index: int, data: dict[str, object]) -> None:
        # O RecycleView redistribui as células a cada mudança nos dados; a
        # que recebe a mesma foto de antes não precisa recarregar nada.
        changed = data["photo_path"] != self.photo_path
        super().refresh_view_attrs(strip, index, data)
        self.strip = strip
        self.position = index
        if changed:
            strip.loader.display(data["photo_path"], self)

    def on_release(self) -> None:
        self.strip.dispatch("on_pick", self.position)


class ThumbnailStrip(RecycleView):
    __events__ = ("on_pick",)
    loader = ObjectProperty(None)
    current = NumericProperty(-1)

    def show(self, paths: list[str], position: int) -> None:
        self.data = [{"photo_path": path} for path in paths]
        self.current = position
        self._halt()
        self.scroll_x = self._alignment(position)

    def focus(self, position: int) -> None:
        self.current = position
        self._halt()
        Animation(scroll_x=self._alignment(position), d=theme.SWIPE_DURATION, t="out_quad").start(self)

    # Uma tira ainda deslizando por inércia disputaria o scroll_x com a
    # animação e venceria. Zerar a velocidade não basta: com o valor fora
    # dos limites o efeito recalcula o overscroll e a mola reacende.
    def _halt(self) -> None:
        Animation.cancel_all(self, "scroll_x")
        effect = self.effect_x
        low, high = sorted((effect.min, effect.max))
        effect.velocity = 0
        effect.value = min(max(effect.value, low), high)

    # A margem lateral do layout, de (largura - miniatura) / 2, faz o
    # conteúdo rolar exatamente uma célula por posição: centralizar a célula
    # i é rolar a fração i / (n - 1).
    def _alignment(self, position: int) -> float:
        return position / max(len(self.data) - 1, 1)

    def on_pick(self, position: int) -> None:
        pass
