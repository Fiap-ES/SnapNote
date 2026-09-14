from threading import Thread

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.dialog import MDDialog

import library
import storage
from core.index import IndexedPhoto, Keyword
from ui import dialogs
from ui.thumbnail_loader import ThumbnailLoader
from ui.widgets import RoundedPhoto, RowCard, SnapScreen

Builder.load_string("""
#:import theme ui.theme

<PhotoCell>:
    fit_mode: "cover"
    radius: dp(theme.THUMB_RADIUS)
    size_hint_y: None
    height: self.width

<FolderCard>:
    IconGlyph:
        icon: "folder-outline"
        font_size: sp(theme.CARD_ICON_SIZE)
        color: theme.ACCENT
    Label:
        text: root.group.keyword.term
        font_name: theme.FONT_REGULAR
        font_size: sp(theme.FONT_BODY)
        color: theme.TEXT
        halign: "left"
        valign: "center"
        text_size: self.size
        shorten: True
    Label:
        text: str(root.group.photo_count)
        font_name: theme.FONT
        font_size: sp(theme.FONT_SMALL)
        color: theme.TEXT_MUTED
        size_hint_x: None
        width: self.texture_size[0]

<GalleryScreen>:
    md_bg_color: theme.LAYER_0
    MDBoxLayout:
        orientation: "vertical"
        ScreenBar:
            title: root.group.term if root.group else "Galeria"
            on_back: root.navigate_back()
            ToolIcon:
                icon: "tag-multiple-outline"
                pos_hint: {"center_y": .5}
                on_release: root.dispatch("on_keywords_requested")
            ToolIcon:
                icon: "database-refresh-outline"
                pos_hint: {"center_y": .5}
                on_release: root.confirm_rebuild()
        MDBoxLayout:
            adaptive_height: True
            padding: dp(theme.PADDING), dp(theme.SPACING)
            FieldBox:
                size_hint_y: None
                height: dp(theme.SEARCH_HEIGHT)
                radius: [self.height / 2]
                IconGlyph:
                    icon: "magnify"
                    color: theme.TEXT_MUTED
                TextInput:
                    id: search_field
                    hint_text: "Buscar na anotação"
                    multiline: False
                    write_tab: False
                    background_normal: ""
                    background_active: ""
                    background_color: theme.TRANSPARENT
                    foreground_color: theme.TEXT
                    hint_text_color: theme.TEXT_MUTED
                    cursor_color: theme.ACCENT
                    font_name: theme.FONT
                    font_size: sp(theme.FONT_BODY)
                    padding: 0, (self.height - self.line_height) / 2
                    on_text: root.refresh()
        MDLabel:
            text: root.message
            font_name: theme.FONT
            halign: "center"
            theme_text_color: "Custom"
            text_color: theme.TEXT_MUTED
            size_hint_y: None
            height: dp(theme.MESSAGE_HEIGHT) if self.text else 0
        MDScrollView:
            MDBoxLayout:
                orientation: "vertical"
                adaptive_height: True
                padding: dp(theme.PADDING), 0, dp(theme.PADDING), dp(theme.PADDING)
                spacing: dp(theme.PADDING)
                MDBoxLayout:
                    id: folders
                    orientation: "vertical"
                    adaptive_height: True
                    spacing: dp(theme.SPACING)
                MDGridLayout:
                    id: grid
                    cols: 3
                    adaptive_height: True
                    spacing: dp(theme.GRID_SPACING)
                    col_force_default: True
                    col_default_width: (self.width - 2 * dp(theme.GRID_SPACING)) / 3
""")


class PhotoCell(ButtonBehavior, RoundedPhoto):
    photo = ObjectProperty(None)


class FolderCard(ButtonBehavior, RowCard):
    group = ObjectProperty(None)


class GalleryScreen(SnapScreen):
    __events__ = ("on_photo_selected", "on_keywords_requested", "on_back")
    message = StringProperty("")
    group = ObjectProperty(None, allownone=True)

    def __init__(self, thumbnails: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._thumbnails = thumbnails

    def refresh(self) -> None:
        term = self.ids.search_field.text
        index_path = storage.index_path()
        keyword_id = self.group.id if self.group else None
        photos = library.find_photos(index_path, term, keyword_id)
        # As pastas só aparecem na raiz e sem busca; dentro de um grupo ou
        # numa busca, só a grade de fotos.
        groups = library.groups(index_path) if not term and self.group is None else []
        self.message = "" if photos or groups else self._empty_message(term)
        self.ids.folders.clear_widgets()
        for group in groups:
            self.ids.folders.add_widget(FolderCard(group=group, on_release=self._open_group))
        self.ids.grid.clear_widgets()
        for photo in photos:
            cell = PhotoCell(photo=photo, on_release=self._select)
            self.ids.grid.add_widget(cell)
            self._thumbnails.display(photo.path, cell)

    def open_group(self, keyword: Keyword | None) -> None:
        self.group = keyword
        self.refresh()

    def navigate_back(self) -> None:
        if self.group is None:
            self.dispatch("on_back")
        else:
            self.open_group(None)

    def confirm_rebuild(self) -> None:
        dialogs.confirm(
            "Reconstruir o índice a partir das fotos?", "Reconstruir", self.rebuild
        )

    def rebuild(self) -> None:
        # A reconstrução lê o EXIF de cada arquivo; fora da thread do Kivy a
        # interface continua respondendo enquanto o diálogo indica a espera.
        progress = dialogs.progress("Reconstruindo o índice...")
        Thread(
            target=self._rebuild_in_background, args=(progress,), daemon=True
        ).start()

    def on_photo_selected(self, photo: IndexedPhoto) -> None:
        pass

    def on_keywords_requested(self) -> None:
        pass

    def on_back(self) -> None:
        pass

    def _open_group(self, card: FolderCard) -> None:
        self.open_group(card.group.keyword)

    def _select(self, cell: PhotoCell) -> None:
        self.dispatch("on_photo_selected", cell.photo)

    def _empty_message(self, term: str) -> str:
        if term:
            return "Nenhuma anotação contém o texto buscado."
        if self.group is not None:
            return "Nenhuma foto neste grupo."
        return "Nenhuma foto ainda."

    def _rebuild_in_background(self, progress: MDDialog) -> None:
        try:
            library.rebuild_index(storage.photos_dir(), storage.index_path())
        finally:
            self._finish_rebuild(progress)

    @mainthread
    def _finish_rebuild(self, progress: MDDialog) -> None:
        progress.dismiss()
        self.refresh()
