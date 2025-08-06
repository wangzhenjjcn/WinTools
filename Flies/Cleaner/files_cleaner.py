import sys
import os
import shutil
import winreg
import subprocess
import ctypes
import threading
import time
from pathlib import Path
from typing import Dict, List, Tuple
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTreeWidget, QTreeWidgetItem, QLabel, 
                             QProgressBar, QMenu, QMessageBox, QWidget, QSplitter,
                             QLineEdit, QComboBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QMutex, QWaitCondition
from PyQt6.QtGui import QIcon, QFont, QColor, QAction

def is_admin():
    """检测是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员权限重新运行程序"""
    try:
        if not is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        pass

class FileScanner(QThread):
    """文件扫描线程"""
    progress_updated = pyqtSignal(int)
    file_found = pyqtSignal(dict)
    scan_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.startup_files = self._get_startup_files()
        self.scan_threads = []
        self.thread_count = 4  # 默认4个线程
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        self.scanned_files = 0
        self.total_files = 0
        
    def _get_startup_files(self) -> set:
        """获取开机启动文件列表"""
        startup_files = set()
        
        # 注册表启动项
        startup_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunServices",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunServicesOnce"
        ]
        
        for key_path in startup_keys:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if value and os.path.exists(value):
                            startup_files.add(value.lower())
                        i += 1
                    except WindowsError:
                        break
                winreg.CloseKey(key)
            except:
                pass
                
        # 启动文件夹
        startup_folders = [
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'),
            os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
        ]
        
        for folder in startup_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        startup_files.add(file_path.lower())
        
        return startup_files
    
    def _get_file_type(self, file_path: str) -> str:
        """判断文件类型"""
        if os.path.isdir(file_path):
            return "文件夹"
        
        ext = os.path.splitext(file_path)[1].lower()
        
        # 可执行文件
        if ext in ['.exe', '.com', '.bat', '.cmd', '.msi', '.msu']:
            return "可执行文件"
        
        # 文档文件
        elif ext in ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx']:
            return "文档"
        
        # 音频文件
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a']:
            return "音频"
        
        # 视频文件
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
            return "视频"
        
        # 压缩文件
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz']:
            return "压缩文件"
        
        # 图片文件
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
            return "图片"
        
        # 系统文件
        elif ext in ['.sys', '.dll', '.drv', '.vxd', '.inf', '.cat']:
            return "系统文件"
        
        else:
            return "其他"
    
    def _is_system_file(self, file_path: str) -> bool:
        """判断是否为系统文件"""
        system_paths = [
            os.environ.get('WINDIR', 'C:\\Windows'),
            os.environ.get('SYSTEMROOT', 'C:\\Windows'),
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'Windows NT'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 'Windows NT')
        ]
        
        file_path_lower = file_path.lower()
        for system_path in system_paths:
            if system_path.lower() in file_path_lower:
                return True
        return False
    
    def _is_program_file(self, file_path: str) -> bool:
        """判断是否为程序文件"""
        program_paths = [
            os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
            os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        ]
        
        file_path_lower = file_path.lower()
        for program_path in program_paths:
            if program_path.lower() in file_path_lower:
                return True
        return False
    
    def run(self):
        """开始扫描"""
        self.running = True
        self.scanned_files = 0
        
        # 获取所有需要扫描的路径
        all_paths = self._get_all_scan_paths()
        self.total_files = len(all_paths)
        
        if self.total_files == 0:
            self.scan_finished.emit()
            return
        
        # 使用单线程扫描，但分批处理以提高响应性
        batch_size = max(100, self.total_files // 100)  # 每批处理100个文件或总文件的1%
        
        for i in range(0, len(all_paths), batch_size):
            if not self.running:
                break
                
            batch = all_paths[i:i + batch_size]
            self._process_batch(batch)
            
            # 更新进度
            self.scanned_files += len(batch)
            progress = int(self.scanned_files * 100 / self.total_files) if self.total_files > 0 else 0
            self.progress_updated.emit(progress)
        
        self.scan_finished.emit()
    
    def _process_batch(self, batch):
        """处理一批文件"""
        for file_path, file_name, is_dir in batch:
            if not self.running:
                break
                
            try:
                if is_dir:
                    file_info = {
                        'path': file_path,
                        'name': file_name,
                        'type': '文件夹',
                        'size': 0,
                        'is_system': self._is_system_file(file_path),
                        'is_program': self._is_program_file(file_path),
                        'is_startup': False
                    }
                else:
                    file_size = os.path.getsize(file_path)
                    file_type = self._get_file_type(file_path)
                    is_startup = file_path.lower() in self.startup_files
                    
                    file_info = {
                        'path': file_path,
                        'name': file_name,
                        'type': file_type,
                        'size': file_size,
                        'is_system': self._is_system_file(file_path),
                        'is_program': self._is_program_file(file_path),
                        'is_startup': is_startup
                    }
                
                self.file_found.emit(file_info)
                
            except Exception as e:
                self.error_occurred.emit(f"处理文件 {file_path} 时出错: {str(e)}")
    
    def _get_all_scan_paths(self) -> List[Tuple[str, str, bool]]:
        """获取所有需要扫描的路径"""
        paths = []
        
        for drive in self._get_drives():
            if not self.running:
                break
                
            if os.path.exists(drive):
                try:
                    for root, dirs, files in os.walk(drive):
                        if not self.running:
                            break
                        
                        # 添加文件夹
                        for dir_name in sorted(dirs):
                            if not self.running:
                                break
                            dir_path = os.path.join(root, dir_name)
                            paths.append((dir_path, dir_name, True))  # True表示是文件夹
                        
                        # 添加文件
                        for file_name in sorted(files):
                            if not self.running:
                                break
                            file_path = os.path.join(root, file_name)
                            paths.append((file_path, file_name, False))  # False表示是文件
                except Exception as e:
                    self.error_occurred.emit(f"扫描路径 {drive} 时出错: {str(e)}")
        
        return paths
    
    def _update_progress(self):
        """更新进度"""
        self.mutex.lock()
        self.scanned_files += 1
        progress = int(self.scanned_files * 100 / self.total_files) if self.total_files > 0 else 0
        self.mutex.unlock()
        self.progress_updated.emit(progress)
    
    def _get_drives(self) -> List[str]:
        """获取所有系统盘"""
        drives = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    
    def stop(self):
        """停止扫描"""
        self.running = False

class FileCleaner(QMainWindow):
    """文件清理器主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 检查管理员权限
        self.check_admin_permission()
        
        self.scanner = FileScanner()
        self.init_ui()
        self.connect_signals()
    
    def check_admin_permission(self):
        """检查管理员权限"""
        if not is_admin():
            reply = QMessageBox.question(
                self, 
                "权限提示", 
                "检测到程序未以管理员权限运行，某些系统文件可能无法访问。\n是否以管理员权限重新启动？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                run_as_admin()
            else:
                QMessageBox.information(
                    self,
                    "权限说明",
                    "程序将以普通权限运行，某些系统文件可能无法扫描。"
                )
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("文件扫描器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部控制区域
        control_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("开始扫描")
        self.scan_button.setMinimumHeight(40)
        self.scan_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.stop_button = QPushButton("停止扫描")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        
        self.stats_label = QLabel("文件统计: 0 个文件")
        self.stats_label.setStyleSheet("font-size: 12px; color: #666;")
        
        # 搜索功能
        self.search_label = QLabel("搜索:")
        self.search_label.setStyleSheet("font-size: 12px; color: #666;")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入文件名或路径...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """)
        self.search_input.textChanged.connect(self.filter_files)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "可执行文件", "系统文件", "文档", "音频", "视频", "压缩文件", "图片", "文件夹", "其他"])
        self.filter_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 12px;
            }
        """)
        self.filter_combo.currentTextChanged.connect(self.filter_files)
        
        control_layout.addWidget(self.scan_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.progress_bar)
        control_layout.addWidget(self.status_label)
        control_layout.addWidget(self.stats_label)
        control_layout.addStretch()
        control_layout.addWidget(self.search_label)
        control_layout.addWidget(self.search_input)
        control_layout.addWidget(self.filter_combo)
        
        main_layout.addLayout(control_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 文件树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["文件名", "类型", "大小", "属性"])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #f5f5f5;
                alternate-background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        
        # 启动项列表
        self.startup_tree = QTreeWidget()
        self.startup_tree.setHeaderLabels(["启动项", "路径", "类型"])
        self.startup_tree.setAlternatingRowColors(True)
        self.startup_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #fff3e0;
                alternate-background-color: #fff8e1;
                border: 1px solid #ffcc02;
                border-radius: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ffecb3;
            }
            QTreeWidget::item:selected {
                background-color: #ffeb3b;
                color: #f57c00;
            }
        """)
        
        splitter.addWidget(self.file_tree)
        splitter.addWidget(self.startup_tree)
        splitter.setSizes([800, 400])
        
        main_layout.addWidget(splitter)
        
        # 右键菜单
        self.setup_context_menu()
        
    def connect_signals(self):
        """连接信号"""
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button.clicked.connect(self.stop_scan)
        self.scanner.progress_updated.connect(self.update_progress)
        self.scanner.file_found.connect(self.add_file_item)
        self.scanner.scan_finished.connect(self.scan_finished)
        self.scanner.error_occurred.connect(self.handle_error)
        
    def setup_context_menu(self):
        """设置右键菜单"""
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.file_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        # 打开文件位置
        open_location_action = QAction("打开文件位置", self)
        open_location_action.triggered.connect(lambda: self.open_file_location(item))
        menu.addAction(open_location_action)
        
        # 打开文件
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            if file_info['type'] != '文件夹':
                open_file_action = QAction("打开文件", self)
                open_file_action.triggered.connect(lambda: self.open_file(item))
                menu.addAction(open_file_action)
        
        menu.addSeparator()
        
        # 复制路径
        copy_path_action = QAction("复制路径", self)
        copy_path_action.triggered.connect(lambda: self.copy_path(item))
        menu.addAction(copy_path_action)
        
        # 复制文件
        copy_file_action = QAction("复制文件", self)
        copy_file_action.triggered.connect(lambda: self.copy_file(item))
        menu.addAction(copy_file_action)
        
        # 剪切文件
        cut_file_action = QAction("剪切文件", self)
        cut_file_action.triggered.connect(lambda: self.cut_file(item))
        menu.addAction(cut_file_action)
        
        menu.addSeparator()
        
        # 删除文件
        delete_action = QAction("删除文件", self)
        delete_action.triggered.connect(lambda: self.delete_file(item))
        menu.addAction(delete_action)
        
        menu.exec(self.file_tree.mapToGlobal(position))
        
    def start_scan(self):
        """开始扫描"""
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在扫描...")
        
        # 清空列表
        self.file_tree.clear()
        self.startup_tree.clear()
        self.all_items = []
        
        # 开始扫描
        self.scanner.start()
    
    def handle_error(self, error_msg):
        """处理错误"""
        QMessageBox.warning(self, "扫描错误", error_msg)
        
    def stop_scan(self):
        """停止扫描"""
        self.scanner.stop()
        self.scan_finished()
        
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
    def add_file_item(self, file_info):
        """添加文件项到列表"""
        # 创建主文件项
        item = QTreeWidgetItem()
        item.setText(0, file_info['name'])
        item.setText(1, file_info['type'])
        
        # 格式化文件大小
        if file_info['size'] > 0:
            size_str = self.format_size(file_info['size'])
        else:
            size_str = "-"
        item.setText(2, size_str)
        
        # 设置文件属性
        attributes = []
        if file_info['is_system']:
            attributes.append("系统")
        if file_info['is_program']:
            attributes.append("程序")
        if not file_info['is_system'] and not file_info['is_program']:
            attributes.append("用户")
        item.setText(3, ", ".join(attributes))
        
        # 设置颜色
        self.set_item_color(item, file_info)
        
        # 存储文件信息
        item.setData(0, Qt.ItemDataRole.UserRole, file_info)
        
        # 添加到文件树
        self.file_tree.addTopLevelItem(item)
        
        # 存储所有项目用于搜索
        if not hasattr(self, 'all_items'):
            self.all_items = []
        self.all_items.append(item)
        
        # 更新统计信息
        self.update_stats()
        
        # 实时更新界面
        QApplication.processEvents()
    
    def update_stats(self):
        """更新统计信息"""
        if hasattr(self, 'all_items'):
            self.stats_label.setText(f"文件统计: {len(self.all_items)} 个文件")
        
        # 如果是启动项，添加到启动项列表
        if file_info['is_startup']:
            startup_item = QTreeWidgetItem()
            startup_item.setText(0, file_info['name'])
            startup_item.setText(1, file_info['path'])
            startup_item.setText(2, file_info['type'])
            startup_item.setData(0, Qt.ItemDataRole.UserRole, file_info)
            
            # 设置启动项颜色
            startup_item.setBackground(0, QColor(255, 235, 59))  # 黄色背景
            startup_item.setBackground(1, QColor(255, 235, 59))
            startup_item.setBackground(2, QColor(255, 235, 59))
            
            self.startup_tree.addTopLevelItem(startup_item)
        
    def set_item_color(self, item, file_info):
        """设置项目颜色"""
        color_map = {
            "可执行文件": QColor(255, 87, 34),  # 橙色
            "系统文件": QColor(156, 39, 176),   # 紫色
            "文档": QColor(33, 150, 243),       # 蓝色
            "音频": QColor(76, 175, 80),        # 绿色
            "视频": QColor(233, 30, 99),        # 粉色
            "压缩文件": QColor(255, 193, 7),    # 黄色
            "图片": QColor(103, 58, 183),       # 深紫色
            "文件夹": QColor(96, 125, 139),     # 灰色
            "其他": QColor(158, 158, 158)       # 浅灰色
        }
        
        file_type = file_info['type']
        if file_type in color_map:
            color = color_map[file_type]
            item.setBackground(0, color)
            item.setBackground(1, color)
            item.setBackground(2, color)
            item.setBackground(3, color)
            
            # 设置文字颜色为白色（深色背景）
            if file_type in ["可执行文件", "系统文件", "视频", "压缩文件"]:
                item.setForeground(0, QColor(255, 255, 255))
                item.setForeground(1, QColor(255, 255, 255))
                item.setForeground(2, QColor(255, 255, 255))
                item.setForeground(3, QColor(255, 255, 255))
        
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def filter_files(self):
        """过滤文件"""
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        
        # 清空当前显示
        self.file_tree.clear()
        
        # 重新添加符合条件的项目
        visible_count = 0
        for item in self.all_items:
            if not hasattr(item, 'data') or not item.data(0, Qt.ItemDataRole.UserRole):
                continue
                
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_name = file_info['name'].lower()
            file_path = file_info['path'].lower()
            file_type = file_info['type']
            
            # 搜索过滤
            if search_text and search_text not in file_name and search_text not in file_path:
                continue
            
            # 类型过滤
            if filter_type != "全部" and file_type != filter_type:
                continue
            
            # 添加符合条件的项目
            self.file_tree.addTopLevelItem(item)
            visible_count += 1
        
        # 更新统计信息
        self.stats_label.setText(f"显示: {visible_count} 个文件 (总计: {len(self.all_items)} 个)")
        
    def scan_finished(self):
        """扫描完成"""
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("扫描完成")
        
    def open_file_location(self, item):
        """打开文件位置"""
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_path = file_info['path']
            folder_path = os.path.dirname(file_path)
            
            try:
                subprocess.run(['explorer', '/select,', file_path])
            except:
                QMessageBox.warning(self, "错误", f"无法打开文件位置：{file_path}")
                
    def open_file(self, item):
        """打开文件"""
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_path = file_info['path']
            
            try:
                os.startfile(file_path)
            except:
                QMessageBox.warning(self, "错误", f"无法打开文件：{file_path}")
                
    def copy_path(self, item):
        """复制文件路径"""
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_path = file_info['path']
            
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
            
    def copy_file(self, item):
        """复制文件"""
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_path = file_info['path']
            
            try:
                # 将文件路径复制到剪贴板，用户可以在资源管理器中粘贴
                clipboard = QApplication.clipboard()
                clipboard.setText(file_path)
                QMessageBox.information(self, "提示", f"文件路径已复制到剪贴板：{file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"复制文件路径失败：{str(e)}")
            
    def cut_file(self, item):
        """剪切文件"""
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_path = file_info['path']
            
            try:
                # 将文件路径复制到剪贴板，用户可以在资源管理器中粘贴
                clipboard = QApplication.clipboard()
                clipboard.setText(file_path)
                QMessageBox.information(self, "提示", f"文件路径已复制到剪贴板：{file_path}\n您可以在资源管理器中粘贴并剪切文件")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"复制文件路径失败：{str(e)}")
            
    def delete_file(self, item):
        """删除文件"""
        if item.data(0, Qt.ItemDataRole.UserRole):
            file_info = item.data(0, Qt.ItemDataRole.UserRole)
            file_path = file_info['path']
            
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除文件：{file_path}？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    self.file_tree.takeTopLevelItem(self.file_tree.indexOfTopLevelItem(item))
                    QMessageBox.information(self, "成功", "文件删除成功")
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"删除文件失败：{str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用Fusion样式
    
    # 检查管理员权限
    if not is_admin():
        print("警告: 程序未以管理员权限运行，某些系统文件可能无法访问")
    
    window = FileCleaner()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
