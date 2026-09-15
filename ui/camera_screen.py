from datetime import datetime
from pathlib import Path

from camera4kivy import Preview
from kivy.animation import Animation
from kivy.clock import mainthread
from kivy.input import MotionEvent
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivymd.toast import toast

import library
import notes
import ocr
import storage
from library import CAPTURE_NAME_FORMAT, find_photos
from permissions import camera_permission_granted, photo_saving_allowed
from ui import dialogs, theme, widgets
from ui.note_panel import NotePanel
from ui.thumbnail_loader import Thumbnail, ThumbnailLoader
from ui.widgets import Island, OverlayBehavior, SnapScreen

Builder.load_string("""
#:import theme ui.theme
#:import md_icons kivymd.icon_definitions.md_icons

<TopSlot@MDAnchorLayout>:
    anchor_x: "center"
    anchor_y: "center"

<TopBadge@Label>:
    font_name: theme.FONT_BADGE
    bold: True
    font_size: sp(theme.FONT_BADGE_SIZE)
    color: theme.ACCENT

<StruckToolIcon@ToolIcon>:
    canvas.after:
        Color:
            rgba: theme.BAR
        Line:
            points: self.center_x - dp(theme.STRIKE_REACH) + dp(theme.STRIKE_GAP), self.center_y + dp(theme.STRIKE_REACH) + dp(theme.STRIKE_GAP), self.center_x + dp(theme.STRIKE_REACH) + dp(theme.STRIKE_GAP), self.center_y - dp(theme.STRIKE_REACH) + dp(theme.STRIKE_GAP)
            width: dp(theme.STRIKE_WIDTH)
        Color:
            rgba: self.icon_color
        Line:
            points: self.center_x - dp(theme.STRIKE_REACH), self.center_y + dp(theme.STRIKE_REACH), self.center_x + dp(theme.STRIKE_REACH), self.center_y - dp(theme.STRIKE_REACH)
            width: dp(theme.STRIKE_WIDTH)

<FloatingIcon>:
    text: md_icons.get(self.icon, "")
    font_name: theme.ICON_FONT
    font_size: sp(theme.FLOAT_ICON_SIZE)
    color: theme.TEXT
    size_hint: None, None
    size: dp(theme.FLOAT_BUTTON_SIZE), dp(theme.FLOAT_BUTTON_SIZE)
    canvas.before:
        PushMatrix
        Scale:
            x: -1
            origin: self.center
        Color:
            rgba: theme.OVERLAY
        Ellipse:
            pos: self.pos
            size: self.size
    canvas.after:
        PopMatrix

<CapturePanel>:
    adaptive_width: True
    padding: dp(theme.ISLAND_INSET), 0, 0, 0
    spacing: dp(theme.SPACING) / 2
    opacity: 0
    RoundedPhoto:
        id: thumbnail
        fit_mode: "cover"
        radius: dp(theme.LAST_PHOTO_RADIUS)
        size_hint: None, None
        size: dp(theme.LAST_PHOTO_SIZE), dp(theme.LAST_PHOTO_SIZE)
        pos_hint: {"center_y": .5}
    ToolIcon:
        icon: "share-variant-outline"
        pos_hint: {"center_y": .5}
        on_release: root.dispatch("on_decorative")
    ToolIcon:
        icon: "pencil-outline"
        pos_hint: {"center_y": .5}
        on_release: root.dispatch("on_decorative")
    ToolIcon:
        icon: "delete-outline"
        pos_hint: {"center_y": .5}
        on_release: root.dispatch("on_delete")
    Widget:
        size_hint: None, None
        size: dp(1), dp(theme.ICON_SIZE)
        pos_hint: {"center_y": .5}
        canvas:
            Color:
                rgba: theme.DIVIDER
            Rectangle:
                pos: self.pos
                size: self.size
    ToolIcon:
        icon: "brain"
        icon_color: theme.ACCENT
        pos_hint: {"center_y": .5}
        on_release: root.dispatch("on_annotate")

<LastPhotoButton>:
    fit_mode: "cover"
    color: theme.TEXT if self.texture else theme.TRANSPARENT
    size_hint: None, None
    size: dp(theme.LAST_PHOTO_SIZE), dp(theme.LAST_PHOTO_SIZE)
    canvas.before:
        StencilPush
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(theme.LAST_PHOTO_RADIUS)]
        StencilUse
        Color:
            rgba: theme.SURFACE
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(theme.LAST_PHOTO_RADIUS)]
    canvas.after:
        StencilUnUse
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(theme.LAST_PHOTO_RADIUS)]
        StencilPop

<CameraScreen>:
    md_bg_color: theme.BAR
    MDBoxLayout:
        orientation: "vertical"
        MDBoxLayout:
            size_hint_y: None
            height: dp(theme.TOP_BAR_HEIGHT)
            TopSlot:
                ToolIcon:
                    icon: "image-filter-center-focus"
                    on_release: root.notice()
            TopSlot:
                ToolIcon:
                    icon: "flash" if root.flash_on else "flash-off"
                    icon_color: theme.ACCENT if root.flash_on else theme.TEXT
                    on_release: root.toggle_flash()
            TopSlot:
                ToolIcon:
                    icon: "timer-off-outline"
                    on_release: root.notice()
            TopSlot:
                TopBadge:
                    text: theme.BADGE_SPACER.join(root.top_label)
            TopSlot:
                StruckToolIcon:
                    icon: "flower-outline"
                    on_release: root.notice()
            TopSlot:
                ToolIcon:
                    icon: "cog-outline"
                    on_release: root.notice()
        MDFloatLayout:
            id: preview_area
            MDBoxLayout:
                pos_hint: {"x": 0, "y": 0}
                Preview:
                    id: preview
                    aspect_ratio: "16:9"
                    letterbox_color: theme.BAR
            FloatingIcon:
                icon: "auto-fix"
                right: preview_area.right - dp(theme.PADDING)
                center_y: zoom_row.center_y
                on_release: root.notice()
            CapturePanel:
                id: capture_panel
                pos_hint: {"center_x": .5}
                on_decorative: root.notice()
                on_delete: root.confirm_delete_capture()
                on_annotate: root.open_note_panel()
            MDBoxLayout:
                id: zoom_row
                adaptive_size: True
                padding: dp(theme.ZOOM_PILL_PADDING), 0
                md_bg_color: theme.OVERLAY
                radius: [self.height / 2]
                pos_hint: {"center_x": .5, "y": theme.ZOOM_ROW_Y}
                ZoomChip:
                    text: "0.6x"
                    on_release: root.notice()
                ZoomChip:
                    text: "1x"
                    active: True
                    on_release: root.notice()
                ZoomChip:
                    text: "2x"
                    on_release: root.notice()
        ScrollView:
            size_hint_y: None
            height: dp(theme.MODES_HEIGHT)
            do_scroll_y: False
            bar_width: 0
            MDAnchorLayout:
                anchor_x: "center"
                size_hint_x: None
                width: max(modes.width, root.width)
                MDBoxLayout:
                    id: modes
                    adaptive_width: True
                    spacing: dp(theme.MODES_SPACING)
                    ModeChip:
                        text: "Noite"
                        on_release: root.notice()
                    ModeChip:
                        text: "Retrato"
                        on_release: root.notice()
                    ModeChip:
                        text: "Foto"
                        active: True
                        on_release: root.notice()
                    ModeChip:
                        text: "Vídeo"
                        on_release: root.notice()
                    ModeChip:
                        text: "Microfilme"
                        on_release: root.notice()
                    ModeChip:
                        text: "Mais"
                        on_release: root.notice()
        MDFloatLayout:
            size_hint_y: None
            height: dp(theme.BOTTOM_BAR_HEIGHT)
            LastPhotoButton:
                id: last_photo
                pos_hint: {"center_x": theme.LAST_PHOTO_X, "center_y": .5}
                on_release: root.dispatch("on_gallery_requested")
            ShutterButton:
                pos_hint: {"center_x": .5, "center_y": .5}
                on_release: root.capture()
            ToolIcon:
                icon: "autorenew"
                icon_size: sp(theme.FLIP_ICON_SIZE)
                pos_hint: {"center_x": theme.FLIP_X, "center_y": .5}
                on_release: root.flip_camera()
    NotePanel:
        id: note_panel
        width: root.width - 2 * dp(theme.PADDING)
        pos_hint: {"center_x": .5}
        on_save: root.save_note(args[1])
        on_cancel: root.hide_note_panel()
""")

