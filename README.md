# WinTools

Windows工具集合

Copyright (c) 2024 wangzhenjjcn@gmail.com  
Author: wangzhenjjcn  
GitHub: https://github.com/wangzhenjjcn/WinTools

## 工具列表

### IP端口扫描器
- 位置：`IP/` 文件夹
- 功能：基于Qt6的图形化局域网IP和端口扫描工具
- 启动方式：
  - 双击 `start_ip_scanner.bat` 或
  - 进入 `IP/` 文件夹运行 `python ip_scanner.py`

详细使用说明请查看 `IP/README_scanner.md`

### 编译为EXE文件
项目提供了多种编译方式：

#### 方式一：从根目录编译（推荐）
- 双击 `build_from_root.bat`
- 选择编译方式（完整/快速/高级）
- 自动进入IP文件夹并执行编译

#### 方式二：直接使用IP文件夹中的脚本
1. **IP/build_exe.bat** - 完整编译脚本（推荐）
   - 自动检查环境
   - 自动安装依赖
   - 详细错误提示
   - 编译后可选测试运行

2. **IP/build_quick.bat** - 快速编译脚本
   - 简化版本
   - 快速编译
   - 适合有经验的用户

3. **IP/build_advanced.bat** - 高级编译脚本
   - 优化编译选项
   - 排除不必要的模块
   - 生成更小的文件
   - 自动清理旧文件

编译后的exe文件将生成在 `IP/dist/` 目录中，文件名为 `IPScanner.exe`。

### 编码优化
所有编译脚本已针对简体中文Windows系统进行优化：
- 使用UTF-8编码（chcp 65001）
- 避免中文文件名，使用英文文件名
- 添加窗口标题
- 确保中文显示正常