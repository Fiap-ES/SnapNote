from collections.abc import Callable
from datetime import datetime

from camera4kivy import Preview
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform

if platform == "android":
    from android.permissions import Permission, check_permission, request_permissions

KV = """
<CameraScreen>:
    orientation: "vertical"
    Preview:
        id: preview
        aspect_ratio: "16:9"
    Label:
        text: root.status
        size_hint_y: None
        height: dp(64)
        font_size: sp(12)
        text_size: self.width - dp(16), None
        halign: "center"
        valign: "middle"
    Button:
        text: "Capturar"
        font_size: sp(18)
        size_hint_y: None
        height: dp(72)
        on_release: root.capture()
"""


def camera_permission_granted() -> bool:
    return platform != "android" or check_permission(Permission.CAMERA)


def request_camera_permission(on_result: Callable[[bool], None]) -> None:
    if camera_permission_granted():
        on_result(True)
        return

    # O Android responde em uma thread Java e, se o diálogo for interrompido,
    # com listas vazias; por isso o estado real é consultado de novo, já na
    # thread do Kivy.
    @mainthread
    def deliver(_permissions: list[str], _grants: list[bool]) -> None:
        on_result(camera_permission_granted())

    request_permissions([Permission.CAMERA], deliver)


def timestamp_name() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


class CameraScreen(BoxLayout):
    status = StringProperty("")

    def on_camera_permission(self, granted: bool) -> None:
        if granted:
            self.start_camera()
        else:
            self.status = "Permissão de câmera negada."

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
        self.ids.preview.capture_photo(
            location="private", subdir="photos", name=timestamp_name()
        )

    # camera4kivy entrega o caminho em uma thread Java; propriedades de widget
    # só podem ser alteradas na thread do Kivy.
    @mainthread
    def on_photo_saved(self, file_path: str) -> None:
        self.status = file_path
        Logger.info("SnapNote: foto salva em %s", file_path)


class SnapNoteApp(App):
    def build(self) -> CameraScreen:
        Builder.load_string(KV)
        return CameraScreen()

    def on_start(self) -> None:
        # camera4kivy exige que connect_camera ocorra pelo menos um frame
        # depois de on_start.
        Clock.schedule_once(
            lambda _dt: request_camera_permission(self.root.on_camera_permission)
        )

    def on_pause(self) -> bool:
        self.root.stop_camera()
        return True

    def on_resume(self) -> None:
        self.root.start_camera()

    def on_stop(self) -> None:
        self.root.stop_camera()


if __name__ == "__main__":
    SnapNoteApp().run()
