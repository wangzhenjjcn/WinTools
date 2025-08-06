#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能腾讯文档解析器 - 处理JSONP数据加载
"""

import requests
import json
import pandas as pd
import re
from typing import Dict, List, Optional
import os
from datetime import datetime
import time

class SmartTencentDocParser:
    def __init__(self, doc_url: str):
        self.doc_url = doc_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_doc_id(self) -> str:
        """从URL中提取文档ID"""
        pattern = r'/sheet/([A-Za-z0-9]+)'
        match = re.search(pattern, self.doc_url)
        if match:
            return match.group(1)
        raise ValueError("无法从URL中提取文档ID")
    
    def get_doc_data_via_jsonp(self) -> Dict:
        """通过JSONP获取文档数据"""
        doc_id = self.extract_doc_id()
        
        # 构造JSONP请求URL
        jsonp_url = f"https://docs.qq.com/dop-api/opendoc"
        params = {
            'id': doc_id,
            'tab': '000001',  # 默认工作表
            'startrow': '0',
            'endrow': '1000',  # 获取更多行
            'needSheetState': '1',
            'sliceStates': '1',
            'normal': '1',
            'outformat': '1',
            'wb': '1',
            'nowb': '0',
            'callback': 'clientVarsCallback',
            't': str(int(time.time() * 1000))
        }
        
        try:
            print(f"尝试JSONP请求: {jsonp_url}")
            response = self.session.get(jsonp_url, params=params, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                print(f"JSONP响应长度: {len(content)}")
                
                # 尝试解析JSONP响应
                json_data = self.parse_jsonp_response(content)
                if json_data:
                    return json_data
                    
        except Exception as e:
            print(f"JSONP请求失败: {e}")
        
        return {}
    
    def parse_jsonp_response(self, content: str) -> Optional[Dict]:
        """解析JSONP响应"""
        try:
            # 查找JSONP回调函数的内容
            # 格式通常是: clientVarsCallback({...})
            pattern = r'clientVarsCallback\s*\(\s*({.*?})\s*\)'
            matches = re.findall(pattern, content, re.DOTALL)
            
            if matches:
                json_str = matches[0]
                # 处理HTML实体
                json_str = json_str.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                json_str = json_str.replace('&#34;', '"').replace('&#39;', "'")
                
                return json.loads(json_str)
                
        except Exception as e:
            print(f"解析JSONP响应失败: {e}")
        
        return None
    
    def get_doc_data_via_api(self) -> Dict:
        """通过API获取文档数据"""
        doc_id = self.extract_doc_id()
        
        # 尝试不同的API端点
        api_endpoints = [
            f"https://docs.qq.com/openapi/sheet/{doc_id}/data",
            f"https://docs.qq.com/sheet/{doc_id}/data",
            f"https://docs.qq.com/api/sheet/{doc_id}",
        ]
        
        for endpoint in api_endpoints:
            try:
                print(f"尝试API请求: {endpoint}")
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"API请求失败 {endpoint}: {e}")
                continue
        
        return {}
    
    def get_doc_data(self) -> Dict:
        """获取文档数据"""
        # 首先尝试JSONP方式
        doc_data = self.get_doc_data_via_jsonp()
        if doc_data:
            return doc_data
        
        # 如果JSONP失败，尝试API方式
        doc_data = self.get_doc_data_via_api()
        if doc_data:
            return doc_data
        
        # 如果都失败，返回空数据
        return {}
    
    def extract_pricing_data(self, doc_data: Dict) -> List[Dict]:
        """提取报价数据"""
        pricing_data = []
        
        try:
            # 查找工作表数据
            sheets = doc_data.get('sheets', [])
            if not sheets:
                # 尝试其他可能的数据结构
                sheets = doc_data.get('data', {}).get('sheets', [])
            
            print(f"找到 {len(sheets)} 个工作表")
            
            for sheet in sheets:
                sheet_name = sheet.get('name', '')
                print(f"处理工作表: {sheet_name}")
                
                # 检查是否是三大件相关的工作表
                if any(keyword in sheet_name for keyword in ['三大件', 'CPU', '内存', '存储', '硬盘']):
                    print(f"找到相关工作表: {sheet_name}")
                    items = self.parse_sheet_data(sheet)
                    pricing_data.extend(items)
                else:
                    # 也处理其他工作表，以防万一
                    items = self.parse_sheet_data(sheet)
                    if items:  # 如果找到数据，也添加
                        pricing_data.extend(items)
                        
        except Exception as e:
            print(f"提取报价数据时出错: {e}")
        
        return pricing_data
    
    def parse_sheet_data(self, sheet: Dict) -> List[Dict]:
        """解析工作表数据"""
        items = []
        
        try:
            # 获取表格数据
            table_data = sheet.get('data', [])
            if not table_data:
                return items
            
            print(f"工作表 {sheet.get('name', '未知')} 包含 {len(table_data)} 行数据")
            
            # 查找表头
            headers = []
            for row in table_data:
                if any(self.is_header_cell(cell) for cell in row):
                    headers = row
                    break
            
            if not headers and table_data:
                headers = table_data[0]
            
            print(f"表头: {headers}")
            
            # 解析数据行
            for i, row in enumerate(table_data[1:], 1):  # 跳过表头
                if len(row) >= 2:  # 至少需要型号和价格两列
                    item = self.parse_row_data(row, headers)
                    if item:
                        items.append(item)
                        if len(items) <= 5:  # 只打印前5条用于调试
                            print(f"解析行 {i}: {item}")
            
            print(f"从工作表 {sheet.get('name', '未知')} 提取了 {len(items)} 条记录")
            
        except Exception as e:
            print(f"解析工作表数据时出错: {e}")
        
        return items
    
    def is_header_cell(self, cell: str) -> bool:
        """判断是否为表头单元格"""
        cell_lower = str(cell).lower()
        header_keywords = ['型号', 'model', '价格', 'price', '品牌', 'brand', '规格', 'spec']
        return any(keyword in cell_lower for keyword in header_keywords)
    
    def parse_row_data(self, row: List, headers: List) -> Optional[Dict]:
        """解析单行数据"""
        try:
            item = {}
            
            # 查找关键列
            model_col = None
            price_col = None
            brand_col = None
            
            for i, header in enumerate(headers):
                header_str = str(header).lower()
                if '型号' in header_str or 'model' in header_str:
                    model_col = i
                elif '价格' in header_str or 'price' in header_str or '￥' in header_str or '¥' in header_str:
                    price_col = i
                elif '品牌' in header_str or 'brand' in header_str:
                    brand_col = i
            
            # 提取数据
            if model_col is not None and model_col < len(row):
                model = str(row[model_col]).strip()
                if model and model != 'nan':
                    item['型号'] = model
            
            if brand_col is not None and brand_col < len(row):
                brand = str(row[brand_col]).strip()
                if brand and brand != 'nan':
                    item['品牌'] = brand
            
            if price_col is not None and price_col < len(row):
                price_str = str(row[price_col]).strip()
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
            if not price_str or price_str.lower() in ['nan', 'none', '']:
                return None
            
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
        print("开始智能解析腾讯文档...")
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
    
    parser = SmartTencentDocParser(doc_url)
    parser.run()

if __name__ == "__main__":
    main() 