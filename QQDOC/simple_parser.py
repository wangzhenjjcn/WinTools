#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化腾讯文档解析器
"""

import requests
import json
import pandas as pd
import re
from typing import Dict, List, Optional
import os
from datetime import datetime

class SimpleTencentDocParser:
    def __init__(self, doc_url: str):
        self.doc_url = doc_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_doc_id(self) -> str:
        """从URL中提取文档ID"""
        pattern = r'/sheet/([A-Za-z0-9]+)'
        match = re.search(pattern, self.doc_url)
        if match:
            return match.group(1)
        raise ValueError("无法从URL中提取文档ID")
    
    def get_doc_data(self) -> Dict:
        """获取文档数据"""
        doc_id = self.extract_doc_id()
        
        # 尝试不同的API端点
        api_endpoints = [
            f"https://docs.qq.com/openapi/sheet/{doc_id}/data",
            f"https://docs.qq.com/sheet/{doc_id}/data",
        ]
        
        for endpoint in api_endpoints:
            try:
                print(f"尝试访问: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"访问 {endpoint} 失败: {e}")
                continue
        
        return {}
    
    def extract_pricing_data(self, doc_data: Dict) -> List[Dict]:
        """提取报价数据"""
        pricing_data = []
        
        try:
            sheets = doc_data.get('sheets', [])
            for sheet in sheets:
                sheet_name = sheet.get('name', '')
                if '三大件' in sheet_name:
                    print(f"找到三大件工作簿: {sheet_name}")
                    pricing_data.extend(self.parse_sheet_data(sheet))
            
            if not pricing_data:
                for sheet in sheets:
                    pricing_data.extend(self.parse_sheet_data(sheet))
                    
        except Exception as e:
            print(f"提取报价数据时出错: {e}")
        
        return pricing_data
    
    def parse_sheet_data(self, sheet: Dict) -> List[Dict]:
        """解析工作簿数据"""
        items = []
        
        try:
            table_data = sheet.get('data', [])
            if not table_data:
                return items
            
            headers = []
            for row in table_data:
                if any('型号' in str(cell) or '价格' in str(cell) for cell in row):
                    headers = row
                    break
            
            if not headers:
                headers = table_data[0] if table_data else []
            
            for row in table_data[1:]:
                if len(row) >= 2:
                    item = self.parse_row_data(row, headers)
                    if item:
                        items.append(item)
                        
        except Exception as e:
            print(f"解析工作簿数据时出错: {e}")
        
        return items
    
    def parse_row_data(self, row: List, headers: List) -> Optional[Dict]:
        """解析单行数据"""
        try:
            item = {}
            
            model_col = None
            price_col = None
            brand_col = None
            
            for i, header in enumerate(headers):
                header_str = str(header).lower()
                if '型号' in header_str:
                    model_col = i
                elif '价格' in header_str or '￥' in header_str:
                    price_col = i
                elif '品牌' in header_str:
                    brand_col = i
            
            if model_col is not None and model_col < len(row):
                item['型号'] = str(row[model_col]).strip()
            
            if brand_col is not None and brand_col < len(row):
                item['品牌'] = str(row[brand_col]).strip()
            
            if price_col is not None and price_col < len(row):
                price_str = str(row[price_col]).strip()
                price = self.clean_price(price_str)
                if price:
                    item['价格'] = price
            
            if not item.get('型号'):
                return None
                
            return item
            
        except Exception as e:
            print(f"解析行数据时出错: {e}")
            return None
    
    def clean_price(self, price_str: str) -> Optional[float]:
        """清理价格数据"""
        try:
            price_str = re.sub(r'[￥¥$,\s]', '', price_str)
            price_match = re.search(r'(\d+(?:\.\d+)?)', price_str)
            if price_match:
                return float(price_match.group(1))
            return None
        except:
            return None
    
    def save_to_excel(self, data: List[Dict], filename: str = None):
        """保存数据到Excel文件"""
        if not data:
            print("没有数据可保存")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"电脑配件报价_{timestamp}.xlsx"
        
        filepath = os.path.join("data", filename)
        
        try:
            df = pd.DataFrame(data)
            columns = ['品牌', '型号', '价格']
            df = df.reindex(columns=columns)
            df.to_excel(filepath, index=False, engine='openpyxl')
            print(f"数据已保存到: {filepath}")
            print(f"共保存 {len(data)} 条记录")
            
        except Exception as e:
            print(f"保存Excel文件时出错: {e}")
    
    def run(self):
        """运行解析程序"""
        print("开始解析腾讯文档...")
        print(f"文档地址: {self.doc_url}")
        
        doc_data = self.get_doc_data()
        
        if not doc_data:
            print("无法获取文档数据")
            return
        
        pricing_data = self.extract_pricing_data(doc_data)
        
        if not pricing_data:
            print("未找到报价数据")
            return
        
        self.save_to_excel(pricing_data)

def main():
    """主函数"""
    doc_url = "https://docs.qq.com/sheet/DUlFDb1NETFBaQU9p"
    
    parser = SimpleTencentDocParser(doc_url)
    parser.run()

if __name__ == "__main__":
    main() 