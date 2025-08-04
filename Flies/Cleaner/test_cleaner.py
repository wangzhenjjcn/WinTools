#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件扫描器测试脚本
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from files_cleaner import FileCleaner

def test_basic_functionality():
    """测试基本功能"""
    print("正在启动文件扫描器...")
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = FileCleaner()
    window.show()
    
    print("文件扫描器已启动，请测试以下功能：")
    print("1. 点击'开始扫描'按钮")
    print("2. 观察进度条和文件列表")
    print("3. 使用搜索框过滤文件")
    print("4. 右键点击文件测试菜单功能")
    print("5. 查看启动项列表")
    
    return app.exec()

if __name__ == "__main__":
    try:
        sys.exit(test_basic_functionality())
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...") 