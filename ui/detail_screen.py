from dataclasses import replace
from pathlib import Path

from kivy.animation import Animation
from kivy.input import MotionEvent
from kivy.lang import Builder
from kivy.properties import ObjectProperty

import library
import notes
import storage
from core.index import IndexedPhoto
from ui import dialogs, theme, widgets
from ui.note_panel import NotePanel
from ui.thumbnail_loader import ThumbnailLoader
from ui.widgets import Card, OverlayBehavior, SnapScreen

NO_NOTE_TEXT = "Sem anotação"
DATE_FORMAT = "%d/%m/%Y %H:%M"

Builder.load_string("""
#:import theme ui.theme

<InfoCard>:
    orientation: "vertical"
    size_hint: None, None
    adaptive_height: True
    padding: dp(theme.PADDING), dp(theme.SPACING)
    spacing: dp(theme.SPACING) / 2
    md_bg_color: theme.ISLAND
    opacity: 0
    MDBoxLayout:
        adaptive_height: True
        spacing: dp(theme.SPACING)
        MDLabel:
            id: note_label
            font_name: theme.FONT
            font_size: sp(theme.FONT_BODY)
            adaptive_height: True
            pos_hint: {"center_y": .5}
        ToolIcon:
            icon: "pencil-outline"
            pos_hint: {"center_y": .5}
            on_release: root.dispatch("on_edit")
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
    ToolIcon:
        icon: "arrow-left"
        pos_hint: {"x": 0, "top": 1}
        on_release: root.dispatch("on_back")
    Island:
        id: island
        pos_hint: {"center_x": .5}
        y: dp(theme.PADDING)
        Slot:
            ToolIcon:
                icon: "heart-outline"
                on_release: root.notice()
        Slot:
            ToolIcon:
                icon: "pencil-outline"
                on_release: root.notice()
        Slot:
            ToolIcon:
                icon: "information-outline"
                on_release: root.toggle_info()
        Slot:
            ToolIcon:
                icon: "share-variant-outline"
                on_release: root.notice()
        Slot:
            ToolIcon:
                icon: "delete-outline"
                on_release: root.confirm_delete()
    InfoCard:
        id: info
        width: root.width - 2 * dp(theme.PADDING)
        pos_hint: {"center_x": .5}
        y: island.top + dp(theme.SPACING)
        on_edit: root.edit_note()
    NotePanel:
        id: note_panel
        width: root.width - 2 * dp(theme.PADDING)
        pos_hint: {"center_x": .5}
        on_save: root.save_note(args[1])
        on_cancel: root.close_note_panel()
""")


class InfoCard(OverlayBehavior, Card):
    __events__ = ("on_edit",)

    def on_edit(self) -> None:
        pass


class DetailScreen(SnapScreen):
    __events__ = ("on_deleted", "on_back")
    photo = ObjectProperty(None)

    def __init__(self, previews: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._previews = previews

    def show(self, photo: IndexedPhoto) -> None:
        self.photo = photo
        self.hide_info()
        self.ids.note_panel.close()
        self._previews.display(photo.path, self.ids.image)

    def on_photo(self, _screen: object, photo: IndexedPhoto) -> None:
        info = self.ids.info
        info.ids.note_label.text = NO_NOTE_TEXT if photo.note is None else photo.note
        info.ids.note_label.theme_text_color = "Hint" if photo.note is None else "Primary"
        info.ids.file_label.text = Path(photo.path).name
        taken_at = photo.captured_at
        info.ids.date_label.text = "" if taken_at is None else taken_at.strftime(DATE_FORMAT)

    def toggle_info(self) -> None:
        if self.ids.info.shown:
            self.hide_info()
        else:
            self.show_info()

    def show_info(self) -> None:
        info = self.ids.info
        info.shown = True
        Animation(opacity=1, d=theme.ISLAND_DURATION, t="out_quad").start(info)

    def hide_info(self) -> None:
        info = self.ids.info
        Animation.cancel_all(info)
        info.opacity = 0
        info.shown = False

    def edit_note(self) -> None:
        self.hide_info()
        self.ids.note_panel.open(self.photo.note or "")

    def save_note(self, text: str) -> None:
        note = notes.save_note(Path(self.photo.path), text, storage.index_path())
        self.photo = replace(self.photo, note=note)
        self.close_note_panel()

    def close_note_panel(self) -> None:
        self.ids.note_panel.close()
        self.show_info()

    # Tocar fora do painel de anotação só o fecha; fora do cartão de
    # informações e da ilha, fecha o cartão e o toque segue ao destino.
    def on_touch_down(self, touch: MotionEvent) -> bool:
        note_panel, info, island = self.ids.note_panel, self.ids.info, self.ids.island
        if note_panel.shown:
            if not note_panel.collide_point(*touch.pos):
                self.close_note_panel()
                return True
        elif info.shown and not info.collide_point(*touch.pos) and not island.collide_point(*touch.pos):
            self.hide_info()
        return super().on_touch_down(touch)

    def notice(self) -> None:
        widgets.notice()

    def confirm_delete(self) -> None:
        dialogs.confirm("Excluir esta foto?", "Excluir", self.delete)

    def delete(self) -> None:
        library.delete_photo(Path(self.photo.path), storage.index_path())
        self.dispatch("on_deleted")

    def on_deleted(self) -> None:
        pass

    def on_back(self) -> None:
        pass
