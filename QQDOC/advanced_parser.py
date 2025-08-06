#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级腾讯文档解析器 - 使用Selenium处理动态内容
"""

import time
import json
import pandas as pd
import re
from typing import Dict, List, Optional
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class AdvancedTencentDocParser:
    def __init__(self, doc_url: str):
        self.doc_url = doc_url
        self.driver = None
        
    def setup_driver(self):
        """设置Chrome浏览器驱动"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Chrome浏览器驱动设置成功")
            return True
        except Exception as e:
            print(f"设置Chrome浏览器驱动失败: {e}")
            return False
    
    def get_page_content(self) -> str:
        """获取页面内容"""
        try:
            print(f"正在访问: {self.doc_url}")
            self.driver.get(self.doc_url)
            time.sleep(5)
            page_source = self.driver.page_source
            return page_source
        except Exception as e:
            print(f"获取页面内容失败: {e}")
            return ""
    
    def extract_data_from_page(self, page_source: str) -> Dict:
        """从页面源码中提取数据"""
        data = {"sheets": []}
        
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # 查找所有表格
            tables = soup.find_all('table')
            print(f"找到 {len(tables)} 个表格")
            
            # 尝试提取JSON数据
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_content = script.string
                    json_matches = re.findall(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_content, re.DOTALL)
                    for match in json_matches:
                        try:
                            json_data = json.loads(match)
                            if 'sheets' in json_data or 'data' in json_data:
                                print("找到JSON数据")
                                return json_data
                        except json.JSONDecodeError:
                            continue
            
            # 解析HTML表格
            return self.parse_html_tables(soup)
            
        except Exception as e:
            print(f"从页面提取数据失败: {e}")
        
        return data
    
    def parse_html_tables(self, soup: BeautifulSoup) -> Dict:
        """解析HTML表格"""
        data = {"sheets": []}
        
        try:
            tables = soup.find_all('table')
            
            for i, table in enumerate(tables):
                sheet_data = {
                    "name": f"表格_{i+1}",
                    "data": []
                }
                
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        sheet_data["data"].append(row_data)
                
                if sheet_data["data"]:
                    data["sheets"].append(sheet_data)
                    print(f"解析表格 {i+1}: {len(sheet_data['data'])} 行数据")
            
        except Exception as e:
            print(f"解析HTML表格失败: {e}")
        
        return data
    
    def extract_pricing_data(self, doc_data: Dict) -> List[Dict]:
        """提取报价数据"""
        pricing_data = []
        
        try:
            sheets = doc_data.get('sheets', [])
            print(f"开始处理 {len(sheets)} 个工作表")
            
            for sheet in sheets:
                sheet_name = sheet.get('name', '')
                print(f"处理工作表: {sheet_name}")
                
                if any(keyword in sheet_name for keyword in ['三大件', 'CPU', '内存', '存储', '硬盘']):
                    print(f"找到相关工作表: {sheet_name}")
                    items = self.parse_sheet_data(sheet)
                    pricing_data.extend(items)
                else:
                    items = self.parse_sheet_data(sheet)
                    if items:
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
            for i, row in enumerate(table_data[1:], 1):
                if len(row) >= 2:
                    item = self.parse_row_data(row, headers)
                    if item:
                        items.append(item)
            
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
            df = pd.DataFrame(data)
            columns = ['品牌', '型号', '价格']
            df = df.reindex(columns=columns)
            df.to_excel(filepath, index=False, engine='openpyxl')
            print(f"数据已保存到: {filepath}")
            print(f"共保存 {len(data)} 条记录")
            
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
        print("开始高级解析腾讯文档...")
        print(f"文档地址: {self.doc_url}")
        
        if not self.setup_driver():
            print("无法设置浏览器驱动，程序退出")
            return
        
        try:
            page_source = self.get_page_content()
            
            if not page_source:
                print("无法获取页面内容")
                return
            
            doc_data = self.extract_data_from_page(page_source)
            
            if not doc_data or not doc_data.get('sheets'):
                print("无法提取文档数据")
                return
            
            pricing_data = self.extract_pricing_data(doc_data)
            
            if not pricing_data:
                print("未找到报价数据")
                return
            
            self.save_to_excel(pricing_data)
            
        finally:
            if self.driver:
                self.driver.quit()
                print("浏览器已关闭")

def main():
    """主函数"""
    doc_url = "https://docs.qq.com/sheet/DUlFDb1NETFBaQU9p"
    
    parser = AdvancedTencentDocParser(doc_url)
    parser.run()

if __name__ == "__main__":
    main() 