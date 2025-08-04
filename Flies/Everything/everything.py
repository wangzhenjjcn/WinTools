import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
from datetime import datetime
import mimetypes
import zipfile
import tarfile
import gzip
import bz2
import lzma
from pathlib import Path
import json
import sqlite3
import hashlib
import pickle
import shutil
from typing import Dict, List, Any, Optional
try:
    import win32api
    import win32con
    import win32file
    import win32security
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False

class FileProperties:
    """文件属性管理器"""
    
    def __init__(self):
        self.properties = {}
        
    def get_file_properties(self, file_path: str) -> Dict[str, Any]:
        """获取文件属性"""
        try:
            stat = os.stat(file_path)
            properties = {
                'size': stat.st_size,
                'size_on_disk': self.get_size_on_disk(file_path),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'accessed': datetime.fromtimestamp(stat.st_atime),
                'filename_length': len(os.path.basename(file_path)),
                'path_length': len(file_path),
                'extension': os.path.splitext(file_path)[1].lower(),
                'is_hidden': self.is_hidden(file_path),
                'is_readonly': self.is_readonly(file_path),
                'is_system': self.is_system(file_path),
                'attributes': self.get_file_attributes(file_path),
                'hash': self.calculate_file_hash(file_path),
                'type': self.get_file_type(file_path)
            }
            
            # 获取特定文件类型的属性
            properties.update(self.get_specific_properties(file_path))
            
            return properties
        except Exception as e:
            return {'error': str(e)}
    
    def get_size_on_disk(self, file_path: str) -> int:
        """获取文件在磁盘上的实际大小"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0
    
    def is_hidden(self, file_path: str) -> bool:
        """检查文件是否隐藏"""
        try:
            return bool(os.stat(file_path).st_file_attributes & win32con.FILE_ATTRIBUTE_HIDDEN)
        except:
            return False
    
    def is_readonly(self, file_path: str) -> bool:
        """检查文件是否只读"""
        try:
            return bool(os.stat(file_path).st_file_attributes & win32con.FILE_ATTRIBUTE_READONLY)
        except:
            return False
    
    def is_system(self, file_path: str) -> bool:
        """检查文件是否系统文件"""
        try:
            return bool(os.stat(file_path).st_file_attributes & win32con.FILE_ATTRIBUTE_SYSTEM)
        except:
            return False
    
    def get_file_attributes(self, file_path: str) -> str:
        """获取文件属性字符串"""
        try:
            attrs = os.stat(file_path).st_file_attributes
            attr_list = []
            if attrs & win32con.FILE_ATTRIBUTE_READONLY:
                attr_list.append("R")
            if attrs & win32con.FILE_ATTRIBUTE_HIDDEN:
                attr_list.append("H")
            if attrs & win32con.FILE_ATTRIBUTE_SYSTEM:
                attr_list.append("S")
            if attrs & win32con.FILE_ATTRIBUTE_ARCHIVE:
                attr_list.append("A")
            return "".join(attr_list)
        except:
            return ""
    
    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值（仅用于小文件）"""
        try:
            if os.path.getsize(file_path) > 1024 * 1024:  # 大于1MB的文件不计算哈希
                return ""
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def get_specific_properties(self, file_path: str) -> Dict[str, Any]:
        """获取特定文件类型的属性"""
        ext = os.path.splitext(file_path)[1].lower()
        properties = {}
        
        # 图片文件属性
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            properties.update(self.get_image_properties(file_path))
        
        # 音频文件属性
        elif ext in ['.mp3', '.wav', '.flac', '.aac']:
            properties.update(self.get_audio_properties(file_path))
        
        # 视频文件属性
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
            properties.update(self.get_video_properties(file_path))
        
        # 文档文件属性
        elif ext in ['.txt', '.doc', '.docx', '.pdf']:
            properties.update(self.get_document_properties(file_path))
        
        return properties
    
    def get_image_properties(self, file_path: str) -> Dict[str, Any]:
        """获取图片文件属性"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return {
                    'dimensions': f"{img.width}x{img.height}",
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'color_depth': img.bits if hasattr(img, 'bits') else None
                }
        except:
            return {}
    
    def get_audio_properties(self, file_path: str) -> Dict[str, Any]:
        """获取音频文件属性"""
        try:
            import mutagen
            audio = mutagen.File(file_path)
            if audio:
                return {
                    'duration': audio.info.length if hasattr(audio.info, 'length') else None,
                    'bitrate': audio.info.bitrate if hasattr(audio.info, 'bitrate') else None,
                    'sample_rate': audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else None,
                    'channels': audio.info.channels if hasattr(audio.info, 'channels') else None
                }
        except:
            pass
        return {}
    
    def get_video_properties(self, file_path: str) -> Dict[str, Any]:
        """获取视频文件属性"""
        try:
            import cv2
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                return {
                    'frame_rate': fps,
                    'frame_count': frame_count,
                    'dimensions': f"{width}x{height}",
                    'width': width,
                    'height': height,
                    'duration': frame_count / fps if fps > 0 else None
                }
        except:
            pass
        return {}
    
    def get_document_properties(self, file_path: str) -> Dict[str, Any]:
        """获取文档文件属性"""
        properties = {}
        try:
            # 尝试读取文本文件的行数
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    properties['line_count'] = len(lines)
                    properties['word_count'] = sum(len(line.split()) for line in lines)
                    properties['char_count'] = sum(len(line) for line in lines)
        except:
            pass
        return properties

class LightweightDatabase:
    """轻量级数据库管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "files.db"
        self.index_path = self.data_dir / "file_index.pkl"
        self.properties_path = self.data_dir / "properties.pkl"
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建文件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                size INTEGER,
                type TEXT,
                created TEXT,
                modified TEXT,
                accessed TEXT,
                attributes TEXT,
                hash TEXT,
                indexed_at TEXT
            )
        ''')
        
        # 创建属性表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                file_id INTEGER,
                property_name TEXT,
                property_value TEXT,
                FOREIGN KEY (file_id) REFERENCES files (id),
                PRIMARY KEY (file_id, property_name)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_path ON files (path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_name ON files (name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_type ON files (type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_properties_name ON properties (property_name)')
        
        conn.commit()
        conn.close()
    
    def add_file(self, file_info: Dict[str, Any]):
        """添加文件到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 插入文件记录
            cursor.execute('''
                INSERT OR REPLACE INTO files 
                (name, path, size, type, created, modified, accessed, attributes, hash, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_info['name'],
                file_info['path'],
                file_info['size'],
                file_info['type'],
                file_info['created'].isoformat(),
                file_info['modified'].isoformat(),
                file_info['accessed'].isoformat(),
                file_info.get('attributes', ''),
                file_info.get('hash', ''),
                datetime.now().isoformat()
            ))
            
            file_id = cursor.lastrowid
            
            # 插入属性
            for prop_name, prop_value in file_info.get('properties', {}).items():
                if prop_value is not None:
                    cursor.execute('''
                        INSERT OR REPLACE INTO properties (file_id, property_name, property_value)
                        VALUES (?, ?, ?)
                    ''', (file_id, prop_name, str(prop_value)))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"数据库错误: {e}")
            return False
        finally:
            conn.close()
    
    def search_files(self, query: str = "", file_type: str = "", size_filter: str = "") -> List[Dict[str, Any]]:
        """搜索文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = '''
            SELECT f.*, GROUP_CONCAT(p.property_name || ':' || p.property_value) as properties
            FROM files f
            LEFT JOIN properties p ON f.id = p.file_id
        '''
        
        conditions = []
        params = []
        
        if query:
            conditions.append("(f.name LIKE ? OR f.path LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        
        if file_type and file_type != "全部":
            conditions.append("f.type = ?")
            params.append(file_type)
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " GROUP BY f.id ORDER BY f.name"
        
        cursor.execute(sql, params)
        results = []
        
        for row in cursor.fetchall():
            file_info = {
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'size': row[3],
                'type': row[4],
                'created': datetime.fromisoformat(row[5]),
                'modified': datetime.fromisoformat(row[6]),
                'accessed': datetime.fromisoformat(row[7]),
                'attributes': row[8],
                'hash': row[9],
                'indexed_at': datetime.fromisoformat(row[10])
            }
            
            # 解析属性
            if row[11]:
                properties = {}
                for prop in row[11].split(','):
                    if ':' in prop:
                        name, value = prop.split(':', 1)
                        properties[name] = value
                file_info['properties'] = properties
            
            results.append(file_info)
        
        conn.close()
        return results
    
    def get_file_count(self) -> int:
        """获取文件总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear_database(self):
        """清空数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files")
        cursor.execute("DELETE FROM properties")
        conn.commit()
        conn.close()

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件搜索工具 - Everything (增强版)")
        self.root.geometry("1400x900")
        
        # 数据目录
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.properties_manager = FileProperties()
        self.database = LightweightDatabase(self.data_dir)
        
        # 文件索引数据
        self.files_data = []
        self.filtered_data = []
        self.is_indexing = False
        self.index_thread = None
        
        # 筛选器配置
        self.filters = {
            "音频": ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.aiff'],
            "压缩文件": ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.lzma'],
            "文档": ['.txt', '.doc', '.docx', '.pdf', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'],
            "可执行文件": ['.exe', '.msi', '.bat', '.cmd', '.com', '.scr'],
            "图片": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico'],
            "视频": ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']
        }
        
        self.setup_ui()
        self.load_settings()
        
        # 加载现有索引
        self.load_existing_index()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 菜单栏
        self.create_menu()
        
        # 工具栏
        self.create_toolbar(main_frame)
        
        # 搜索区域
        self.create_search_area(main_frame)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 文件列表
        self.create_file_list(content_frame)
        
        # 属性面板
        self.create_properties_panel(content_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="选择索引目录", command=self.select_index_directory)
        file_menu.add_command(label="重新索引", command=self.reindex_files)
        file_menu.add_separator()
        file_menu.add_command(label="导出结果", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="数据库管理", command=self.show_database_manager)
        tools_menu.add_command(label="属性查看器", command=self.show_properties_viewer)
        tools_menu.add_separator()
        tools_menu.add_command(label="设置", command=self.show_settings)
        tools_menu.add_command(label="关于", command=self.show_about)
        
    def create_toolbar(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # 索引按钮
        self.index_btn = ttk.Button(toolbar, text="开始索引", command=self.start_indexing)
        self.index_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 停止索引按钮
        self.stop_btn = ttk.Button(toolbar, text="停止索引", command=self.stop_indexing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 数据库信息
        self.db_info_label = ttk.Label(toolbar, text="数据库: 0 个文件")
        self.db_info_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # 进度条
        self.progress = ttk.Progressbar(toolbar, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
    def create_search_area(self, parent):
        search_frame = ttk.LabelFrame(parent, text="搜索")
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 搜索输入框
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(search_input_frame, text="关键词:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        self.search_entry = ttk.Entry(search_input_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        
        # 筛选器
        filter_frame = ttk.Frame(search_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(filter_frame, text="文件类型:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                   values=["全部"] + list(self.filters.keys()) + ["其他"],
                                   state="readonly", width=15)
        filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        filter_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # 大小筛选
        ttk.Label(filter_frame, text="大小:").pack(side=tk.LEFT, padx=(20, 0))
        self.size_var = tk.StringVar(value="全部")
        size_combo = ttk.Combobox(filter_frame, textvariable=self.size_var,
                                 values=["全部", "小于1MB", "1MB-10MB", "10MB-100MB", "大于100MB"],
                                 state="readonly", width=12)
        size_combo.pack(side=tk.LEFT, padx=(5, 0))
        size_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
    def create_file_list(self, parent):
        # 创建左侧文件列表框架
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ('name', 'path', 'size', 'type', 'modified', 'created')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)
        
        # 定义列标题
        self.tree.heading('name', text='文件名', command=lambda: self.sort_treeview('name'))
        self.tree.heading('path', text='路径', command=lambda: self.sort_treeview('path'))
        self.tree.heading('size', text='大小', command=lambda: self.sort_treeview('size'))
        self.tree.heading('type', text='类型', command=lambda: self.sort_treeview('type'))
        self.tree.heading('modified', text='修改时间', command=lambda: self.sort_treeview('modified'))
        self.tree.heading('created', text='创建时间', command=lambda: self.sort_treeview('created'))
        
        # 设置列宽
        self.tree.column('name', width=200)
        self.tree.column('path', width=300)
        self.tree.column('size', width=100)
        self.tree.column('type', width=100)
        self.tree.column('modified', width=150)
        self.tree.column('created', width=150)
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定双击事件
        self.tree.bind('<Double-1>', self.on_file_double_click)
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
    def create_properties_panel(self, parent):
        # 创建右侧属性面板
        props_frame = ttk.LabelFrame(parent, text="文件属性")
        props_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        # 属性显示区域
        self.props_text = scrolledtext.ScrolledText(props_frame, width=40, height=20)
        self.props_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_status_bar(self, parent):
        self.status_bar = ttk.Label(parent, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
    def load_existing_index(self):
        """加载现有索引"""
        count = self.database.get_file_count()
        self.update_db_info(count)
        self.update_status(f"已加载 {count} 个文件的索引")
        
    def update_db_info(self, count: int):
        """更新数据库信息显示"""
        self.db_info_label.config(text=f"数据库: {count} 个文件")
        
    def select_index_directory(self):
        directory = filedialog.askdirectory(title="选择要索引的目录")
        if directory:
            self.index_directory = directory
            self.save_settings()
            self.update_status(f"已选择索引目录: {directory}")
            
    def start_indexing(self):
        if not hasattr(self, 'index_directory'):
            messagebox.showwarning("警告", "请先选择索引目录")
            return
            
        if self.is_indexing:
            return
            
        self.is_indexing = True
        self.index_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start()
        
        self.index_thread = threading.Thread(target=self.index_files)
        self.index_thread.daemon = True
        self.index_thread.start()
        
    def stop_indexing(self):
        self.is_indexing = False
        self.index_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress.stop()
        self.update_status("索引已停止")
        
    def index_files(self):
        total_files = 0
        indexed_files = 0
        
        try:
            for root, dirs, files in os.walk(self.index_directory):
                if not self.is_indexing:
                    break
                    
                for file in files:
                    if not self.is_indexing:
                        break
                        
                    try:
                        file_path = os.path.join(root, file)
                        
                        # 获取文件信息
                        file_info = {
                            'name': file,
                            'path': file_path,
                            'type': self.get_file_type(file_path)
                        }
                        
                        # 获取详细属性
                        properties = self.properties_manager.get_file_properties(file_path)
                        file_info.update(properties)
                        
                        # 添加到数据库
                        if self.database.add_file(file_info):
                            indexed_files += 1
                        
                        total_files += 1
                        
                        if total_files % 100 == 0:
                            self.update_status(f"已处理 {total_files} 个文件，索引 {indexed_files} 个...")
                            
                    except (PermissionError, OSError) as e:
                        continue
                        
            if self.is_indexing:
                self.update_status(f"索引完成，共处理 {total_files} 个文件，成功索引 {indexed_files} 个")
                self.update_db_info(self.database.get_file_count())
                self.apply_filters()
                
        except Exception as e:
            self.update_status(f"索引出错: {str(e)}")
            
        finally:
            self.is_indexing = False
            self.root.after(0, self.stop_indexing)
            
    def get_file_type(self, file_path):
        """获取文件类型分类"""
        ext = os.path.splitext(file_path)[1].lower()
        
        for category, extensions in self.filters.items():
            if ext in extensions:
                return category
                
        return "其他"
        
    def on_search_change(self, *args):
        self.apply_filters()
        
    def on_filter_change(self, *args):
        self.apply_filters()
        
    def apply_filters(self):
        search_term = self.search_var.get()
        filter_type = self.filter_var.get()
        size_filter = self.size_var.get()
        
        # 从数据库搜索
        self.filtered_data = self.database.search_files(search_term, filter_type, size_filter)
        
        self.update_file_list()
        self.update_status(f"找到 {len(self.filtered_data)} 个文件")
        
    def update_file_list(self):
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加过滤后的文件
        for file_info in self.filtered_data:
            size_str = self.format_size(file_info['size'])
            modified_str = file_info['modified'].strftime('%Y-%m-%d %H:%M')
            created_str = file_info['created'].strftime('%Y-%m-%d %H:%M')
            
            self.tree.insert('', 'end', values=(
                file_info['name'],
                file_info['path'],
                size_str,
                file_info['type'],
                modified_str,
                created_str
            ), tags=(file_info['id'],))
            
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            
    def sort_treeview(self, column):
        """排序树形视图"""
        # 获取当前排序方向
        current_sort = getattr(self, 'current_sort', {})
        reverse = current_sort.get(column, False)
        
        # 切换排序方向
        current_sort[column] = not reverse
        self.current_sort = current_sort
        
        # 排序数据
        if column == 'size':
            self.filtered_data.sort(key=lambda x: x['size'], reverse=reverse)
        elif column == 'modified':
            self.filtered_data.sort(key=lambda x: x['modified'], reverse=reverse)
        elif column == 'created':
            self.filtered_data.sort(key=lambda x: x['created'], reverse=reverse)
        else:
            self.filtered_data.sort(key=lambda x: x[column], reverse=reverse)
            
        self.update_file_list()
        
    def on_file_double_click(self, event):
        """双击文件打开"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            file_path = item['values'][1]  # 路径在第二列
            
            try:
                os.startfile(file_path)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
                
    def on_file_select(self, event):
        """文件选择事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            file_id = item['tags'][0] if item['tags'] else None
            
            if file_id:
                # 显示文件属性
                self.show_file_properties(file_id)
                
    def show_file_properties(self, file_id):
        """显示文件属性"""
        # 从数据库获取文件详细信息
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.*, GROUP_CONCAT(p.property_name || ':' || p.property_value) as properties
            FROM files f
            LEFT JOIN properties p ON f.id = p.file_id
            WHERE f.id = ?
            GROUP BY f.id
        ''', (file_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # 清空属性显示
            self.props_text.delete(1.0, tk.END)
            
            # 基本信息
            basic_info = f"""
