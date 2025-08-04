@echo off
chcp 65001 >nul
title IP扫描器高级编译

echo ========================================
echo IP扫描器高级编译脚本
echo ========================================

echo.
echo 正在检查环境...

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未找到Python
    pause
    exit /b 1
)

REM 检查并安装依赖
echo 检查依赖包...
pip install pyinstaller PyQt6 --quiet

echo.
echo 开始编译...

REM 当前已在IP目录

REM 清理之前的编译文件
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del *.spec

REM 高级编译选项
pyinstaller ^
    --onefile ^
    --windowed ^
    --noconsole ^
    --name "IPScanner" ^
    --clean ^
    --optimize 2 ^
    --strip ^
    --exclude-module matplotlib ^
    --exclude-module numpy ^
    --exclude-module pandas ^
    --exclude-module scipy ^
    --exclude-module PIL ^
    --exclude-module cv2 ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import socket ^
    --hidden-import threading ^
    --hidden-import ipaddress ^
    --hidden-import re ^
    ip_scanner.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 编译成功！
    echo ========================================
    echo.
    echo 文件位置：IP\dist\IPScanner.exe
    echo.
    
    REM 显示文件信息
    if exist "dist\IPScanner.exe" (
        echo 文件大小：
        for %%A in ("dist\IPScanner.exe") do echo %%~zA 字节
        echo.
        echo 是否立即运行测试？(Y/N)
        set /p test_choice=
        if /i "%test_choice%"=="Y" (
            echo 启动程序...
            start "" "dist\IPScanner.exe"
        )
    )
) else (
    echo.
    echo 编译失败！请检查错误信息。
)

echo.
pause 