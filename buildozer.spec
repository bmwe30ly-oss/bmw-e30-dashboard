[app]
title = BMW E30 Dashboard
package.name = bmwe30dashboard
package.domain = com.bmw.e30
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 2.0
requirements = python3==3.11.0,kivy==2.2.1,pillow
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_NETWORK_STATE,BLUETOOTH,BLUETOOTH_ADMIN,CHANGE_WIFI_STATE,ACCESS_WIFI_STATE,CAMERA,RECORD_AUDIO,WAKE_LOCK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.arch = armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
