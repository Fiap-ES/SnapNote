import os
from pathlib import Path

# O bootstrap do python-for-android define ANDROID_ARGUMENT no ambiente; é o
# mesmo critério de kivy.utils.platform, sem trazer o Kivy para os casos de
# uso.
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

if ON_ANDROID:
    from android import mActivity
    from jnius import autoclass

    MediaScannerConnection = autoclass("android.media.MediaScannerConnection")


def notify(path: Path) -> None:
    # scanFile insere ou atualiza a entrada no MediaStore e, se o arquivo já
    # não existe, remove-a; por isso vale para criação, reescrita e exclusão.
    if ON_ANDROID:
        MediaScannerConnection.scanFile(
            mActivity.getApplicationContext(), [str(path)], None, None
        )
