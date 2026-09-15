from dataclasses import dataclass

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.input import MotionEvent
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from ui import theme
from ui.thumbnail_loader import Thumbnail

Builder.load_string("""
#:import theme ui.theme

<Slide>:
    fit_mode: "contain"
    color: theme.TEXT if self.texture else theme.TRANSPARENT
""")

SLOTS = (-1, 0, 1)


def rotate_slot(slot: int, direction: int) -> int:
    # Ao avançar, o slide da direita vira o central, o central vai para a
    # esquerda e o da esquerda reaparece à direita; ao recuar, o inverso.
    return (slot - direction + 1) % 3 - 1


def swipe_destination(offset: float, width: float, index: int, count: int) -> int:
    threshold = width * theme.SWIPE_COMMIT
    if offset < -threshold and index + 1 < count:
        return index + 1
    if offset > threshold and index > 0:
        return index - 1
    return index


class Slide(Thumbnail):
    slot = NumericProperty(0)


@dataclass
class Drag:
    origin: float
    # Ponto em que o dedo passou da folga e o arrasto começou de fato.
    anchor: float | None = None


# Três slides bastam para qualquer quantidade de fotos: o central e os dois
# vizinhos, pré-carregados. O que sai por um lado volta pelo outro com a
# foto seguinte.
class PhotoPager(Widget):
    __events__ = ("on_tap",)
    loader = ObjectProperty(None)
    index = NumericProperty(0)
    # Deslocamento dos slides em relação ao repouso; propriedade para poder
    # ser animada.
    offset = NumericProperty(0)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._paths: list[str] = []
        self._drag: Drag | None = None
        self._slides = [Slide(slot=slot) for slot in SLOTS]
        for slide in self._slides:
            self.add_widget(slide)
        relayout = Clock.create_trigger(self._layout, -1)
        self.bind(pos=relayout, size=relayout, offset=relayout, index=relayout)

    def show(self, paths: list[str], position: int) -> None:
        Animation.cancel_all(self, "offset")
        self._paths = paths
        self.offset = 0
        self.index = position
        self._fill()

    def go_to(self, position: int) -> None:
        if position == self.index or self._path_at(position) is None:
            return
        Animation.cancel_all(self, "offset")
        self.offset = 0
        direction = 1 if position > self.index else -1
        # O vizinho, ainda fora da tela, recebe a foto de destino e entra
        # como se fosse a seguinte.
        self.loader.display(self._paths[position], self._slide_at(direction))
        self._commit(position, direction)

    def on_touch_down(self, touch: MotionEvent) -> bool:
        if not self.collide_point(*touch.pos):
            return False
        if self._drag is None:
            Animation.cancel_all(self, "offset")
            touch.grab(self)
            self._drag = Drag(origin=self.offset)
        return True

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return False
        drag = self._drag
        if drag.anchor is None and abs(touch.x - touch.ox) > dp(theme.SWIPE_SLOP):
            drag.anchor = touch.x
        if drag.anchor is not None:
            travel = touch.x - drag.anchor
            self.offset = drag.origin + travel * self._resistance(travel)
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        drag, self._drag = self._drag, None
        if drag.anchor is None and self.offset == 0:
            self.dispatch("on_tap")
        else:
            self._release()
        return True

    def on_tap(self) -> None:
        pass

    def _resistance(self, travel: float) -> float:
        at_edge = (travel < 0 and self.index == len(self._paths) - 1) or (travel > 0 and self.index == 0)
        return theme.SWIPE_RESISTANCE if at_edge else 1

    def _release(self) -> None:
        destination = swipe_destination(self.offset, self.width, self.index, len(self._paths))
        if destination == self.index:
            self._settle()
        else:
            self._commit(destination, destination - self.index)

    def _commit(self, position: int, direction: int) -> None:
        for slide in self._slides:
            slide.slot = rotate_slot(slide.slot, direction)
        self.index = position
        # O slide que virou o central continua no mesmo ponto da tela: o
        # deslocamento absorve a troca de índice, e a animação o leva ao
        # repouso.
        self.offset += direction * self.width
        self._fill()
        self._settle()

    def _settle(self) -> None:
        animation = Animation(offset=0, d=theme.SWIPE_DURATION, t="out_quad")
        animation.bind(on_complete=lambda *_args: self._fill())
        animation.start(self)

    def _fill(self) -> None:
        for slide in self._slides:
            # Um slide ainda em cena, saindo, só troca de foto quando some.
            if slide.slot != 0 and self._on_screen(slide):
                continue
            path = self._path_at(self.index + slide.slot)
            if path is None:
                slide.photo_path = ""
                slide.texture = None
            elif slide.photo_path != path:
                self.loader.display(path, slide)

    def _on_screen(self, slide: Slide) -> bool:
        return abs(slide.slot * self.width + self.offset) < self.width

    def _path_at(self, position: int) -> str | None:
        return self._paths[position] if 0 <= position < len(self._paths) else None

    def _slide_at(self, slot: int) -> Slide:
        return next(slide for slide in self._slides if slide.slot == slot)

    def _layout(self, *_args: object) -> None:
        for slide in self._slides:
            slide.size = self.size
            slide.pos = (self.x + slide.slot * self.width + self.offset, self.y)
