import sys
import socket
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QMessageBox,
                             QProgressBar, QSpinBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor
import ipaddress
import re


class ScannerThread(QThread):
    """扫描线程类"""
    progress_updated = pyqtSignal(int)
    result_updated = pyqtSignal(str)
    scan_finished = pyqtSignal()
    
    def __init__(self, start_ip, end_ip, ports, timeout, max_threads):
        super().__init__()
        self.start_ip = start_ip
        self.end_ip = end_ip
        self.ports = ports
        self.timeout = timeout
        self.max_threads = max_threads
        self.is_running = False
        
    def run(self):
        self.is_running = True
        try:
            # 解析IP范围
            start_ip_int = int(ipaddress.IPv4Address(self.start_ip))
            end_ip_int = int(ipaddress.IPv4Address(self.end_ip))
            
            # 解析端口
            port_list = self._parse_ports(self.ports)
            
            total_ips = end_ip_int - start_ip_int + 1
            total_scans = total_ips * len(port_list)
            current_scan = 0
            
            # 创建线程池
            threads = []
            results = []
            
            for ip_int in range(start_ip_int, end_ip_int + 1):
                if not self.is_running:
                    break
                    
                ip = str(ipaddress.IPv4Address(ip_int))
                
                for port in port_list:
                    if not self.is_running:
                        break
                        
                    # 限制并发线程数
                    while len([t for t in threads if t.is_alive()]) >= self.max_threads:
                        time.sleep(0.01)
                        if not self.is_running:
                            break
                    
                    if not self.is_running:
                        break
                    
                    # 创建扫描线程
                    scan_thread = threading.Thread(
                        target=self._scan_port,
                        args=(ip, port, results, self.result_updated)
                    )
                    scan_thread.daemon = True
                    scan_thread.start()
                    threads.append(scan_thread)
                    
                    current_scan += 1
                    progress = int((current_scan / total_scans) * 100)
                    self.progress_updated.emit(progress)
            
            # 等待所有线程完成
            for thread in threads:
                if self.is_running:
                    thread.join()
            
            # 输出结果
            if not results:
                self.result_updated.emit("扫描完成！未发现开放端口。")
                
        except Exception as e:
            self.result_updated.emit(f"扫描出错: {str(e)}\n")
        
        self.scan_finished.emit()
    
    def stop(self):
        self.is_running = False
    
    def _parse_ports(self, ports_str):
        """解析端口字符串"""
        port_list = []
        parts = ports_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 端口范围
                try:
                    start_port, end_port = part.split('-')
                    start_port = int(start_port.strip())
                    end_port = int(end_port.strip())
                    
                    if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                        port_list.extend(range(start_port, end_port + 1))
                except ValueError:
                    continue
            else:
                # 单个端口
                try:
                    port = int(part)
                    if 1 <= port <= 65535:
                        port_list.append(port)
                except ValueError:
                    continue
        
        return list(set(port_list))  # 去重
    
    def _scan_port(self, ip, port, results, result_signal):
        """扫描单个端口"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout / 1000.0)  # 转换为秒
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                results.append((ip, port))
                # 实时发送结果
                result_signal.emit(f"{ip}:{port}")
                
        except Exception:
            pass


class IPScannerGUI(QMainWindow):
    """IP扫描器GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.scanner_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("局域网IP端口扫描器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 信息设置区
        self.create_settings_group(main_layout)
        
        # 扫描结果区
        self.create_results_group(main_layout)
        
        # 按钮区
        self.create_buttons(main_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
    def create_settings_group(self, parent_layout):
        """创建信息设置区"""
        settings_group = QGroupBox("信息设置")
        settings_layout = QGridLayout()
        
        # 起始IP
        settings_layout.addWidget(QLabel("起始IP:"), 0, 0)
        self.start_ip_edit = QLineEdit("192.168.1.1")
        self.start_ip_edit.setPlaceholderText("例如: 192.168.1.1")
        settings_layout.addWidget(self.start_ip_edit, 0, 1)
        
        # 结束IP
        settings_layout.addWidget(QLabel("结束IP:"), 0, 2)
        self.end_ip_edit = QLineEdit("192.168.1.255")
        self.end_ip_edit.setPlaceholderText("例如: 192.168.1.255")
        settings_layout.addWidget(self.end_ip_edit, 0, 3)
        
        # 端口号
        settings_layout.addWidget(QLabel("端口号:"), 1, 0)
        self.ports_edit = QLineEdit("80,139,440-445")
        self.ports_edit.setPlaceholderText("例如: 80,139,440-445")
        settings_layout.addWidget(self.ports_edit, 1, 1, 1, 3)
        
        # 超时
        settings_layout.addWidget(QLabel("超时(毫秒):"), 2, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 9999)
        self.timeout_spin.setValue(1000)
        self.timeout_spin.setSuffix(" ms")
        settings_layout.addWidget(self.timeout_spin, 2, 1)
        
        # 线程数
        settings_layout.addWidget(QLabel("线程数:"), 2, 2)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 9999)
        self.threads_spin.setValue(10)
        settings_layout.addWidget(self.threads_spin, 2, 3)
        
        settings_group.setLayout(settings_layout)
        parent_layout.addWidget(settings_group)
        
    def create_results_group(self, parent_layout):
        """创建扫描结果区"""
        results_group = QGroupBox("扫描结果")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        
        # 设置文档边距
        document = self.results_text.document()
        document.setDocumentMargin(2)
        
        # 设置样式表减少行距
        self.results_text.setStyleSheet("""
            QTextEdit {
                padding: 2px;
            }
        """)
        
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        parent_layout.addWidget(results_group)
        
    def create_buttons(self, parent_layout):
        """创建按钮区"""
        button_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("开始扫描")
        self.scan_button.clicked.connect(self.start_scan)
        button_layout.addWidget(self.scan_button)
        
        self.stop_button = QPushButton("停止扫描")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        
        self.exit_button = QPushButton("退出程序")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)
        
        parent_layout.addLayout(button_layout)
        
    def validate_inputs(self):
        """验证输入数据"""
        errors = []
        
        # 验证IP地址
        try:
            start_ip = self.start_ip_edit.text().strip()
            end_ip = self.end_ip_edit.text().strip()
            
            ipaddress.IPv4Address(start_ip)
            ipaddress.IPv4Address(end_ip)
            
            # 检查IP范围
            start_ip_int = int(ipaddress.IPv4Address(start_ip))
            end_ip_int = int(ipaddress.IPv4Address(end_ip))
            
            if start_ip_int > end_ip_int:
                errors.append("起始IP不能大于结束IP")
                
        except ipaddress.AddressValueError:
            errors.append("IP地址格式不正确")
        
        # 验证端口
        ports_str = self.ports_edit.text().strip()
        if not ports_str:
            errors.append("端口号不能为空")
        else:
            try:
                port_list = self._parse_ports(ports_str)
                if not port_list:
                    errors.append("端口号格式不正确")
            except:
                errors.append("端口号格式不正确")
        
        # 验证超时
        timeout = self.timeout_spin.value()
        if timeout < 100 or timeout > 9999:
            errors.append("超时时间必须在100-9999毫秒之间")
        
        # 验证线程数
        threads = self.threads_spin.value()
        if threads < 1 or threads > 9999:
            errors.append("线程数必须在1-9999之间")
        
        return errors
    
    def _parse_ports(self, ports_str):
        """解析端口字符串（用于验证）"""
        port_list = []
        parts = ports_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 端口范围
                start_port, end_port = part.split('-')
                start_port = int(start_port.strip())
                end_port = int(end_port.strip())
                
                if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                    port_list.extend(range(start_port, end_port + 1))
            else:
                # 单个端口
                port = int(part)
                if 1 <= port <= 65535:
                    port_list.append(port)
        
        return list(set(port_list))
    
    def start_scan(self):
        """开始扫描"""
        # 验证输入
        errors = self.validate_inputs()
        if errors:
            QMessageBox.warning(self, "输入错误", "\n".join(errors))
            return
        
        # 清空结果
        self.results_text.clear()
        
        # 创建扫描线程
        self.scanner_thread = ScannerThread(
            self.start_ip_edit.text().strip(),
            self.end_ip_edit.text().strip(),
            self.ports_edit.text().strip(),
            self.timeout_spin.value(),
            self.threads_spin.value()
        )
        
        # 连接信号
        self.scanner_thread.progress_updated.connect(self.update_progress)
        self.scanner_thread.result_updated.connect(self.update_results)
        self.scanner_thread.scan_finished.connect(self.scan_finished)
        
        # 更新UI状态
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 开始扫描
        self.scanner_thread.start()
    
    def stop_scan(self):
        """停止扫描"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()
            # 扫描已停止，不添加提示
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_results(self, text):
        """更新扫描结果"""
        # 添加换行符确保结果间没有空行
        self.results_text.append(text)
        # 滚动到底部
        cursor = self.results_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)
    
    def scan_finished(self):
        """扫描完成"""
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        # 扫描完成，不添加额外提示


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("IP端口扫描器")
    
    window = IPScannerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 