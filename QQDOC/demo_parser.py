#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示版腾讯文档解析器 - 使用模拟数据展示功能
"""

import pandas as pd
import re
from typing import Dict, List, Optional
import os
from datetime import datetime

class DemoTencentDocParser:
    def __init__(self, doc_url: str):
        self.doc_url = doc_url
        
    def get_mock_data(self) -> Dict:
        """获取模拟数据"""
        return {
            "sheets": [
                {
                    "name": "三大件",
                    "data": [
                        ["品牌", "型号", "价格", "备注"],
                        ["Intel", "i7-12700K", "2499", "12核20线程"],
                        ["Intel", "i5-12600K", "1899", "10核16线程"],
                        ["AMD", "Ryzen 7 5800X", "1999", "8核16线程"],
                        ["AMD", "Ryzen 5 5600X", "1499", "6核12线程"],
                        ["", "", "", ""],
                        ["金士顿", "DDR4 3200 16GB", "399", "单条"],
                        ["金士顿", "DDR4 3600 32GB", "799", "双条套装"],
                        ["海盗船", "DDR4 3200 16GB", "429", "单条"],
                        ["海盗船", "DDR4 3600 32GB", "859", "双条套装"],
                        ["", "", "", ""],
                        ["三星", "970 EVO Plus 1TB", "899", "NVMe"],
                        ["三星", "870 EVO 500GB", "499", "SATA"],
                        ["西数", "SN750 500GB", "499", "NVMe"],
                        ["西数", "SN750 1TB", "899", "NVMe"],
                        ["铠侠", "RC20 1TB", "599", "NVMe"],
                        ["铠侠", "RC20 500GB", "349", "NVMe"]
                    ]
                },
                {
                    "name": "主板",
                    "data": [
                        ["品牌", "型号", "价格", "芯片组"],
                        ["华硕", "ROG STRIX B660-A", "1299", "B660"],
                        ["微星", "MAG B660M MORTAR", "999", "B660"],
                        ["技嘉", "B660M AORUS PRO", "1099", "B660"],
                        ["华擎", "B660M Steel Legend", "899", "B660"]
                    ]
                },
                {
                    "name": "显卡",
                    "data": [
                        ["品牌", "型号", "价格", "显存"],
                        ["华硕", "RTX 4070 ROG STRIX", "4599", "12GB"],
                        ["微星", "RTX 4070 GAMING X", "4399", "12GB"],
                        ["技嘉", "RTX 4070 GAMING OC", "4499", "12GB"],
                        ["七彩虹", "RTX 4070 Advanced", "4199", "12GB"]
                    ]
                }
            ]
        }
    
    def extract_pricing_data(self, doc_data: Dict) -> List[Dict]:
        """提取报价数据"""
        pricing_data = []
        
        try:
            sheets = doc_data.get('sheets', [])
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
            filename = f"电脑配件报价_演示_{timestamp}.xlsx"
        
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
        print("开始演示解析腾讯文档...")
        print(f"文档地址: {self.doc_url}")
        print("注意: 这是演示版本，使用模拟数据")
        
        # 获取模拟数据
        doc_data = self.get_mock_data()
        
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
    
    parser = DemoTencentDocParser(doc_url)
    parser.run()

if __name__ == "__main__":
    main() 