from threading import Thread

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen

import library
import storage
from core.index import IndexedPhoto
from ui import dialogs
from ui.thumbnail_loader import Thumbnail, ThumbnailLoader

Builder.load_string("""
<PhotoCell>:
    fit_mode: "cover"
    size_hint_y: None
    height: self.width
    canvas.before:
        Color:
            rgba: app.theme_cls.bg_light
        Rectangle:
            pos: self.pos
            size: self.size

<GalleryScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Galeria"
            left_action_items: [["arrow-left", lambda _button: root.dispatch("on_back")]]
            right_action_items: [["database-refresh", lambda _button: root.confirm_rebuild()]]
        MDBoxLayout:
            adaptive_height: True
            padding: dp(16), dp(8)
            MDTextField:
                id: search_field
                hint_text: "Buscar na anotação"
                icon_left: "magnify"
                on_text: root.refresh()
        MDLabel:
            text: root.message
            halign: "center"
            theme_text_color: "Hint"
            size_hint_y: None
            height: dp(56) if self.text else 0
        MDScrollView:
            MDGridLayout:
                id: grid
                cols: 3
                adaptive_height: True
                spacing: dp(2)
""")


class PhotoCell(ButtonBehavior, Thumbnail):
    photo = ObjectProperty(None)


class GalleryScreen(MDScreen):
    __events__ = ("on_photo_selected", "on_back")
    message = StringProperty("")

    def __init__(self, thumbnails: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._thumbnails = thumbnails

    def refresh(self) -> None:
        term = self.ids.search_field.text
        photos = library.find_photos(storage.index_path(), term)
        self.message = "" if photos else self._empty_message(term)
        self.ids.grid.clear_widgets()
        for photo in photos:
            cell = PhotoCell(photo=photo, on_release=self._select)
            self.ids.grid.add_widget(cell)
            self._thumbnails.display(photo.path, cell)

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

    def on_back(self) -> None:
        pass

    def _select(self, cell: PhotoCell) -> None:
        self.dispatch("on_photo_selected", cell.photo)

    def _empty_message(self, term: str) -> str:
        if term:
            return "Nenhuma anotação contém o texto buscado."
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