# O zoom inicial do camera4kivy é a escala linear do CameraX (padrão 0.5, já
# ampliado): 0 corresponde ao menor zoom que o aparelho suporta, inclusive
# abaixo de 1x quando há ultrawide. O provedor aplica o valor logo após
# vincular a câmera, e a conexão é refeita a cada volta para esta tela.
MINIMUM_ZOOM = 0

SUGGESTION_CAPTION = "Sugestão lida da imagem. Revise ou apague antes de salvar."


def timestamp_name() -> str:
    return datetime.now().strftime(CAPTURE_NAME_FORMAT)


class LastPhotoButton(ButtonBehavior, Thumbnail):
    pass


class CapturePanel(OverlayBehavior, Island):
    __events__ = ("on_decorative", "on_delete", "on_annotate")
    photo_path = StringProperty("")

    def on_decorative(self) -> None:
        pass

    def on_delete(self) -> None:
        pass

    def on_annotate(self) -> None:
        pass


class FloatingIcon(ButtonBehavior, Label):
    icon = StringProperty("")


class CameraScreen(SnapScreen):
    __events__ = ("on_photo_captured", "on_gallery_requested")
    top_label = StringProperty("ZEISS")
    flash_on = BooleanProperty(False)

    def __init__(self, thumbnails: ThumbnailLoader, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._thumbnails = thumbnails
        self._suggestion = ""

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
        preview.connect_camera(
            enable_video=False,
            default_zoom=MINIMUM_ZOOM,
            default_flash=self._flash_state(),
            filepath_callback=self.on_photo_saved,
        )

    def stop_camera(self) -> None:
        # disconnect_camera falha em um Preview que nunca foi conectado, o que
        # acontece ao pausar o app com a permissão negada.
        if self.ids.preview.camera_connected:
            self.ids.preview.disconnect_camera()

    def toggle_flash(self) -> None:
        self.flash_on = not self.flash_on
        if self.ids.preview.camera_connected:
            self.ids.preview.flash(self._flash_state())

    def flip_camera(self) -> None:
        if self.ids.preview.camera_connected:
            self.ids.preview.select_camera("toggle")

    def capture(self) -> None:
        if not photo_saving_allowed():
            toast("Sem permissão de armazenamento, a foto não pode ser salva.")
            return
        self.ids.preview.capture_photo(
            location=storage.capture_location(),
            subdir=storage.CAPTURE_SUBDIR,
            name=timestamp_name(),
        )

    def show_capture(self, file_path: str) -> None:
        panel = self.ids.capture_panel
        panel.photo_path = file_path
        self._thumbnails.display(file_path, panel.ids.thumbnail)
        self._suggestion = ""
        ocr.recognize_text(Path(file_path), lambda text: self._suggest(file_path, text))
        resting = self.ids.zoom_row.top + dp(theme.SPACING)
        panel.y = resting - dp(theme.ISLAND_SLIDE)
        panel.shown = True
        Animation(y=resting, opacity=1, d=theme.ISLAND_DURATION, t="out_quad").start(panel)

    def hide_capture(self) -> None:
        panel = self.ids.capture_panel
        Animation.cancel_all(panel)
        panel.opacity = 0
        panel.shown = False

    def confirm_delete_capture(self) -> None:
        dialogs.confirm("Excluir esta foto?", "Excluir", self.delete_capture)

    def delete_capture(self) -> None:
        library.delete_photo(Path(self.ids.capture_panel.photo_path), storage.index_path())
        self.hide_capture()
        self.refresh_last_photo()

    def open_note_panel(self) -> None:
        self.ids.note_panel.open(self._suggestion, SUGGESTION_CAPTION if self._suggestion else "")

    # O reconhecimento responde em outra thread e pode terminar depois de o
    # painel já estar aberto ou de outra foto ter sido capturada.
    @mainthread
    def _suggest(self, file_path: str, text: str) -> None:
        if self.ids.capture_panel.photo_path != file_path or not text:
            return
        self._suggestion = text
        if self.ids.note_panel.shown:
            self.ids.note_panel.suggest(text, SUGGESTION_CAPTION)

    def hide_note_panel(self) -> None:
        self.ids.note_panel.close()

    def save_note(self, text: str) -> None:
        notes.save_note(Path(self.ids.capture_panel.photo_path), text, storage.index_path())
        self.hide_note_panel()
        self.hide_capture()

    def dismiss_overlay(self) -> bool:
        if self.ids.note_panel.shown:
            self.hide_note_panel()
            return True
        if self.ids.capture_panel.shown:
            self.hide_capture()
            return True
        return False

    # Tocar fora do painel de anotação só o fecha; fora da ilha, fecha a
    # ilha e o toque segue ao destino, para que o obturador já capture.
    def on_touch_down(self, touch: MotionEvent) -> bool:
        note_panel, island = self.ids.note_panel, self.ids.capture_panel
        if note_panel.shown:
            if not note_panel.collide_point(*touch.pos):
                self.hide_note_panel()
                return True
        elif island.shown and not island.collide_point(*touch.pos):
            self.hide_capture()
        return super().on_touch_down(touch)

    def on_pre_leave(self) -> None:
        self.hide_note_panel()
        self.hide_capture()

    def refresh_last_photo(self) -> None:
        photos = find_photos(storage.index_path())
        if photos:
            self._thumbnails.display(photos[0].path, self.ids.last_photo)
        else:
            self.ids.last_photo.texture = None

    def notice(self) -> None:
        widgets.notice()

    def _flash_state(self) -> str:
        return "on" if self.flash_on else "off"

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
