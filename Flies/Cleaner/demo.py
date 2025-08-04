#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件扫描器演示脚本
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from files_cleaner import FileCleaner

def show_demo_info():
    """显示演示信息"""
    info = """
文件扫描器演示

功能特点：
1. 全盘扫描 - 扫描所有系统盘的文件和文件夹
2. 智能分类 - 自动识别文件类型并用颜色区分
3. 启动项检测 - 高亮显示开机启动的可执行文件
4. 搜索过滤 - 支持按文件名和类型搜索过滤
5. 右键菜单 - 丰富的文件操作功能
6. 实时统计 - 显示文件总数和搜索结果

使用方法：
1. 点击"开始扫描"按钮开始扫描
2. 使用搜索框快速查找文件
3. 使用类型过滤器按文件类型查看
4. 右键点击文件进行各种操作
5. 查看右侧的启动项列表

注意事项：
- 首次扫描可能需要较长时间
- 建议在扫描前关闭其他占用磁盘的程序
- 删除文件操作不可恢复，请谨慎操作
"""
    return info

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 显示演示信息
    QMessageBox.information(None, "文件扫描器演示", show_demo_info())
    
    # 创建主窗口
    window = FileCleaner()
    window.setWindowTitle("文件扫描器 - 演示版")
    window.show()
    
    print("文件扫描器演示版已启动")
    print("请按照提示信息进行操作")
    
    return app.exec()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...") 
 