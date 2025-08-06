#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件扫描器性能测试脚本
"""

import sys
import os
import time
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QWidget
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from files_cleaner import FileScanner

class PerformanceTest(QMainWindow):
    """性能测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.test_results = []
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("文件扫描器性能测试")
        self.setGeometry(200, 200, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("多线程扫描性能测试")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 说明
        info = QLabel("点击开始测试按钮，将测试不同线程数的扫描性能")
        info.setStyleSheet("margin: 10px; color: #666;")
        layout.addWidget(info)
        
        # 测试按钮
        self.test_button = QPushButton("开始性能测试")
        self.test_button.setMinimumHeight(40)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.test_button.clicked.connect(self.start_performance_test)
        layout.addWidget(self.test_button)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.result_text)
        
    def start_performance_test(self):
        """开始性能测试"""
        self.test_button.setEnabled(False)
        self.result_text.clear()
        self.result_text.append("开始性能测试...\n")
        
        # 创建测试线程
        self.test_thread = PerformanceTestThread()
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.progress_updated.connect(self.on_progress_updated)
        self.test_thread.start()
    
    def on_progress_updated(self, message):
        """更新进度"""
        self.result_text.append(message)
        self.result_text.ensureCursorVisible()
    
    def on_test_completed(self, results):
        """测试完成"""
        self.test_button.setEnabled(True)
        self.result_text.append("\n=== 测试结果 ===\n")
        
        for thread_count, time_taken, files_scanned in results:
            speed = files_scanned / time_taken if time_taken > 0 else 0
            self.result_text.append(f"线程数: {thread_count:2d} | 时间: {time_taken:6.2f}秒 | 文件数: {files_scanned:6d} | 速度: {speed:6.1f} 文件/秒")
        
        # 找出最佳配置
        if results:
            best_result = min(results, key=lambda x: x[1])  # 时间最短的
            self.result_text.append(f"\n推荐配置: {best_result[0]} 个线程 (耗时 {best_result[1]:.2f} 秒)")

class PerformanceTestThread(QThread):
    """性能测试线程"""
    test_completed = pyqtSignal(list)
    progress_updated = pyqtSignal(str)
    
    def run(self):
        """运行测试"""
        results = []
        test_threads = [2, 4, 8, 16]
        
        for thread_count in test_threads:
            self.progress_updated.emit(f"测试 {thread_count} 个线程...")
            
            # 创建扫描器
            scanner = FileScanner()
            scanner.thread_count = thread_count
            
            # 记录开始时间
            start_time = time.time()
            files_scanned = 0
            
            # 连接信号
            def on_file_found(file_info):
                nonlocal files_scanned
                files_scanned += 1
                if files_scanned % 1000 == 0:
                    self.progress_updated.emit(f"  已扫描 {files_scanned} 个文件...")
            
            scanner.file_found.connect(on_file_found)
            
            # 开始扫描
            scanner.start()
            scanner.wait()
            
            # 计算时间
            end_time = time.time()
            time_taken = end_time - start_time
            
            results.append((thread_count, time_taken, files_scanned))
            self.progress_updated.emit(f"  完成: {files_scanned} 个文件，耗时 {time_taken:.2f} 秒\n")
        
        self.test_completed.emit(results)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = PerformanceTest()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 