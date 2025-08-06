@echo off
chcp 65001 >nul
echo ========================================
echo        文件扫描器 - 管理员模式
echo ========================================
echo.

echo 正在以管理员权限启动文件扫描器...
powershell -Command "Start-Process python -ArgumentList 'files_cleaner.py' -Verb RunAs"

if errorlevel 1 (
    echo 错误: 无法以管理员权限启动程序
    echo 请手动右键点击程序，选择"以管理员身份运行"
    pause
) 