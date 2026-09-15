[app]
title = SnapNote
package.name = snapnote
package.domain = br.com.fiap
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests, bin

requirements = python3,kivy,camera4kivy,gestures4kivy,pillow,piexif,kivymd==1.2.0
orientation = portrait
fullscreen = 0

android.permissions = CAMERA, (name=android.permission.WRITE_EXTERNAL_STORAGE;maxSdkVersion=28), (name=android.permission.READ_EXTERNAL_STORAGE;maxSdkVersion=32), android.permission.READ_MEDIA_IMAGES, android.permission.READ_MEDIA_VISUAL_USER_SELECTED, android.permission.RECORD_AUDIO
android.api = 34
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

# Adiciona as dependências Gradle do CameraX e o código Java do provedor.
p4a.hook = camerax_provider/gradle_options.py

# Visibilidade do serviço de reconhecimento de voz, exigida a partir do
# Android 11 para o SpeechRecognizer encontrar o reconhecedor do sistema.
android.extra_manifest_xml = manifest/speech_queries.xml

[buildozer]
log_level = 2
warn_on_root = 1
