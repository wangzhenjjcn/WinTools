@echo off
chcp 65001 >nul
title 安装文件搜索工具依赖包

echo ========================================
echo 文件搜索工具 - Everything (增强版)
echo 依赖包安装脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    pause
    exit /b 1
)

echo.
echo 正在安装可选依赖包...
echo.

echo 1. 安装 pywin32 (Windows API支持)...
pip install pywin32

echo.
echo 2. 安装 Pillow (图片处理)...
pip install Pillow

echo.
echo 3. 安装 mutagen (音频文件属性)...
pip install mutagen

echo.
echo 4. 安装 opencv-python (视频文件属性)...
pip install opencv-python

echo.
echo ========================================
echo 依赖包安装完成！
echo.
echo 现在可以运行程序了：
echo 1. 双击 start_everything.bat
echo 2. 或运行 python everything.py
echo ========================================
echo.
pause 