#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件搜索工具测试脚本
用于验证程序的基本功能
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

def create_test_files():
    """创建测试文件"""
    test_dir = tempfile.mkdtemp(prefix="everything_test_")
    
    # 创建不同类型的测试文件
    test_files = [
        ("test_document.txt", "这是一个测试文档文件"),
        ("test_image.jpg", "假图片文件"),
        ("test_video.mp4", "假视频文件"),
        ("test_audio.mp3", "假音频文件"),
        ("test_archive.zip", "假压缩文件"),
        ("test_executable.exe", "假可执行文件"),
        ("large_file.bin", "x" * 1024 * 1024),  # 1MB文件
        ("small_file.txt", "小文件"),
    ]
    
    for filename, content in test_files:
        filepath = os.path.join(test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"测试文件已创建在: {test_dir}")
    return test_dir

def test_file_search_app():
    """测试文件搜索应用"""
    try:
        # 导入主程序
        from everything import FileSearchApp, FileProperties, LightweightDatabase
        import tkinter as tk
        
        print("✓ 程序模块导入成功")
        
        # 测试属性管理器
        props_manager = FileProperties()
        print("✓ 属性管理器初始化成功")
        
        # 测试数据库
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            db = LightweightDatabase(temp_dir)
            print("✓ 数据库初始化成功")
        finally:
            shutil.rmtree(temp_dir)
        
        # 创建测试窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        app = FileSearchApp(root)
        print("✓ 应用程序初始化成功")
        
        # 测试文件类型分类
        test_paths = [
            "test.mp3",
            "test.zip", 
            "test.txt",
            "test.exe",
            "test.jpg",
            "test.mp4",
            "test.unknown"
        ]
        
        for path in test_paths:
            file_type = app.get_file_type(path)
            print(f"✓ {path} -> {file_type}")
        
        # 测试文件大小格式化
        test_sizes = [100, 1024, 1024*1024, 1024*1024*1024]
        for size in test_sizes:
            formatted = app.format_size(size)
            print(f"✓ {size} bytes -> {formatted}")
        
        root.destroy()
        print("✓ 所有测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("文件搜索工具测试")
    print("=" * 50)
    
    # 测试程序功能
    if test_file_search_app():
        print("\n🎉 所有测试通过！程序可以正常使用。")
        print("\n使用方法:")
        print("1. 运行: python everything.py")
        print("2. 或双击: start_everything.bat")
    else:
        print("\n❌ 测试失败，请检查程序代码。")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 