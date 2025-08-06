#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件扫描器简化测试脚本
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from files_cleaner import FileCleaner

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 显示测试信息
    QMessageBox.information(None, "测试信息", 
        "文件扫描器测试\n\n"
        "修复内容：\n"
        "1. 解决了Qt线程错误问题\n"
        "2. 使用分批处理替代多线程\n"
        "3. 保持界面响应性和扫描效率\n\n"
        "测试步骤：\n"
        "1. 点击开始扫描\n"
        "2. 观察进度条和文件列表\n"
        "3. 测试搜索和过滤功能\n"
        "4. 测试右键菜单功能")
    
    # 创建主窗口
    window = FileCleaner()
    window.setWindowTitle("文件扫描器 - 测试版")
    window.show()
    
    print("文件扫描器测试版已启动")
    print("请测试各项功能是否正常工作")
    
    return app.exec()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...") 