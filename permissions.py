from collections.abc import Callable
from dataclasses import dataclass

from kivy.clock import mainthread
from kivy.utils import platform

if platform == "android":
    from android import api_version
    from android.permissions import Permission, check_permission, request_permissions

READ_MEDIA_VISUAL_USER_SELECTED = "android.permission.READ_MEDIA_VISUAL_USER_SELECTED"


@dataclass(frozen=True)
class PermissionStatus:
    camera: bool
    storage: bool


def storage_permission() -> str:
    # Até a API 28, gravar em DCIM exige WRITE_EXTERNAL_STORAGE. Da 29 em
    # diante o app cria e edita os próprios arquivos ali sem permissão e só
    # precisa de leitura para as demais fotos: READ_EXTERNAL_STORAGE até a
    # 32 e READ_MEDIA_IMAGES a partir da 33.
    if api_version >= 33:
        return Permission.READ_MEDIA_IMAGES
    if api_version >= 29:
        return Permission.READ_EXTERNAL_STORAGE
    return Permission.WRITE_EXTERNAL_STORAGE


def camera_permission_granted() -> bool:
    return platform != "android" or check_permission(Permission.CAMERA)


def storage_permission_granted() -> bool:
    if platform != "android":
        return True
    # No Android 14 o usuário pode conceder acesso parcial ("selecionar
    # fotos"): READ_MEDIA_IMAGES consta como negada, e pedi-la de novo
    # reabriria o diálogo a cada início.
    accepted = [storage_permission()]
    if api_version >= 34:
        accepted.append(READ_MEDIA_VISUAL_USER_SELECTED)
    return any(check_permission(permission) for permission in accepted)


def microphone_permission_granted() -> bool:
    return platform != "android" or check_permission(Permission.RECORD_AUDIO)


def photo_saving_allowed() -> bool:
    # Antes da API 29 a gravação em DCIM depende da permissão de escrita.
    return platform != "android" or api_version >= 29 or storage_permission_granted()


def current_status() -> PermissionStatus:
    return PermissionStatus(camera_permission_granted(), storage_permission_granted())


def request_app_permissions(on_result: Callable[[PermissionStatus], None]) -> None:
    status = current_status()
    if status.camera and status.storage:
        on_result(status)
        return
    wanted = {Permission.CAMERA: status.camera, storage_permission(): status.storage}
    missing = [permission for permission, granted in wanted.items() if not granted]
    _request(missing, lambda: on_result(current_status()))


def request_microphone_permission(on_result: Callable[[bool], None]) -> None:
    if microphone_permission_granted():
        on_result(True)
        return
    _request([Permission.RECORD_AUDIO], lambda: on_result(microphone_permission_granted()))


def _request(permissions: list[str], on_answered: Callable[[], None]) -> None:
    # O Android responde em uma thread Java e, se o diálogo for interrompido,
    # com listas vazias; por isso o estado real é consultado de novo, já na
    # thread do Kivy.
    @mainthread
    def deliver(_permissions: list[str], _grants: list[bool]) -> None:
        on_answered()

    request_permissions(permissions, deliver)
