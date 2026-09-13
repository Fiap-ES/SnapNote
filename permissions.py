from collections.abc import Callable

from kivy.clock import mainthread
from kivy.utils import platform

if platform == "android":
    from android.permissions import Permission, check_permission, request_permissions


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
