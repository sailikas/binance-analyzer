[app]

# 应用标题
title = Binance Analyzer

# 包名
package.name = binanceanalyzer

# 包域名
package.domain = org.binance

# 源代码目录
source.dir = .

# 源代码包含的文件
source.include_exts = py,png,jpg,kv,atlas,json

# 应用版本
version = 1.0.0

# 应用需求 - 修复版本兼容性
requirements = python3==3.10.6,kivy==2.2.1,requests==2.31.0,plyer==2.1.0,pyjnius

# 支持的架构
android.archs = arm64-v8a,armeabi-v7a

# Android权限
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,POST_NOTIFICATIONS,SCHEDULE_EXACT_ALARM,ACCESS_NETWORK_STATE

# Android API版本
android.api = 31
android.minapi = 21
android.ndk = 25b
android.skip_update = False
android.accept_sdk_license = True

# 应用主题
android.presplash_color = #FFFFFF

# 方向支持
orientation = portrait

# 全屏模式
fullscreen = 0

# Android入口点
android.entrypoint = org.kivy.android.PythonActivity

# wakelock
android.wakelock = True

# 添加Python路径
android.add_src = .

# 私有存储
android.private_storage = True

# 日志级别
log_level = 2

[buildozer]

# 日志级别
log_level = 2

# 显示警告
warn_on_root = 1
