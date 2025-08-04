@echo off
chcp 65001 >nul
title IP扫描器快速编译

echo 快速编译IP扫描器...

REM 当前已在IP目录

REM 安装PyInstaller（如果需要）
pip install pyinstaller --quiet

REM 编译
pyinstaller --onefile --windowed --name "IPScanner" --noconsole ip_scanner.py

if %errorlevel% equ 0 (
    echo 编译成功！文件位置：IP\dist\IPScanner.exe
) else (
    echo 编译失败！
)

pause 