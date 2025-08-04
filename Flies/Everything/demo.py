#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件搜索工具演示脚本
展示增强版功能
"""

import os
import tempfile
import shutil
from pathlib import Path

def create_demo_files():
    """创建演示文件"""
    demo_dir = Path("demo_files")
    demo_dir.mkdir(exist_ok=True)
    
    # 创建不同类型的演示文件
    demo_files = [
        ("demo_document.txt", "这是一个演示文档文件\n包含多行文本\n用于测试文档属性"),
        ("demo_image.jpg", "假图片文件内容"),
        ("demo_video.mp4", "假视频文件内容"),
        ("demo_audio.mp3", "假音频文件内容"),
        ("demo_archive.zip", "假压缩文件内容"),
        ("demo_executable.exe", "假可执行文件内容"),
        ("large_demo_file.bin", "x" * 1024 * 1024),  # 1MB文件
        ("small_demo_file.txt", "小文件内容"),
        ("hidden_file.txt", "隐藏文件内容"),
        ("readonly_file.txt", "只读文件内容"),
    ]
    
    for filename, content in demo_files:
        filepath = demo_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"演示文件已创建在: {demo_dir}")
    return demo_dir

def demo_properties():
    """演示属性系统"""
    print("\n" + "="*50)
    print("文件属性系统演示")
    print("="*50)
    
    from everything import FileProperties
    
    props_manager = FileProperties()
    
    # 创建测试文件
    test_file = "demo_test.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件\n用于演示属性系统")
    
    try:
        # 获取文件属性
        properties = props_manager.get_file_properties(test_file)
        
        print("文件属性:")
        for key, value in properties.items():
            if key != 'properties':  # 跳过嵌套属性
                print(f"  {key}: {value}")
        
        # 显示特定属性
        if 'properties' in properties:
            print("\n详细属性:")
            for prop_name, prop_value in properties['properties'].items():
                print(f"  {prop_name}: {prop_value}")
                
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

def demo_database():
    """演示数据库功能"""
    print("\n" + "="*50)
    print("数据库功能演示")
    print("="*50)
    
    from everything import LightweightDatabase
    
    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    try:
        db = LightweightDatabase(temp_dir)
        print(f"✓ 数据库初始化成功: {temp_dir}")
        
        # 添加测试文件
        test_file_info = {
            'name': 'test.txt',
            'path': '/path/to/test.txt',
            'size': 1024,
            'type': '文档',
            'created': datetime.now(),
            'modified': datetime.now(),
            'accessed': datetime.now(),
            'attributes': 'R',
            'hash': 'abc123',
            'properties': {
                'line_count': 10,
                'word_count': 50,
                'char_count': 200
            }
        }
        
        if db.add_file(test_file_info):
            print("✓ 文件添加成功")
        
        # 搜索文件
        results = db.search_files("test")
        print(f"✓ 搜索到 {len(results)} 个文件")
        
        # 获取文件数量
        count = db.get_file_count()
        print(f"✓ 数据库中共有 {count} 个文件")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

def demo_app():
    """演示应用程序"""
    print("\n" + "="*50)
    print("应用程序演示")
    print("="*50)
    
    import tkinter as tk
    from everything import FileSearchApp
    
    # 创建演示窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    app = FileSearchApp(root)
    print("✓ 应用程序初始化成功")
    
    # 演示文件类型分类
    test_files = [
        "demo.mp3", "demo.zip", "demo.txt", "demo.exe",
        "demo.jpg", "demo.mp4", "demo.unknown"
    ]
    
    print("\n文件类型分类:")
    for file in test_files:
        file_type = app.get_file_type(file)
        print(f"  {file} -> {file_type}")
    
    # 演示文件大小格式化
    test_sizes = [100, 1024, 1024*1024, 1024*1024*1024]
    print("\n文件大小格式化:")
    for size in test_sizes:
        formatted = app.format_size(size)
        print(f"  {size} bytes -> {formatted}")
    
    root.destroy()
    print("✓ 应用程序演示完成")

def main():
    """主演示函数"""
    print("文件搜索工具 - Everything (增强版)")
    print("功能演示")
    print("="*50)
    
    # 创建演示文件
    demo_dir = create_demo_files()
    
    try:
        # 演示各个功能
        demo_properties()
        demo_database()
        demo_app()
        
        print("\n" + "="*50)
        print("🎉 所有演示完成！")
        print("\n使用方法:")
        print("1. 运行: python everything.py")
        print("2. 或双击: start_everything.bat")
        print("3. 选择索引目录开始使用")
        print("="*50)
        
    finally:
        # 清理演示文件
        if demo_dir.exists():
            shutil.rmtree(demo_dir)
            print(f"\n已清理演示文件: {demo_dir}")

if __name__ == "__main__":
    from datetime import datetime
    main() 