基本信息:
  文件名: {row[1]}
  路径: {row[2]}
  大小: {self.format_size(row[3])}
  类型: {row[4]}
  创建时间: {row[5]}
  修改时间: {row[6]}
  访问时间: {row[7]}
  属性: {row[8]}
  哈希值: {row[9] if row[9] else '未计算'}

"""
            self.props_text.insert(tk.END, basic_info)
            
            # 详细属性
            if row[11]:
                self.props_text.insert(tk.END, "详细属性:\n")
                properties = row[11].split(',')
                for prop in properties:
                    if ':' in prop:
                        name, value = prop.split(':', 1)
                        self.props_text.insert(tk.END, f"  {name}: {value}\n")
                        
    def update_status(self, message):
        """更新状态栏"""
        self.root.after(0, lambda: self.status_bar.config(text=message))
        
    def reindex_files(self):
        """重新索引文件"""
        if hasattr(self, 'index_directory'):
            self.start_indexing()
        else:
            messagebox.showwarning("警告", "请先选择索引目录")
            
    def export_results(self):
        """导出搜索结果"""
        if not self.filtered_data:
            messagebox.showinfo("提示", "没有搜索结果可导出")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("文件名,路径,大小,类型,修改时间,创建时间,属性\n")
                    for file_info in self.filtered_data:
                        size_str = self.format_size(file_info['size'])
                        modified_str = file_info['modified'].strftime('%Y-%m-%d %H:%M')
                        created_str = file_info['created'].strftime('%Y-%m-%d %H:%M')
                        
                        # 属性字符串
                        props_str = ""
                        if 'properties' in file_info:
                            props = []
                            for k, v in file_info['properties'].items():
                                props.append(f"{k}={v}")
                            props_str = "; ".join(props)
                        
                        f.write(f"{file_info['name']},{file_info['path']},{size_str},"
                               f"{file_info['type']},{modified_str},{created_str},{props_str}\n")
                               
                messagebox.showinfo("成功", f"结果已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
                
    def show_database_manager(self):
        """显示数据库管理器"""
        db_window = tk.Toplevel(self.root)
        db_window.title("数据库管理")
        db_window.geometry("600x400")
        db_window.transient(self.root)
        db_window.grab_set()
        
        # 数据库信息
        info_frame = ttk.LabelFrame(db_window, text="数据库信息")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        count = self.database.get_file_count()
        ttk.Label(info_frame, text=f"总文件数: {count}").pack(anchor=tk.W, padx=10, pady=5)
        
        # 操作按钮
        btn_frame = ttk.Frame(db_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="清空数据库", 
                  command=lambda: self.clear_database(db_window)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="重新索引", 
                  command=lambda: self.reindex_from_manager(db_window)).pack(side=tk.LEFT)
        
    def clear_database(self, window):
        """清空数据库"""
        if messagebox.askyesno("确认", "确定要清空数据库吗？这将删除所有索引数据。"):
            self.database.clear_database()
            self.update_db_info(0)
            self.update_status("数据库已清空")
            window.destroy()
            
    def reindex_from_manager(self, window):
        """从管理器重新索引"""
        window.destroy()
        self.reindex_files()
        
    def show_properties_viewer(self):
        """显示属性查看器"""
        props_window = tk.Toplevel(self.root)
        props_window.title("属性查看器")
        props_window.geometry("800x600")
        props_window.transient(self.root)
        props_window.grab_set()
        
        # 属性列表
        columns = ('property', 'value', 'count')
        tree = ttk.Treeview(props_window, columns=columns, show='headings', height=20)
        
        tree.heading('property', text='属性名')
        tree.heading('value', text='属性值')
        tree.heading('count', text='文件数量')
        
        tree.column('property', width=200)
        tree.column('value', width=400)
        tree.column('count', width=100)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 加载属性统计
        self.load_property_statistics(tree)
        
    def load_property_statistics(self, tree):
        """加载属性统计"""
        conn = sqlite3.connect(self.database.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT property_name, property_value, COUNT(*) as count
            FROM properties
            GROUP BY property_name, property_value
            ORDER BY property_name, count DESC
        ''')
        
        for row in cursor.fetchall():
            tree.insert('', 'end', values=row)
            
        conn.close()
        
    def show_settings(self):
        """显示设置对话框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置内容
        ttk.Label(settings_window, text="索引目录:").pack(anchor=tk.W, padx=10, pady=5)
        
        dir_frame = ttk.Frame(settings_window)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.settings_dir_var = tk.StringVar(value=getattr(self, 'index_directory', ''))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.settings_dir_var)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(dir_frame, text="浏览", 
                  command=lambda: self.settings_dir_var.set(filedialog.askdirectory())).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 数据目录设置
        ttk.Label(settings_window, text="数据目录:").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(settings_window, text=str(self.data_dir), foreground='gray').pack(anchor=tk.W, padx=10)
        
        # 保存按钮
        ttk.Button(settings_window, text="保存", 
                  command=lambda: self.save_settings_from_dialog(settings_window)).pack(pady=20)
        
    def save_settings_from_dialog(self, dialog):
        """从设置对话框保存设置"""
        self.index_directory = self.settings_dir_var.get()
        self.save_settings()
        dialog.destroy()
        messagebox.showinfo("成功", "设置已保存")
        
    def show_about(self):
        """显示关于对话框"""
        about_text = """
文件搜索工具 - Everything (增强版)

功能特点:
• 快速文件索引和搜索
• 轻量级SQLite数据库存储
• 详细的文件属性系统
• 支持多种文件类型筛选
• 实时搜索和排序
• 文件大小和日期筛选
• 导出搜索结果
• 属性查看和管理

版本: 2.0 (增强版)
        """
        messagebox.showinfo("关于", about_text)
        
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists('everything_settings.json'):
                with open('everything_settings.json', 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.index_directory = settings.get('index_directory', '')
        except:
            pass
            
    def save_settings(self):
        """保存设置"""
        try:
            settings = {
                'index_directory': getattr(self, 'index_directory', '')
            }
            with open('everything_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except:
            pass

def main():
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
