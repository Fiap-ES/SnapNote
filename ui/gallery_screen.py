from datetime import date
from threading import Thread

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, OptionProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout

import library
import storage
from core.index import IndexedPhoto, Keyword
from ui import dialogs
from ui.dates import section_label
from ui.thumbnail_loader import ThumbnailLoader
from ui.widgets import Card, RoundedPhoto, SnapScreen

Builder.load_string("""
#:import theme ui.theme

<PhotoCell>:
    fit_mode: "cover"
    radius: dp(theme.THUMB_RADIUS)
    size_hint_y: None
    height: self.width

<PhotoGrid>:
    cols: 3
    adaptive_height: True
    spacing: dp(theme.GRID_SPACING)
    col_force_default: True
    col_default_width: (self.width - 2 * dp(theme.GRID_SPACING)) / 3

<SectionHeader>:
    font_name: theme.FONT_REGULAR
    bold: True
    font_size: sp(theme.SECTION_FONT_SIZE)
    color: theme.TEXT
    halign: "left"
    valign: "center"
    text_size: self.size
    size_hint_y: None
    height: dp(theme.SECTION_HEIGHT)

<AlbumGrid>:
    cols: 2
    adaptive_height: True
    spacing: dp(theme.ALBUM_SPACING)
    col_force_default: True
    col_default_width: (self.width - dp(theme.ALBUM_SPACING)) / 2

<AlbumCard>:
    orientation: "vertical"
    adaptive_height: True
    spacing: dp(theme.SPACING) / 2
    RoundedPhoto:
        id: cover
        fit_mode: "cover"
        radius: dp(theme.CARD_RADIUS)
        size_hint_y: None
        height: self.width
    Label:
        text: root.album.group.keyword.term
        font_name: theme.FONT_REGULAR
        font_size: sp(theme.FONT_BODY)
        color: theme.TEXT
        halign: "left"
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]
        shorten: True
    Label:
        text: str(root.album.group.photo_count)
        font_name: theme.FONT
        font_size: sp(theme.FONT_SMALL)
        color: theme.TEXT_MUTED
        halign: "left"
        text_size: self.width, None
        size_hint_y: None
        height: self.texture_size[1]

<NavItem>:
    orientation: "vertical"
    padding: 0, dp(theme.SPACING)
    IconGlyph:
        icon: root.icon
        font_size: sp(theme.NAV_ICON_SIZE)
        color: theme.ACCENT if root.active else theme.TEXT_MUTED
        size_hint_x: 1
        halign: "center"
        text_size: self.width, None
    Label:
        text: root.text
        font_name: theme.FONT_MODE
        font_size: sp(theme.NAV_FONT_SIZE)
        color: theme.ACCENT if root.active else theme.TEXT_MUTED
        size_hint_y: None
        height: self.texture_size[1]

<NavPill>:
    size_hint: None, None
    size: dp(theme.NAV_WIDTH), dp(theme.NAV_HEIGHT)
    radius: [self.height / 2]
    NavItem:
        icon: "image-multiple-outline"
        text: "Fotos"
        active: root.view == "photos"
        on_release: root.dispatch("on_select", "photos")
    NavItem:
        icon: "folder-outline"
        text: "Pastas"
        active: root.view == "folders"
        on_release: root.dispatch("on_select", "folders")

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
                id: content
                orientation: "vertical"
                adaptive_height: True
                padding: dp(theme.PADDING), 0, dp(theme.PADDING), dp(theme.NAV_HEIGHT + 2 * theme.PADDING)
                spacing: dp(theme.SPACING)
    NavPill:
        view: root.view
        pos_hint: {"center_x": .5}
        y: dp(theme.PADDING)
        on_select: root.show_view(args[1])
""")


class PhotoCell(ButtonBehavior, RoundedPhoto):
    photo = ObjectProperty(None)


class PhotoGrid(MDGridLayout):
    pass


class SectionHeader(Label):
    pass


class AlbumGrid(MDGridLayout):
    pass


class AlbumCard(ButtonBehavior, MDBoxLayout):
    album = ObjectProperty(None)


class NavItem(ButtonBehavior, MDBoxLayout):
    icon = StringProperty("")
    text = StringProperty("")
    active = BooleanProperty(False)


class NavPill(Card):
    __events__ = ("on_select",)
    view = StringProperty("photos")

    def on_select(self, view: str) -> None:
        pass


class GalleryScreen(SnapScreen):
    __events__ = ("on_photo_selected", "on_keywords_requested", "on_back")
    message = StringProperty("")
    group = ObjectProperty(None, allownone=True)
    view = OptionProperty("photos", options=["photos", "folders"])

    def __init__(self, thumbnails: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._thumbnails = thumbnails

    def refresh(self) -> None:
        term = self.ids.search_field.text
        index_path = storage.index_path()
        self.ids.content.clear_widgets()
        if term:
            keyword_id = self.group.id if self.group else None
            self._show_grid(library.find_photos(index_path, term, keyword_id), "Nenhuma anotação contém o texto buscado.")
        elif self.group is not None:
            self._show_grid(library.find_photos(index_path, keyword_id=self.group.id), "Nenhuma foto neste grupo.")
        elif self.view == "folders":
            self._show_albums(library.albums(index_path))
        else:
            self._show_sections(library.photo_sections(index_path))

    def show_view(self, view: str) -> None:
        self.group = None
        self.view = view
        self.refresh()

    def reset(self) -> None:
        self.group = None
        self.view = "photos"

    def open_group(self, keyword: Keyword | None) -> None:
        self.group = keyword
        self.refresh()

    def navigate_back(self) -> None:
        if self.group is None:
            self.dispatch("on_back")
        else:
            self.show_view("folders")

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

    def _show_sections(self, sections: list[library.DateSection]) -> None:
        self.message = "" if sections else "Nenhuma foto ainda."
        today = date.today()
        for section in sections:
            self.ids.content.add_widget(SectionHeader(text=section_label(section.day, today)))
            self.ids.content.add_widget(self._grid(section.photos))

    def _show_grid(self, photos: list[IndexedPhoto], empty_message: str) -> None:
        self.message = "" if photos else empty_message
        self.ids.content.add_widget(self._grid(photos))

    def _show_albums(self, albums: list[library.Album]) -> None:
        self.message = "" if albums else "Nenhuma pasta ainda."
        grid = AlbumGrid()
        for album in albums:
            card = AlbumCard(album=album, on_release=self._open_album)
            grid.add_widget(card)
            self._thumbnails.display(album.cover.path, card.ids.cover)
        self.ids.content.add_widget(grid)

    def _grid(self, photos: list[IndexedPhoto]) -> PhotoGrid:
        grid = PhotoGrid()
        for photo in photos:
            cell = PhotoCell(photo=photo, on_release=self._select)
            grid.add_widget(cell)
            self._thumbnails.display(photo.path, cell)
        return grid

    def _open_album(self, card: AlbumCard) -> None:
        self.open_group(card.album.group.keyword)

    def _select(self, cell: PhotoCell) -> None:
        self.dispatch("on_photo_selected", cell.photo)

    def _rebuild_in_background(self, progress: MDDialog) -> None:
        try:
            library.rebuild_index(storage.photos_dir(), storage.index_path())
        finally:
            self._finish_rebuild(progress)

    @mainthread
    def _finish_rebuild(self, progress: MDDialog) -> None:
        progress.dismiss()
        self.refresh()
