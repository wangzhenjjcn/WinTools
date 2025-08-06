#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试版腾讯文档解析器
"""

import requests
import json
import pandas as pd
import re
from typing import Dict, List, Optional
import os
from datetime import datetime

def test_tencent_doc():
    """测试腾讯文档访问"""
    doc_url = "https://docs.qq.com/sheet/DUlFDb1NETFBaQU9p"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    try:
        print(f"正在访问: {doc_url}")
        response = session.get(doc_url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            content = response.text
            print(f"页面内容长度: {len(content)}")
            
            # 查找JSON数据
            json_patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
                r'data:\s*({.*?})\s*,',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                print(f"找到 {len(matches)} 个JSON匹配")
                for i, match in enumerate(matches):
                    try:
                        json_data = json.loads(match)
                        print(f"JSON数据 {i+1}: {list(json_data.keys())}")
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误 {i+1}: {e}")
            
            # 保存页面内容用于调试
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("页面内容已保存到 debug_page.html")
            
        else:
            print(f"访问失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"访问失败: {e}")

def create_sample_data():
    """创建示例数据用于测试"""
    sample_data = [
        {"品牌": "Intel", "型号": "i7-12700K", "价格": 2499.0},
        {"品牌": "AMD", "型号": "Ryzen 7 5800X", "价格": 1999.0},
        {"品牌": "金士顿", "型号": "DDR4 3200 16GB", "价格": 399.0},
        {"品牌": "三星", "型号": "970 EVO Plus 1TB", "价格": 899.0},
        {"品牌": "西数", "型号": "SN750 500GB", "价格": 499.0},
    ]
    
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    # 保存示例数据
    df = pd.DataFrame(sample_data)
    filename = f"示例报价_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join("data", filename)
    
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"示例数据已保存到: {filepath}")
    print(f"共保存 {len(sample_data)} 条记录")

def main():
    """主函数"""
    print("=== 腾讯文档解析器测试 ===")
    
    # 测试文档访问
    test_tencent_doc()
    
    print("\n=== 创建示例数据 ===")
    create_sample_data()
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 