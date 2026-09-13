[app]
title = SnapNote
package.name = snapnote
package.domain = br.com.fiap
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests, bin

requirements = python3,kivy,camera4kivy,gestures4kivy,pillow,piexif,kivymd==1.2.0
orientation = portrait
fullscreen = 0

android.permissions = CAMERA
android.api = 34
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

# Adiciona as dependências Gradle do CameraX e o código Java do provedor.
p4a.hook = camerax_provider/gradle_options.py

[buildozer]
log_level = 2
warn_on_root = 1
