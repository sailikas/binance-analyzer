[app]

title = Binance Analyzer
package.name = binanceanalyzer
package.domain = org.binance
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
version = 1.0.0
requirements = python3,kivy==2.2.1,requests,plyer,pyjnius,sqlite3
android.archs = arm64-v8a,armeabi-v7a
android.add_src = .
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,POST_NOTIFICATIONS,SCHEDULE_EXACT_ALARM,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True
android.presplash_color = #FFFFFF
orientation = portrait
fullscreen = 0
android.entrypoint = org.kivy.android.PythonActivity
android.wakelock = True
android.private_storage = True
log_level = 2

[buildozer]

log_level = 2
warn_on_root = 1

