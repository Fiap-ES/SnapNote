from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

from permissions import request_camera_permission
from ui.camera_screen import CameraScreen
from ui.note_screen import NoteScreen


class SnapNoteApp(MDApp):
    def build(self) -> ScreenManager:
        self.theme_cls.theme_style = "Dark"
        # No Android o teclado virtual cobriria o campo de anotação; neste
        # modo o Kivy desloca a janela até o widget focado ficar acima dele.
        Window.softinput_mode = "below_target"
        self.camera = CameraScreen(name="camera")
        self.note = NoteScreen(name="note")
        self.camera.bind(on_photo_captured=self.open_note)
        self.note.bind(on_finished=self.back_to_camera)
        manager = ScreenManager()
        manager.add_widget(self.camera)
        manager.add_widget(self.note)
        return manager

    def open_note(self, _camera: CameraScreen, file_path: str) -> None:
        self.camera.stop_camera()
        self.note.show_photo(file_path)
        self.root.current = "note"

    def back_to_camera(self, _note: NoteScreen) -> None:
        self.root.current = "camera"
        self.camera.start_camera()

    def on_start(self) -> None:
        # camera4kivy exige que connect_camera ocorra pelo menos um frame
        # depois de on_start.
        Clock.schedule_once(
            lambda _dt: request_camera_permission(self.camera.on_camera_permission)
        )

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
