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

# 应用需求
requirements = python3,kivy==2.2.1,requests,plyer,pyjnius,sqlite3

# 支持的架构
android.archs = arm64-v8a,armeabi-v7a

# Android权限
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,POST_NOTIFICATIONS,SCHEDULE_EXACT_ALARM,ACCESS_NETWORK_STATE

# Android API版本
android.api = 31
android.minapi = 21
android.ndk = 25b

# 应用主题
android.presplash_color = #FFFFFF

# 启动屏幕
# android.presplash.filename = %(source.dir)s/data/presplash.png

# 应用图标
# android.icon.filename = %(source.dir)s/data/icon.png

# 方向支持
orientation = portrait

# 服务
# android.services = AnalysisService:service.py

# 是否为调试模式
# android.logcat_filters = *:S python:D

# 全屏模式
fullscreen = 0

# Android入口点
android.entrypoint = org.kivy.android.PythonActivity

# Android应用主题
# android.apptheme = "@android:style/Theme.NoTitleBar"

# 白名单
android.whitelist = lib-dynload/termios.so

# 黑名单
android.blacklist = openssl

# 添加Java类
# android.add_src = 

# Gradle依赖
android.gradle_dependencies = 

# Android AAR库
# android.add_aars = 

# Android额外的库
# android.add_libs_armeabi = 
# android.add_libs_armeabi_v7a = 
# android.add_libs_arm64_v8a = 
# android.add_libs_x86 = 
# android.add_libs_mips = 

# 复制库目录
# android.copy_libs = 1

# wakelock
android.wakelock = True

# Meta-data
# android.meta_data = 

# 库目录
# android.library_references = 

# 端口
# android.port = 

[buildozer]

# 日志级别 (0 = error only, 1 = info, 2 = debug)
log_level = 2

# 显示警告
warn_on_root = 1

# 构建目录
# build_dir = ./.buildozer

# bin目录
# bin_dir = ./bin
