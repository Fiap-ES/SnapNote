from datetime import datetime

from camera4kivy import Preview
from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivymd.toast import toast

import storage
from library import CAPTURE_NAME_FORMAT, find_photos
from permissions import camera_permission_granted, photo_saving_allowed
from ui.thumbnail_loader import Thumbnail, ThumbnailLoader
from ui.widgets import SnapScreen

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
""")

PROTOTYPE_NOTICE = "Elemento ilustrativo, fora do escopo deste protótipo."


def timestamp_name() -> str:
    return datetime.now().strftime(CAPTURE_NAME_FORMAT)


class LastPhotoButton(ButtonBehavior, Thumbnail):
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

    def refresh_last_photo(self) -> None:
        photos = find_photos(storage.index_path())
        if photos:
            self._thumbnails.display(photos[0].path, self.ids.last_photo)
        else:
            self.ids.last_photo.texture = None

    def notice(self) -> None:
        toast(PROTOTYPE_NOTICE)

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
