#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档解析器 - 电脑配件报价表解析
解析 https://docs.qq.com/sheet/DUlFDb1NETFBaQU9p 中的报价信息
"""

import requests
import json
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
import os
from datetime import datetime
import time

class TencentDocParser:
    def __init__(self, doc_url: str):
        self.doc_url = doc_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
            f"https://docs.qq.com/api/sheet/{doc_id}"
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
        
        # 如果API访问失败，尝试解析网页内容
        return self.parse_webpage_content()
    
    def parse_webpage_content(self) -> Dict:
        """解析网页内容获取数据"""
        try:
            response = self.session.get(self.doc_url, timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # 查找JSON数据
                json_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
                    r'data:\s*({.*?})\s*,',
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    for match in matches:
                        try:
                            return json.loads(match)
                        except json.JSONDecodeError:
                            continue
                
                # 如果找不到JSON，尝试解析HTML表格
                return self.parse_html_tables(content)
                
        except Exception as e:
            print(f"解析网页内容失败: {e}")
        
        return {}
    
    def parse_html_tables(self, html_content: str) -> Dict:
        """解析HTML表格内容"""
        # 这里可以添加HTML表格解析逻辑
        # 由于腾讯文档的复杂性，这里提供一个基础框架
        return {"tables": [], "sheets": []}
    
    def extract_pricing_data(self, doc_data: Dict) -> List[Dict]:
        """提取报价数据"""
        pricing_data = []
        
        try:
            # 查找"三大件"工作簿
            sheets = doc_data.get('sheets', [])
            for sheet in sheets:
                sheet_name = sheet.get('name', '')
                if '三大件' in sheet_name:
                    print(f"找到三大件工作簿: {sheet_name}")
                    pricing_data.extend(self.parse_sheet_data(sheet))
            
            # 如果没有找到"三大件"，尝试解析所有工作簿
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
            # 获取表格数据
            table_data = sheet.get('data', [])
            if not table_data:
                return items
            
            # 查找表头
            headers = []
            for row in table_data:
                if any('型号' in str(cell) or '价格' in str(cell) or '品牌' in str(cell) for cell in row):
                    headers = row
                    break
            
            if not headers:
                # 如果没有找到明确的表头，使用第一行
                headers = table_data[0] if table_data else []
            
            # 解析数据行
            for row in table_data[1:]:  # 跳过表头
                if len(row) >= 2:  # 至少需要型号和价格两列
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
            
            # 查找型号列
            model_col = None
            price_col = None
            brand_col = None
            
            for i, header in enumerate(headers):
                header_str = str(header).lower()
                if '型号' in header_str or 'model' in header_str:
                    model_col = i
                elif '价格' in header_str or 'price' in header_str or '￥' in header_str:
                    price_col = i
                elif '品牌' in header_str or 'brand' in header_str:
                    brand_col = i
            
            # 提取数据
            if model_col is not None and model_col < len(row):
                item['型号'] = str(row[model_col]).strip()
            
            if brand_col is not None and brand_col < len(row):
                item['品牌'] = str(row[brand_col]).strip()
            
            if price_col is not None and price_col < len(row):
                price_str = str(row[price_col]).strip()
                # 清理价格数据
                price = self.clean_price(price_str)
                if price:
                    item['价格'] = price
            
            # 如果型号为空，跳过
            if not item.get('型号'):
                return None
                
            return item
            
        except Exception as e:
            print(f"解析行数据时出错: {e}")
            return None
    
    def clean_price(self, price_str: str) -> Optional[float]:
        """清理价格数据"""
        try:
            # 移除货币符号和空格
            price_str = re.sub(r'[￥¥$,\s]', '', price_str)
            
            # 提取数字
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
            # 创建DataFrame
            df = pd.DataFrame(data)
            
            # 重新排列列顺序
            columns = ['品牌', '型号', '价格']
            df = df.reindex(columns=columns)
            
            # 保存到Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            print(f"数据已保存到: {filepath}")
            print(f"共保存 {len(data)} 条记录")
            
            # 显示统计信息
            self.show_statistics(df)
            
        except Exception as e:
            print(f"保存Excel文件时出错: {e}")
    
    def show_statistics(self, df: pd.DataFrame):
        """显示统计信息"""
        print("\n=== 统计信息 ===")
        print(f"总记录数: {len(df)}")
        
        if '品牌' in df.columns:
            brand_counts = df['品牌'].value_counts()
            print(f"\n品牌分布:")
            for brand, count in brand_counts.head(10).items():
                print(f"  {brand}: {count}条")
        
        if '价格' in df.columns:
            price_df = df[df['价格'].notna()]
            if len(price_df) > 0:
                print(f"\n价格统计:")
                print(f"  有价格记录: {len(price_df)}条")
                print(f"  价格范围: {price_df['价格'].min():.2f} - {price_df['价格'].max():.2f}")
                print(f"  平均价格: {price_df['价格'].mean():.2f}")
    
    def run(self):
        """运行解析程序"""
        print("开始解析腾讯文档...")
        print(f"文档地址: {self.doc_url}")
        
        # 获取文档数据
        doc_data = self.get_doc_data()
        
        if not doc_data:
            print("无法获取文档数据")
            return
        
        # 提取报价数据
        pricing_data = self.extract_pricing_data(doc_data)
        
        if not pricing_data:
            print("未找到报价数据")
            return
        
        # 保存到Excel
        self.save_to_excel(pricing_data)

def main():
    """主函数"""
    doc_url = "https://docs.qq.com/sheet/DUlFDb1NETFBaQU9p"
    
    parser = TencentDocParser(doc_url)
    parser.run()

if __name__ == "__main__":
    main()
