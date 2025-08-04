@echo off
chcp 65001 >nul
title IP扫描器编译工具

echo ========================================
echo IP扫描器编译工具
echo ========================================
echo.
echo 选择编译方式：
echo 1. 完整编译（推荐）
echo 2. 快速编译
echo 3. 高级编译
echo.
set /p choice=请输入选择 (1-3): 

if "%choice%"=="1" (
    echo 启动完整编译...
    cd IP
    call build_exe.bat
) else if "%choice%"=="2" (
    echo 启动快速编译...
    cd IP
    call build_quick.bat
) else if "%choice%"=="3" (
    echo 启动高级编译...
    cd IP
    call build_advanced.bat
) else (
    echo 无效选择！
    pause
    exit /b 1
)

echo.
echo 编译完成！
pause 