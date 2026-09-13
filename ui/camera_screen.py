from datetime import datetime

from camera4kivy import Preview
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.logger import Logger
from kivymd.toast import toast
from kivymd.uix.screen import MDScreen

import storage
from permissions import camera_permission_granted, photo_saving_allowed

Builder.load_string("""
<CameraScreen>:
    MDBoxLayout:
        orientation: "vertical"
        Preview:
            id: preview
            aspect_ratio: "16:9"
        MDFloatLayout:
            size_hint_y: None
            height: dp(96)
            MDIconButton:
                icon: "camera"
                icon_size: "48sp"
                md_bg_color: app.theme_cls.primary_color
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                pos_hint: {"center_x": .5, "center_y": .5}
                on_release: root.capture()
            MDIconButton:
                icon: "image-multiple"
                icon_size: "32sp"
                pos_hint: {"center_x": .85, "center_y": .5}
                on_release: root.dispatch("on_gallery_requested")
""")


def timestamp_name() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


class CameraScreen(MDScreen):
    __events__ = ("on_photo_captured", "on_gallery_requested")

    def on_camera_permission(self, granted: bool) -> None:
        if granted:
            self.start_camera()
        else:
            toast("Permissão de câmera negada.")

    def start_camera(self) -> None:
        # Depois do diálogo de permissão o Android dispara tanto o callback de
        # concessão quanto on_resume; a câmera só pode ser conectada uma vez.
        preview = self.ids.preview
        if preview.camera_connected or not camera_permission_granted():
            return
        preview.connect_camera(enable_video=False, filepath_callback=self.on_photo_saved)

    def stop_camera(self) -> None:
        # disconnect_camera falha em um Preview que nunca foi conectado, o que
        # acontece ao pausar o app com a permissão negada.
        if self.ids.preview.camera_connected:
            self.ids.preview.disconnect_camera()

    def capture(self) -> None:
        if not photo_saving_allowed():
            toast("Sem permissão de armazenamento, a foto não pode ser salva.")
            return
        self.ids.preview.capture_photo(
            location=storage.capture_location(),
            subdir=storage.CAPTURE_SUBDIR,
            name=timestamp_name(),
        )

    # camera4kivy entrega o caminho em uma thread Java; a navegação e os
    # widgets só podem ser tocados na thread do Kivy.
    @mainthread
    def on_photo_saved(self, file_path: str) -> None:
        Logger.info("SnapNote: foto salva em %s", file_path)
        self.dispatch("on_photo_captured", file_path)

    def on_photo_captured(self, file_path: str) -> None:
        pass

    def on_gallery_requested(self) -> None:
        pass
