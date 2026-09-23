[app]
title = SnapNote
package.name = snapnote
package.domain = br.com.fiap
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests, bin

# openssl e certifi atendem à chamada HTTPS ao Gemini: o pacote de
# certificados do certifi supre o que o Android não expõe ao OpenSSL.
requirements = python3,kivy,camera4kivy,gestures4kivy,pillow,piexif,kivymd==1.2.0,openssl,certifi
orientation = portrait
fullscreen = 0

# A descrição da foto pelo Gemini exige INTERNET; ACCESS_NETWORK_STATE
# permite saber se há rede antes de tentar o envio.
android.permissions = CAMERA, (name=android.permission.WRITE_EXTERNAL_STORAGE;maxSdkVersion=28), (name=android.permission.READ_EXTERNAL_STORAGE;maxSdkVersion=32), android.permission.READ_MEDIA_IMAGES, android.permission.READ_MEDIA_VISUAL_USER_SELECTED, android.permission.RECORD_AUDIO, android.permission.INTERNET, android.permission.ACCESS_NETWORK_STATE
android.api = 34
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

# Adiciona as dependências Gradle do CameraX e o código Java do provedor.
p4a.hook = camerax_provider/gradle_options.py

# Reconhecimento de texto do ML Kit com modelo embarcado (sem rede). O hook
# acima preserva estas dependências e acrescenta só as do CameraX.
android.gradle_dependencies = com.google.mlkit:text-recognition:16.0.0

# Visibilidade do serviço de reconhecimento de voz, exigida a partir do
# Android 11 para o SpeechRecognizer encontrar o reconhecedor do sistema.
android.extra_manifest_xml = manifest/speech_queries.xml

[buildozer]
log_level = 2
warn_on_root = 1
