from pathlib import Path

from kivy.config import Config
from kivy.utils import platform

from ui import theme

if platform != "android":
    # A janela de desktop imita a geometria do aparelho; a configuração
    # precisa vir antes de qualquer import que crie a janela.
    Config.set("graphics", "width", str(theme.WINDOW_WIDTH))
    Config.set("graphics", "height", str(theme.WINDOW_HEIGHT))
    Config.set("graphics", "resizable", "0")

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.toast import toast

import library
import storage
from core.index import IndexedPhoto
from permissions import PermissionStatus, request_app_permissions
from ui.camera_screen import CameraScreen
from ui.detail_screen import DetailScreen
from ui.gallery_screen import GalleryScreen
from ui.keywords_screen import KeywordsScreen
from ui.thumbnail_loader import ThumbnailLoader

BACK_KEY = 27
GRID_THUMBNAIL_SIZE = 320
PREVIEW_SIZE = 1024
# A foto atual, as duas vizinhas e alguma folga para voltar: o suficiente
# para deslizar sem acumular imagens grandes.
PREVIEW_CACHE = 8


class SnapNoteApp(MDApp):
    def build(self) -> ScreenManager:
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = theme.PALETTE
        self.theme_cls.primary_hue = theme.HUE
        self.theme_cls.accent_palette = theme.PALETTE
        # No Android o teclado virtual cobriria o campo de anotação; neste
        # modo o Kivy desloca a janela até o widget focado ficar acima dele.
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_window_key)

        previews = ThumbnailLoader(PREVIEW_SIZE, max_cached=PREVIEW_CACHE)
        thumbnails = ThumbnailLoader(GRID_THUMBNAIL_SIZE)
        self.camera = CameraScreen(thumbnails, name="camera")
        self.gallery = GalleryScreen(thumbnails, name="gallery")
        self.detail = DetailScreen(previews, thumbnails, name="detail")
        self.keywords = KeywordsScreen(name="keywords")

        self.camera.bind(
            on_photo_captured=lambda _camera, file_path: self.register_capture(file_path),
            on_gallery_requested=lambda _camera: self.show_gallery_root(),
        )
        self.gallery.bind(
            on_photo_selected=lambda _gallery, photos, position: self.show_detail(photos, position),
            on_keywords_requested=lambda _gallery: self.show_keywords(),
            on_back=lambda _gallery: self.show_camera(),
        )
        self.keywords.bind(on_back=lambda _keywords: self.show_gallery())
        self.detail.bind(
            on_deleted=lambda _detail: self.show_gallery(),
            on_back=lambda _detail: self.show_gallery(),
        )

        manager = ScreenManager()
        for screen in (self.camera, self.gallery, self.detail, self.keywords):
            manager.add_widget(screen)
        return manager

    def show_camera(self) -> None:
        self.camera.refresh_last_photo()
        self.root.current = "camera"
        self.camera.start_camera()

    def show_gallery(self) -> None:
        self.camera.stop_camera()
        self.gallery.refresh()
        self.root.current = "gallery"

    def show_gallery_root(self) -> None:
        self.gallery.reset()
        self.show_gallery()

    def show_keywords(self) -> None:
        self.keywords.refresh()
        self.root.current = "keywords"

    def show_detail(self, photos: list[IndexedPhoto], position: int) -> None:
        self.detail.show(photos, position)
        self.root.current = "detail"

    def register_capture(self, file_path: str) -> None:
        photo = storage.publish(Path(file_path))
        library.index_photo(photo, storage.index_path())
        self.camera.refresh_last_photo()
        self.camera.show_capture(str(photo))

    # No Android o botão voltar chega à janela como a tecla ESC; devolver True
    # impede o comportamento padrão do Kivy, que é encerrar o app.
    def on_window_key(self, _window: object, key: int, *_args: object) -> bool:
        if key != BACK_KEY:
            return False
        if self.root.current == "camera":
            return self.camera.dismiss_overlay()
        back_actions = {
            "gallery": self.gallery.navigate_back,
            "detail": self.show_gallery,
            "keywords": self.show_gallery,
        }
        back_actions[self.root.current]()
        return True

    def on_start(self) -> None:
        # camera4kivy exige que connect_camera ocorra pelo menos um frame
        # depois de on_start.
        self.camera.refresh_last_photo()
        Clock.schedule_once(lambda _dt: request_app_permissions(self.on_permissions))

    def on_permissions(self, status: PermissionStatus) -> None:
        self.camera.on_camera_permission(status.camera)
        if not status.storage:
            toast("Sem acesso às fotos do aparelho, a galeria e a reconstrução do índice ficam limitadas às fotos deste app.")

    def on_pause(self) -> bool:
        self.camera.stop_camera()
        return True

    def on_resume(self) -> None:
        if self.root.current == "camera":
            self.camera.start_camera()

    def on_stop(self) -> None:
        self.camera.stop_camera()


if __name__ == "__main__":
    SnapNoteApp().run()
