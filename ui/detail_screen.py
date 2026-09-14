from pathlib import Path

from kivy.animation import Animation
from kivy.input import MotionEvent
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty

import library
import storage
from core.index import IndexedPhoto
from ui import dialogs, theme
from ui.thumbnail_loader import ThumbnailLoader
from ui.widgets import Card, SnapScreen

NO_NOTE_TEXT = "Sem anotação"
DATE_FORMAT = "%d/%m/%Y %H:%M"

Builder.load_string("""
#:import theme ui.theme

<InfoPanel>:
    orientation: "vertical"
    size_hint: 1, None
    height: dp(theme.PANEL_HEIGHT)
    radius: [dp(theme.CARD_RADIUS), dp(theme.CARD_RADIUS), 0, 0]
    padding: dp(theme.PADDING), 0, dp(theme.PADDING), dp(theme.PADDING)
    spacing: dp(theme.SPACING)
    Widget:
        size_hint_y: None
        height: dp(theme.PANEL_PEEK)
        canvas:
            Color:
                rgba: theme.TEXT_MUTED
            RoundedRectangle:
                pos: self.center_x - dp(theme.HANDLE_WIDTH) / 2, self.center_y - dp(theme.HANDLE_HEIGHT) / 2
                size: dp(theme.HANDLE_WIDTH), dp(theme.HANDLE_HEIGHT)
                radius: [dp(theme.HANDLE_HEIGHT) / 2]
    MDScrollView:
        MDLabel:
            id: note_label
            font_name: theme.FONT
            font_size: sp(theme.FONT_BODY)
            adaptive_height: True
    MDLabel:
        id: file_label
        font_name: theme.FONT
        font_size: sp(theme.FONT_SMALL)
        theme_text_color: "Custom"
        text_color: theme.TEXT_MUTED
        adaptive_height: True
    MDLabel:
        id: date_label
        font_name: theme.FONT
        font_size: sp(theme.FONT_SMALL)
        theme_text_color: "Custom"
        text_color: theme.TEXT_MUTED
        adaptive_height: True

<DetailScreen>:
    md_bg_color: theme.BAR
    Thumbnail:
        id: image
        fit_mode: "contain"
        color: theme.TEXT if self.texture else theme.TRANSPARENT
        pos_hint: {"x": 0, "y": 0}
    TopScrim:
        size_hint_y: None
        height: dp(theme.SCRIM_HEIGHT)
        pos_hint: {"top": 1}
    MDBoxLayout:
        size_hint_y: None
        height: dp(theme.SCREEN_BAR_HEIGHT)
        padding: dp(theme.SPACING), 0
        pos_hint: {"top": 1}
        ToolIcon:
            icon: "arrow-left"
            pos_hint: {"center_y": .5}
            on_release: root.dispatch("on_back")
        Widget:
        ToolIcon:
            icon: "pencil-outline"
            pos_hint: {"center_y": .5}
            on_release: root.dispatch("on_edit_requested", root.photo)
        ToolIcon:
            icon: "delete-outline"
            pos_hint: {"center_y": .5}
            on_release: root.confirm_delete()
    InfoPanel:
        id: panel
""")


class InfoPanel(Card):
    expanded = BooleanProperty(False)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.collapse()

    def collapse(self) -> None:
        self.expanded = False
        self.y = self._resting_y()

    # Só a faixa da alça arrasta o painel; o restante fica com o conteúdo,
    # cuja anotação rola quando expandida.
    def on_touch_down(self, touch: MotionEvent) -> bool:
        if self.collide_point(*touch.pos) and touch.y > self.top - dp(theme.PANEL_PEEK):
            touch.grab(self)
            self._drag_start = (touch.y, self.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        touch_y, panel_y = self._drag_start
        self.y = min(0, max(self._collapsed_y(), panel_y + touch.y - touch_y))
        return True

    def on_touch_up(self, touch: MotionEvent) -> bool:
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        travelled = touch.y - self._drag_start[0]
        if abs(travelled) < dp(theme.DRAG_THRESHOLD):
            self.expanded = not self.expanded
        else:
            self.expanded = travelled > 0
        Animation(y=self._resting_y(), d=theme.PANEL_DURATION, t="out_quad").start(self)
        return True

    def _resting_y(self) -> float:
        return 0 if self.expanded else self._collapsed_y()

    def _collapsed_y(self) -> float:
        return dp(theme.PANEL_PEEK) - self.height


class DetailScreen(SnapScreen):
    __events__ = ("on_edit_requested", "on_deleted", "on_back")
    photo = ObjectProperty(None)

    def __init__(self, previews: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._previews = previews

    def show(self, photo: IndexedPhoto) -> None:
        self.photo = photo
        panel = self.ids.panel
        panel.ids.note_label.text = NO_NOTE_TEXT if photo.note is None else photo.note
        panel.ids.note_label.theme_text_color = "Hint" if photo.note is None else "Primary"
        panel.ids.file_label.text = Path(photo.path).name
        taken_at = library.capture_time(Path(photo.path))
        panel.ids.date_label.text = "" if taken_at is None else taken_at.strftime(DATE_FORMAT)
        panel.collapse()
        self._previews.display(photo.path, self.ids.image)

    def confirm_delete(self) -> None:
        dialogs.confirm("Excluir esta foto?", "Excluir", self.delete)

    def delete(self) -> None:
        library.delete_photo(Path(self.photo.path), storage.index_path())
        self.dispatch("on_deleted")

    def on_edit_requested(self, photo: IndexedPhoto) -> None:
        pass

    def on_deleted(self) -> None:
        pass

    def on_back(self) -> None:
        pass
