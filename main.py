from pathlib import Path

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.toast import toast

import notes
import storage
from core.index import IndexedPhoto
from permissions import PermissionStatus, request_app_permissions
from ui.camera_screen import CameraScreen
from ui.detail_screen import DetailScreen
from ui.gallery_screen import GalleryScreen
from ui.note_screen import NoteScreen
from ui.thumbnail_loader import ThumbnailLoader

BACK_KEY = 27
GRID_THUMBNAIL_SIZE = 320
PREVIEW_SIZE = 1024


class SnapNoteApp(MDApp):
    def build(self) -> ScreenManager:
        self.theme_cls.theme_style = "Dark"
        # No Android o teclado virtual cobriria o campo de anotação; neste
        # modo o Kivy desloca a janela até o widget focado ficar acima dele.
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_window_key)

        previews = ThumbnailLoader(PREVIEW_SIZE)
        self.camera = CameraScreen(name="camera")
        self.note = NoteScreen(previews, name="note")
        self.gallery = GalleryScreen(ThumbnailLoader(GRID_THUMBNAIL_SIZE), name="gallery")
        self.detail = DetailScreen(previews, name="detail")

        self.camera.bind(
            on_photo_captured=lambda _camera, file_path: self.annotate_capture(file_path),
            on_gallery_requested=lambda _camera: self.show_gallery(),
        )
        self.gallery.bind(
            on_photo_selected=lambda _gallery, photo: self.show_detail(photo),
            on_back=lambda _gallery: self.show_camera(),
        )
        self.detail.bind(
            on_edit_requested=lambda _detail, photo: self.edit_note(photo),
            on_deleted=lambda _detail: self.show_gallery(),
            on_back=lambda _detail: self.show_gallery(),
        )

        manager = ScreenManager()
        for screen in (self.camera, self.note, self.gallery, self.detail):
            manager.add_widget(screen)
        return manager

    def show_camera(self) -> None:
        self.root.current = "camera"
        self.camera.start_camera()

    def show_gallery(self) -> None:
        self.camera.stop_camera()
        self.gallery.refresh()
        self.root.current = "gallery"

    def show_detail(self, photo: IndexedPhoto) -> None:
        self.detail.show(photo)
        self.root.current = "detail"

    def annotate_capture(self, file_path: str) -> None:
        self.camera.stop_camera()
        photo = storage.publish(Path(file_path))
        self.note.edit(
            str(photo),
            "",
            cancel_label="Descartar",
            on_saved=lambda _path, _note: self.show_camera(),
            on_cancelled=self.discard_capture,
        )
        self.root.current = "note"

    def discard_capture(self, file_path: str) -> None:
        notes.discard_photo(Path(file_path))
        self.show_camera()

    def edit_note(self, photo: IndexedPhoto) -> None:
        self.note.edit(
            photo.path,
            photo.note or "",
            cancel_label="Cancelar",
            on_saved=lambda path, note: self.show_detail(IndexedPhoto(path, note)),
            on_cancelled=lambda _path: self.show_detail(photo),
        )
        self.root.current = "note"

    # No Android o botão voltar chega à janela como a tecla ESC; devolver True
    # impede o comportamento padrão do Kivy, que é encerrar o app.
    def on_window_key(self, _window: object, key: int, *_args: object) -> bool:
        back_actions = {
            "note": self.note.cancel,
            "gallery": self.show_camera,
            "detail": self.show_gallery,
        }
        action = back_actions.get(self.root.current)
        if key != BACK_KEY or action is None:
            return False
        action()
        return True

    def on_start(self) -> None:
        # camera4kivy exige que connect_camera ocorra pelo menos um frame
        # depois de on_start.
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
