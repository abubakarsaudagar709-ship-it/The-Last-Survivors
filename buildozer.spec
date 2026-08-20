[app]
title = The Last Survivors
package.name = thelastsurvivors
package.domain = org.plainstudios

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy

orientation = landscape
fullscreen = 1

icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
