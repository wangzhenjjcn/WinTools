@echo off
chcp 65001 >nul
title IP扫描器编译工具

echo ========================================
echo IP扫描器自动编译脚本
echo ========================================

echo.
echo 正在检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python环境，请先安装Python
    pause
    exit /b 1
)

echo.
echo 正在检查PyInstaller...
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo 错误：PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo.
echo 正在检查PyQt6...
python -c "import PyQt6" 2>nul
if %errorlevel% neq 0 (
    echo 正在安装PyQt6...
    pip install PyQt6
    if %errorlevel% neq 0 (
        echo 错误：PyQt6安装失败
        pause
        exit /b 1
    )
)

echo.
echo 开始编译IP扫描器...
echo.

REM 当前已在IP目录

REM 使用PyInstaller编译
pyinstaller --onefile ^
            --windowed ^
            --name "IPScanner" ^
            --icon=NONE ^
            --add-data "README_scanner.md;." ^
            --hidden-import PyQt6.QtCore ^
            --hidden-import PyQt6.QtWidgets ^
            --hidden-import PyQt6.QtGui ^
            --hidden-import socket ^
            --hidden-import threading ^
            --hidden-import ipaddress ^
            ip_scanner.py

if %errorlevel% neq 0 (
    echo.
    echo 错误：编译失败！
    pause
    exit /b 1
)

echo.
echo 编译完成！
echo.

REM 检查生成的文件
if exist "dist\IPScanner.exe" (
    echo 成功生成：dist\IPScanner.exe
    echo.
    echo 文件大小：
    dir "dist\IPScanner.exe" | find "IPScanner.exe"
    echo.
    echo 是否要运行测试？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        echo 正在启动程序进行测试...
        start "" "dist\IPScanner.exe"
    )
) else (
    echo 错误：未找到生成的exe文件
)

echo.
echo 编译过程完成！
pause 