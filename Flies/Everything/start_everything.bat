@echo off
chcp 65001 >nul
title 文件搜索工具 - Everything

echo 正在启动文件搜索工具...
echo.

python everything.py

if errorlevel 1 (
    echo.
    echo 错误: 程序运行失败
    echo 请确保已安装Python和tkinter模块
    pause
) 