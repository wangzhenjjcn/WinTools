#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件搜索工具排序功能演示
展示属性排序功能
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

def create_sort_demo_files():
    """创建排序演示文件"""
    demo_dir = Path("sort_demo_files")
    demo_dir.mkdir(exist_ok=True)
    
    # 创建不同大小和类型的文件
    demo_files = [
        ("small_file.txt", "小文件", 100),
        ("medium_file.txt", "中等文件" * 100, 1024),
        ("large_file.txt", "大文件" * 1000, 1024 * 1024),
        ("hidden_file.txt", "隐藏文件", 500),
        ("readonly_file.txt", "只读文件", 800),
        ("system_file.txt", "系统文件", 600),
        ("very_long_filename_that_exceeds_normal_length.txt", "长文件名文件", 300),
        ("short.txt", "短文件名", 200),
        ("document.pdf", "PDF文档", 1500),
        ("image.jpg", "图片文件", 2000),
        ("video.mp4", "视频文件", 5000),
        ("audio.mp3", "音频文件", 3000),
        ("archive.zip", "压缩文件", 4000),
        ("executable.exe", "可执行文件", 2500),
        ("script.py", "Python脚本", 1200),
    ]
    
    for filename, content, size in demo_files:
        filepath = demo_dir / filename
        # 创建指定大小的文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            # 填充到指定大小
            while os.path.getsize(filepath) < size:
                f.write("x")
    
    print(f"排序演示文件已创建在: {demo_dir}")
    return demo_dir

def demo_property_sorter():
    """演示属性排序器"""
    print("\n" + "="*50)
    print("属性排序器演示")
    print("="*50)
    
    from everything import PropertySorter
    
    sorter = PropertySorter()
    
    # 创建测试文件信息
    test_files = [
        {
            'name': 'small.txt',
            'size': 100,
            'type': '文档',
            'created': datetime.now(),
            'modified': datetime.now(),
            'attributes': '',
            'hash': 'abc12345',
            'is_hidden': False,
            'is_readonly': False,
            'is_system': False
        },
        {
            'name': 'large.txt',
            'size': 1024 * 1024,
            'type': '文档',
            'created': datetime.now(),
            'modified': datetime.now(),
            'attributes': 'R',
            'hash': 'def67890',
            'is_hidden': False,
            'is_readonly': True,
            'is_system': False
        },
        {
            'name': 'hidden.txt',
            'size': 500,
            'type': '文档',
            'created': datetime.now(),
            'modified': datetime.now(),
            'attributes': 'H',
            'hash': 'ghi11111',
            'is_hidden': True,
            'is_readonly': False,
            'is_system': False
        }
    ]
    
    print("原始文件列表:")
    for i, file_info in enumerate(test_files, 1):
        print(f"  {i}. {file_info['name']} - {file_info['size']} bytes - {file_info['attributes']}")
    
    # 演示按大小排序
    print("\n按大小排序 (升序):")
    sorted_by_size = sorter.sort_files(test_files, 'size', False)
    for i, file_info in enumerate(sorted_by_size, 1):
        print(f"  {i}. {file_info['name']} - {file_info['size']} bytes")
    
    # 演示按文件名长度排序
    print("\n按文件名长度排序 (升序):")
    sorted_by_length = sorter.sort_files(test_files, 'length', False)
    for i, file_info in enumerate(sorted_by_length, 1):
        print(f"  {i}. {file_info['name']} - 长度: {len(file_info['name'])}")
    
    # 演示按属性排序
    print("\n按文件属性排序 (升序):")
    sorted_by_attrs = sorter.sort_files(test_files, 'attributes', False)
    for i, file_info in enumerate(sorted_by_attrs, 1):
        print(f"  {i}. {file_info['name']} - 属性: '{file_info['attributes']}'")
    
    # 演示按哈希值排序
    print("\n按哈希值排序 (升序):")
    sorted_by_hash = sorter.sort_files(test_files, 'hash', False)
    for i, file_info in enumerate(sorted_by_hash, 1):
        print(f"  {i}. {file_info['name']} - 哈希: {file_info['hash']}")

def demo_sortable_properties():
    """演示可排序属性"""
    print("\n" + "="*50)
    print("可排序属性列表")
    print("="*50)
    
    from everything import PropertySorter
    
    sorter = PropertySorter()
    
    print("支持排序的属性:")
    for i, (prop_key, prop_desc) in enumerate(sorter.sortable_properties.items(), 1):
        print(f"  {i:2d}. {prop_key:15s} - {prop_desc}")
    
    print(f"\n总共支持 {len(sorter.sortable_properties)} 种属性排序")

def demo_advanced_sorting():
    """演示高级排序功能"""
    print("\n" + "="*50)
    print("高级排序功能演示")
    print("="*50)
    
    print("高级排序功能包括:")
    print("  1. 点击列标题进行快速排序")
    print("  2. 排序方向指示器 (↑ 升序, ↓ 降序)")
    print("  3. 高级排序对话框")
    print("  4. 支持15种不同属性的排序")
    print("  5. 实时排序更新")
    
    print("\n排序属性说明:")
    sort_props = {
        'name': '按文件名排序',
        'path': '按完整路径排序',
        'size': '按文件大小排序',
        'type': '按文件类型排序',
        'modified': '按修改时间排序',
        'created': '按创建时间排序',
        'length': '按文件名长度排序',
        'attributes': '按文件属性排序',
        'hash': '按哈希值排序',
        'extension': '按文件扩展名排序',
        'size_on_disk': '按磁盘占用大小排序',
        'accessed': '按访问时间排序',
        'is_hidden': '按是否隐藏排序',
        'is_readonly': '按是否只读排序',
        'is_system': '按是否系统文件排序'
    }
    
    for prop, desc in sort_props.items():
        print(f"  • {prop:15s} - {desc}")

def main():
    """主演示函数"""
    print("文件搜索工具 - Everything (增强版)")
    print("排序功能演示")
    print("="*50)
    
    # 创建演示文件
    demo_dir = create_sort_demo_files()
    
    try:
        # 演示各个排序功能
        demo_property_sorter()
        demo_sortable_properties()
        demo_advanced_sorting()
        
        print("\n" + "="*50)
        print("🎉 排序功能演示完成！")
        print("\n使用方法:")
        print("1. 运行: python everything.py")
        print("2. 点击列标题进行排序")
        print("3. 使用 '工具' → '高级排序' 进行复杂排序")
        print("4. 观察排序方向指示器")
        print("="*50)
        
    finally:
        # 清理演示文件
        if demo_dir.exists():
            shutil.rmtree(demo_dir)
            print(f"\n已清理演示文件: {demo_dir}")

if __name__ == "__main__":
    main() 