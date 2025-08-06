@echo off
chcp 65001
echo 腾讯文档解析器启动中...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 安装依赖
echo 正在安装依赖包...
pip install -r requirements.txt

echo.
echo 请选择运行模式:
echo 1. 演示模式 (使用模拟数据)
echo 2. 真实模式 (尝试解析真实文档)
echo 3. 智能模式 (使用多种方法解析)
echo.
set /p choice="请输入选择 (1-3): "

if "%choice%"=="1" (
    echo.
    echo 运行演示模式...
    python demo_parser.py
) else if "%choice%"=="2" (
    echo.
    echo 运行真实模式...
    python xlsx.py
) else if "%choice%"=="3" (
    echo.
    echo 运行智能模式...
    python smart_parser.py
) else (
    echo 无效选择，运行演示模式...
    python demo_parser.py
)

echo.
echo 解析完成！
pause 