@echo off
chcp 65001 >nul
echo ========================================
echo           文件扫描器启动器
echo ========================================
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python 3.7+
    pause
    exit /b 1
)

echo 检查PyQt6依赖...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyQt6依赖...
    pip install PyQt6>=6.4.0
    if errorlevel 1 (
        echo 错误: PyQt6安装失败
        pause
        exit /b 1
    )
)

echo 启动文件扫描器...
python files_cleaner.py

if errorlevel 1 (
    echo 程序运行出错，请检查错误信息
    pause
) 