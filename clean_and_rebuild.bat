@echo off
echo === 清理缓存和重新打包 ===

echo 1. 清理buildozer缓存...
if exist .buildozer (
    rmdir /s /q .buildozer
    echo   .buildozer目录已删除
) else (
    echo   .buildozer目录不存在
)

echo 2. 清理bin目录...
if exist bin (
    rmdir /s /q bin
    echo   bin目录已删除
) else (
    echo   bin目录不存在
)

echo 3. 清理Python缓存...
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo   __pycache__目录已删除
)

for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
    )
)

echo 4. 开始打包APK...
buildozer android debug

echo 5. 检查打包结果...
if exist bin\*.apk (
    echo   ✓ APK打包成功！
    echo.
    echo   APK文件位置：
    dir bin\*.apk /b
) else (
    echo   ✗ APK打包失败
    echo   请检查上面的错误信息
)

echo.
echo === 完成 ===
pause